from dataclasses import dataclass

from .contributor import ContributionPlan
from .github_writer import GitHubRepositoryWriter


@dataclass(frozen=True)
class PublishResult:
    repository: str
    branch: str
    pull_request_number: int


class ContributionPublisher:
    def __init__(self, writer: GitHubRepositoryWriter, base_branch: str = "main") -> None:
        self.writer = writer
        self.base_branch = base_branch

    def publish(self, plan: ContributionPlan, base_sha: str, branch: str, files: dict[str, str], title: str | None = None, body: str = "") -> PublishResult:
        self.writer.create_branch(plan.repository, branch, base_sha)
        for path, content in files.items():
            self.writer.commit_file(plan.repository, branch, path, content, f"feat: implement issue #{plan.issue_number}")
        pr_number = self.writer.create_draft_pr(plan.repository, branch, self.base_branch, title or plan.objective, body)
        return PublishResult(plan.repository, branch, pr_number)
