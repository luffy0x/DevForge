from collections.abc import Iterable

from .models import Issue


class Finder:
    """Select open, actionable issues from an allow-listed repository set."""

    def __init__(self, allowed_repositories: Iterable[str]) -> None:
        self.allowed_repositories = frozenset(allowed_repositories)

    def find(self, issues: Iterable[Issue]) -> list[Issue]:
        return [
            issue
            for issue in issues
            if issue.state == "open"
            and issue.repository in self.allowed_repositories
            and issue.title.strip()
            and "wontfix" not in {label.lower() for label in issue.labels}
        ]
