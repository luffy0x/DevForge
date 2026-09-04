from dataclasses import dataclass

from .models import CandidateTask, TaskStatus
from .queue import TaskStore


@dataclass(frozen=True)
class ContributionPlan:
    task_key: str
    repository: str
    issue_number: int
    objective: str
    constraints: tuple[str, ...]


class ContributorAgent:
    """Claim queued work and produce an auditable implementation plan.

    Code edits and pull-request creation are intentionally separate adapters;
    claiming a task must never mutate a repository by itself.
    """

    def __init__(self, store: TaskStore) -> None:
        self.store = store

    def claim(self, task_key: str) -> ContributionPlan | None:
        task = self.store.get(task_key)
        if task is None or task.status is not TaskStatus.QUEUED:
            return None
        if not self.store.transition(task_key, TaskStatus.QUEUED, TaskStatus.WORKING):
            return None
        return self._plan(task)

    @staticmethod
    def _plan(task: CandidateTask) -> ContributionPlan:
        issue = task.issue
        return ContributionPlan(
            task_key=task.task_key,
            repository=issue.repository,
            issue_number=issue.number,
            objective=issue.title.strip(),
            constraints=(
                "work in an isolated branch",
                "run repository tests before opening a pull request",
                "do not merge or deploy automatically",
            ),
        )
