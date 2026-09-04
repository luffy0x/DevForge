import argparse
import json
import os
from pathlib import Path

from .finder import Finder
from .github import GitHubIssueSource
from .models import Issue
from .pipeline import MvpPipeline
from .queue import TaskStore
from .scoring import ScoreAgent


def _issues_from_json(path: Path) -> list[Issue]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("issues file must contain a JSON array")
    return [Issue(item["repository"], int(item["number"]), item["title"], item.get("body", ""), tuple(item.get("labels", [])), item.get("url", ""), item.get("state", "open")) for item in raw]


def main() -> int:
    parser = argparse.ArgumentParser(prog="devforge")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--issues-file", type=Path)
    source.add_argument("--github-repository", action="append", dest="github_repositories")
    parser.add_argument("--repository", action="append", default=[])
    parser.add_argument("--database", type=Path, default=Path("devforge.db"))
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    if args.issues_file:
        issues = _issues_from_json(args.issues_file)
        repositories = args.repository or sorted({issue.repository for issue in issues})
    else:
        repositories = args.github_repositories
        client = GitHubIssueSource(os.getenv("GITHUB_TOKEN"))
        issues = [issue for repository in repositories for issue in client.list_open_issues(repository)]

    result = MvpPipeline(Finder(repositories), ScoreAgent(), TaskStore(args.database), args.threshold).run(issues)
    print(f"discovered={result.discovered} queued={result.queued} rejected={result.rejected}")
    for task in result.tasks:
        print(f"{task.task_key} score={task.score:.2f} status={task.status.value}")
    return 0
