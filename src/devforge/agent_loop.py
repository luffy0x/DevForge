from .contributor import ContributorAgent
from .github_writer import GitHubRepositoryWriter
from .model import ModelAdapter
from .models import TaskStatus
from .publisher import ContributionPublisher, PublishResult
from .queue import TaskStore
from .workspace import WorkspaceManager


class ContributorLoop:
    """Claim, propose, test, publish, and complete one queued task."""

    def __init__(self, store: TaskStore, workspace: WorkspaceManager, model: ModelAdapter, writer: GitHubRepositoryWriter) -> None:
        self.store = store
        self.contributor = ContributorAgent(store)
        self.workspace = workspace
        self.model = model
        self.publisher = ContributionPublisher(writer)

    def run_once(self, task_key: str, repository_url: str, base_sha: str, branch: str) -> PublishResult | None:
        plan = self.contributor.claim(task_key)
        if plan is None:
            return None
        workspace = self.workspace.prepare(repository_url, branch)
        proposal = self.model.propose(plan, workspace)
        self.workspace.apply_files(workspace, proposal.files)
        self.workspace.run(workspace, proposal.test_command)
        result = self.publisher.publish(plan, base_sha, branch, proposal.files, body=proposal.summary)
        self.store.transition(task_key, TaskStatus.WORKING, TaskStatus.FULFILLED)
        return result
