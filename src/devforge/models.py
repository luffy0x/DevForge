from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class TaskStatus(StrEnum):
    PENDING = "pending"
    SCORED = "scored"
    QUEUED = "queued"
    WORKING = "working"
    FULFILLED = "fulfilled"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Issue:
    repository: str
    number: int
    title: str
    body: str = ""
    labels: tuple[str, ...] = ()
    url: str = ""
    state: str = "open"


@dataclass(frozen=True)
class CandidateTask:
    issue: Issue
    score: float
    reasons: tuple[str, ...] = ()
    status: TaskStatus = TaskStatus.SCORED
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def task_key(self) -> str:
        return f"{self.issue.repository}#{self.issue.number}"
