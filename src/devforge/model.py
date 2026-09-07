import json
from dataclasses import dataclass
from pathlib import Path
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
            files = result["files"]
            test_command = tuple(result["test_command"])
            summary = str(result.get("summary", ""))
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ModelAdapterError("model returned an invalid contributor proposal") from exc
        if not isinstance(files, dict) or not files or not all(isinstance(k, str) and isinstance(v, str) for k, v in files.items()):
            raise ModelAdapterError("proposal files must be a non-empty string map")
        if not test_command or not all(isinstance(part, str) and part for part in test_command):
            raise ModelAdapterError("proposal test_command must be a non-empty string list")
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
                "Prefer the smallest testable change.",
            ],
        }, ensure_ascii=False)
