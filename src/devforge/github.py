import json
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Issue


class GitHubApiError(RuntimeError):
    pass


class GitHubIssueSource:
    """Read open issues from GitHub without coupling the core pipeline to HTTP."""

    def __init__(
        self,
        token: str | None = None,
        api_base: str = "https://api.github.com",
        request: Callable[[Request], bytes] | None = None,
    ) -> None:
        self.token = token
        self.api_base = api_base.rstrip("/")
        self._request = request or self._default_request

    @staticmethod
    def _default_request(request: Request) -> bytes:
        try:
            with urlopen(request, timeout=20) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            raise GitHubApiError(str(exc)) from exc

    def list_open_issues(self, repository: str, per_page: int = 100) -> list[Issue]:
        if "/" not in repository or repository.startswith("/"):
            raise ValueError("repository must use owner/name format")
        query = urlencode({"state": "open", "per_page": min(max(per_page, 1), 100)})
        request = Request(f"{self.api_base}/repos/{repository}/issues?{query}")
        request.add_header("Accept", "application/vnd.github+json")
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")
        try:
            payload = json.loads(self._request(request).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GitHubApiError("GitHub returned invalid JSON") from exc
        if not isinstance(payload, list):
            raise GitHubApiError("GitHub issues response must be a list")
        return [self._to_issue(repository, item) for item in payload if "pull_request" not in item]

    @staticmethod
    def _to_issue(repository: str, item: dict) -> Issue:
        labels = tuple(label["name"] for label in item.get("labels", []) if label.get("name"))
        return Issue(
            repository=repository,
            number=int(item["number"]),
            title=str(item.get("title", "")),
            body=str(item.get("body") or ""),
            labels=labels,
            url=str(item.get("html_url", "")),
            state=str(item.get("state", "open")),
        )
