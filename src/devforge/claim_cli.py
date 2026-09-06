import argparse
from pathlib import Path

from .contributor import ContributorAgent
from .queue import TaskStore


def main() -> int:
    parser = argparse.ArgumentParser(prog="devforge claim")
    parser.add_argument("--task", required=True, help="Task key, for example owner/repo#123")
    parser.add_argument("--database", type=Path, default=Path("devforge.db"))
    args = parser.parse_args()

    plan = ContributorAgent(TaskStore(args.database)).claim(args.task)
    if plan is None:
        print(f"unable to claim task: {args.task}")
        return 1
    print(f"claimed={plan.task_key}")
    print(f"repository={plan.repository}")
    print(f"issue={plan.issue_number}")
    print(f"objective={plan.objective}")
    for constraint in plan.constraints:
        print(f"constraint={constraint}")
    return 0
