import base64
import json
from collections.abc import Callable
from urllib.request import Request, urlopen


class GitHubWriteError(RuntimeError):
    pass


class GitHubRepositoryWriter:
    """Minimal GitHub write adapter; callers decide when publishing is allowed."""

    def __init__(self, token: str, api_base: str = "https://api.github.com", request: Callable[[Request], bytes] | None = None) -> None:
        if not token:
            raise ValueError("a GitHub token is required for write operations")
        self.token = token
        self.api_base = api_base.rstrip("/")
        self._request = request or self._default_request

    @staticmethod
    def _default_request(request: Request) -> bytes:
        try:
            with urlopen(request, timeout=20) as response:
                return response.read()
        except Exception as exc:
            raise GitHubWriteError(str(exc)) from exc

    def _call(self, method: str, path: str, payload: dict) -> dict:
        request = Request(f"{self.api_base}{path}", method=method, data=json.dumps(payload).encode())
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("Content-Type", "application/json")
        request.add_header("Authorization", f"Bearer {self.token}")
        try:
            data = self._request(request)
            result = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GitHubWriteError("GitHub returned invalid JSON") from exc
        if not isinstance(result, dict):
            raise GitHubWriteError("GitHub response must be an object")
        return result

    def create_branch(self, repository: str, branch: str, base_sha: str) -> str:
        result = self._call("POST", f"/repos/{repository}/git/refs", {"ref": f"refs/heads/{branch}", "sha": base_sha})
        return result.get("ref", f"refs/heads/{branch}")

    def commit_file(self, repository: str, branch: str, path: str, content: str, message: str) -> str:
        result = self._call("PUT", f"/repos/{repository}/contents/{path}", {"message": message, "content": base64.b64encode(content.encode()).decode(), "branch": branch})
        return result.get("commit", {}).get("sha", "")

    def create_draft_pr(self, repository: str, branch: str, base: str, title: str, body: str = "") -> int:
        result = self._call("POST", f"/repos/{repository}/pulls", {"title": title, "head": branch, "base": base, "body": body, "draft": True})
        return int(result["number"])
