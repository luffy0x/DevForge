from dataclasses import dataclass
from collections.abc import Iterable

from .finder import Finder
from .models import CandidateTask, Issue, TaskStatus
from .queue import TaskStore
from .scoring import ScoreAgent


@dataclass(frozen=True)
class PipelineResult:
    discovered: int
    queued: int
    rejected: int
    tasks: tuple[CandidateTask, ...]


class MvpPipeline:
    def __init__(self, finder: Finder, scorer: ScoreAgent, store: TaskStore, threshold: float = 0.5) -> None:
        if not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1")
        self.finder = finder
        self.scorer = scorer
        self.store = store
        self.threshold = threshold

    def run(self, issues: Iterable[Issue]) -> PipelineResult:
        candidates = self.finder.find(issues)
        tasks: list[CandidateTask] = []
        queued = rejected = 0
        for issue in candidates:
            task = self.scorer.score(issue)
            if task.score >= self.threshold:
                task = CandidateTask(task.issue, task.score, task.reasons, TaskStatus.QUEUED, task.metadata)
                self.store.upsert(task)
                queued += 1
            else:
                rejected += 1
            tasks.append(task)
        return PipelineResult(len(candidates), queued, rejected, tuple(tasks))
