import argparse
from pathlib import Path

from .models import TaskStatus
from .queue import TaskStore


def main() -> int:
    parser = argparse.ArgumentParser(prog="devforge tasks")
    parser.add_argument("--database", type=Path, default=Path("devforge.db"))
    parser.add_argument("--status", choices=[status.value for status in TaskStatus])
    args = parser.parse_args()

    status = TaskStatus(args.status) if args.status else None
    tasks = TaskStore(args.database).list(status)
    for task in tasks:
        pull_request_url = task.metadata.get("pull_request_url")
        last_error = task.metadata.get("last_error")
        publication = f" pull_request={pull_request_url}" if pull_request_url else ""
        failure = f" error={last_error!r}" if last_error else ""
        print(
            f"{task.task_key} score={task.score:.2f} status={task.status.value} "
            f"title={task.issue.title}{publication}{failure}"
        )
    print(f"count={len(tasks)}")
    return 0
