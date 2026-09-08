from pathlib import Path

from devforge.agent_loop import ContributorLoop
from devforge.github_writer import GitHubRepositoryWriter
from devforge.model import ModelProposal
from devforge.models import CandidateTask, Issue, TaskStatus
from devforge.publisher import PublishResult
from devforge.queue import TaskStore
from devforge.workspace import CommandResult


class FakeWorkspace:
    def prepare(self, repository_url, branch):
        return Path("/tmp/devforge-loop")

    def apply_files(self, workspace, files):
        pass

    def run(self, workspace, command):
        return CommandResult(command, 0, "ok", "")


class FakeModel:
    def propose(self, plan, workspace):
        return ModelProposal({"fix.py": "pass"}, ("python", "-c", "print('ok')"), "implemented")


class FakeWriter(GitHubRepositoryWriter):
    def __init__(self):
        pass

    def create_branch(self, repository, branch, base_sha):
        pass

    def commit_file(self, repository, branch, path, content, message):
        return "sha"

    def create_draft_pr(self, repository, branch, base, title, body=""):
        return 99


def test_contributor_loop_publishes_and_fulfills(tmp_path) -> None:
    store = TaskStore(tmp_path / "db")
    task = CandidateTask(Issue("acme/app", 1, "Fix bug"), 0.8, status=TaskStatus.QUEUED)
    store.upsert(task)
    result = ContributorLoop(store, FakeWorkspace(), FakeModel(), FakeWriter()).run_once(task.task_key, "https://github.com/acme/app.git", "base", "devforge/1")
    assert result == PublishResult("acme/app", "devforge/1", 99)
    completed = store.get(task.task_key)
    assert completed.status is TaskStatus.FULFILLED
    assert completed.metadata["pull_request_url"] == "https://github.com/acme/app/pull/99"
