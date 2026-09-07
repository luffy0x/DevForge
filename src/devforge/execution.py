from dataclasses import dataclass
from pathlib import Path

from .contributor import ContributionPlan
from .workspace import CommandResult, WorkspaceManager


@dataclass(frozen=True)
class ExecutionArtifact:
    plan: ContributionPlan
    workspace: Path
    files: dict[str, str]
    test_result: CommandResult


class ContributorExecution:
    """Apply an externally generated change set and validate it in isolation."""

    def __init__(self, workspace_manager: WorkspaceManager) -> None:
        self.workspace_manager = workspace_manager

    def run(
        self,
        plan: ContributionPlan,
        repository_url: str,
        branch: str,
        files: dict[str, str],
        test_command: tuple[str, ...],
    ) -> ExecutionArtifact:
        workspace = self.workspace_manager.prepare(repository_url, branch)
        self.workspace_manager.apply_files(workspace, files)
        test_result = self.workspace_manager.run(workspace, test_command)
        return ExecutionArtifact(plan, workspace, files, test_result)
