import argparse
import json
from pathlib import Path

from .finder import Finder
from .models import Issue
from .pipeline import MvpPipeline
from .queue import TaskStore
from .scoring import ScoreAgent


def _issues_from_json(path: Path) -> list[Issue]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("issues file must contain a JSON array")
    return [
        Issue(
            repository=item["repository"],
            number=int(item["number"]),
            title=item["title"],
            body=item.get("body", ""),
            labels=tuple(item.get("labels", [])),
            url=item.get("url", ""),
            state=item.get("state", "open"),
        )
        for item in raw
    ]


def main() -> int:
    parser = argparse.ArgumentParser(prog="devforge")
    parser.add_argument("--issues-file", type=Path, required=True)
    parser.add_argument("--repository", action="append", required=True)
    parser.add_argument("--database", type=Path, default=Path("devforge.db"))
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    result = MvpPipeline(
        Finder(args.repository), ScoreAgent(), TaskStore(args.database), args.threshold
    ).run(_issues_from_json(args.issues_file))
    print(f"discovered={result.discovered} queued={result.queued} rejected={result.rejected}")
    for task in result.tasks:
        print(f"{task.task_key} score={task.score:.2f} status={task.status.value}")
    return 0
