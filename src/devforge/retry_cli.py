import argparse
from pathlib import Path

from .queue import TaskStore


def main() -> int:
    parser = argparse.ArgumentParser(prog="devforge retry")
    parser.add_argument("--task", required=True)
    parser.add_argument("--database", type=Path, default=Path("devforge.db"))
    args = parser.parse_args()

    if not TaskStore(args.database).retry(args.task):
        print(f"task is not failed or does not exist: {args.task}")
        return 1
    print(f"queued={args.task}")
    return 0
