from collections.abc import Iterable

from .contributor import ContributionPlan, ContributorAgent
from .finder import Finder
from .github import GitHubIssueSource
from .models import CandidateTask
from .pipeline import MvpPipeline, PipelineResult
from .queue import TaskStore
from .scoring import ScoreAgent


class DevForgeWorkflow:
    """Application service coordinating discovery, scoring, queueing, and claiming."""

    def __init__(self, repositories: Iterable[str], store: TaskStore, source: GitHubIssueSource | None = None, threshold: float = 0.5) -> None:
        repositories = tuple(repositories)
        self.source = source or GitHubIssueSource()
        self.pipeline = MvpPipeline(Finder(repositories), ScoreAgent(), store, threshold)
        self.contributor = ContributorAgent(store)
        self.repositories = repositories

    def scan(self) -> PipelineResult:
        issues = [issue for repository in self.repositories for issue in self.source.list_open_issues(repository)]
        return self.pipeline.run(issues)

    def claim(self, task_key: str) -> ContributionPlan | None:
        return self.contributor.claim(task_key)
