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
        print(f"{task.task_key} score={task.score:.2f} status={task.status.value} title={task.issue.title}")
    print(f"count={len(tasks)}")
    return 0
