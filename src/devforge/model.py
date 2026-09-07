import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .contributor import ContributionPlan


class ModelAdapterError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelProposal:
    files: dict[str, str]
    test_command: tuple[str, ...]
    summary: str


class ModelAdapter(Protocol):
    def propose(self, plan: ContributionPlan, workspace: Path) -> ModelProposal:
        ...


def _validate_files(files: object) -> dict[str, str]:
    if not isinstance(files, dict) or not files:
        raise ModelAdapterError("proposal files must be a non-empty string map")
    if len(files) > 50:
        raise ModelAdapterError("proposal contains too many files")
    validated: dict[str, str] = {}
    for raw_path, content in files.items():
        if not isinstance(raw_path, str) or not isinstance(content, str):
            raise ModelAdapterError("proposal files must be a non-empty string map")
        normalized = raw_path.replace("\\", "/")
        path = PurePosixPath(normalized)
        if ("\x00" in normalized or path.is_absolute() or not normalized or ".." in path.parts or "." in path.parts):
            raise ModelAdapterError(f"proposal path is not repository-relative: {raw_path!r}")
        validated[normalized] = content
    return validated


def _validate_test_command(command: object) -> tuple[str, ...]:
    allowed = {"python", "python3", "pytest", "node", "npm", "pnpm", "yarn", "bun", "go", "cargo", "mvn", "gradle", "make", "dotnet", "ruby", "bundle"}
    if not isinstance(command, (list, tuple)) or not command or len(command) > 20:
        raise ModelAdapterError("proposal test_command must be a non-empty string list")
    if not all(isinstance(part, str) and part and "\x00" not in part for part in command):
        raise ModelAdapterError("proposal test_command must be a non-empty string list")
    if any(token in part for part in command for token in (";", "|", "&", ">", "<", "`", "$(") ):
        raise ModelAdapterError("proposal test_command contains shell syntax")
    executable = Path(command[0]).name
    if executable not in allowed:
        raise ModelAdapterError(f"test executable is not allowed: {command[0]!r}")
    return tuple(command)


class OpenAICompatibleAdapter:
    """Generate a validated file map through an OpenAI-compatible chat endpoint."""

    def __init__(self, api_key: str, model: str, endpoint: str = "https://api.openai.com/v1/chat/completions") -> None:
        if not api_key:
            raise ValueError("api_key is required")
        if not model:
            raise ValueError("model is required")
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint

    def propose(self, plan: ContributionPlan, workspace: Path) -> ModelProposal:
        prompt = self._prompt(plan, workspace)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a cautious software contributor. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        request = Request(self.endpoint, method="POST", data=json.dumps(payload).encode())
        request.add_header("Authorization", f"Bearer {self.api_key}")
        request.add_header("Content-Type", "application/json")
        try:
            with urlopen(request, timeout=120) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ModelAdapterError(str(exc)) from exc
        try:
            content = raw["choices"][0]["message"]["content"]
            result = json.loads(content)
            files = _validate_files(result["files"])
            test_command = _validate_test_command(result["test_command"])
            summary = str(result.get("summary", ""))
        except ModelAdapterError:
            raise
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ModelAdapterError("model returned an invalid contributor proposal") from exc
        return ModelProposal(files=files, test_command=test_command, summary=summary)

    @staticmethod
    def _prompt(plan: ContributionPlan, workspace: Path) -> str:
        paths = sorted(str(path.relative_to(workspace)) for path in workspace.rglob("*") if path.is_file())[:200]
        return json.dumps({
            "task": {
                "repository": plan.repository,
                "issue_number": plan.issue_number,
                "objective": plan.objective,
                "constraints": plan.constraints,
            },
            "workspace": str(workspace),
            "file_paths": paths,
            "output_schema": {
                "files": "map of repository-relative paths to complete UTF-8 file contents",
                "test_command": "argv array for a focused repository test command",
                "summary": "short implementation summary",
            },
            "rules": [
                "Inspect relevant files before proposing changes.",
                "Do not modify secrets, CI credentials, or files outside the repository.",
                "Return an argv-only test command using a standard test executable; never use shell syntax.",
                "Prefer the smallest testable change.",
            ],
        }, ensure_ascii=False)
