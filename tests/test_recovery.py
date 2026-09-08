import pytest

from devforge.agent_loop import ContributorLoop
from devforge.github_writer import GitHubRepositoryWriter
from devforge.models import CandidateTask, Issue, TaskStatus
from devforge.queue import TaskStore


class FakeWorkspace:
    def prepare(self, repository_url, branch, base_branch):
        return "/tmp/devforge-recovery"

    def apply_files(self, workspace, files):
        pass

    def run(self, workspace, command):
        return None


class FailingModel:
    def propose(self, plan, workspace):
        raise RuntimeError("model unavailable")


class UnusedWriter(GitHubRepositoryWriter):
    def __init__(self):
        pass


def test_failed_run_is_retryable(tmp_path) -> None:
    store = TaskStore(tmp_path / "db")
    task = CandidateTask(Issue("acme/app", 1, "Fix bug"), 0.8, status=TaskStatus.QUEUED)
    store.upsert(task)
    loop = ContributorLoop(store, FakeWorkspace(), FailingModel(), UnusedWriter())

    with pytest.raises(RuntimeError, match="model unavailable"):
        loop.run_once(task.task_key, "https://github.com/acme/app.git", "base", "devforge/1")

    assert store.get(task.task_key).status is TaskStatus.FAILED
    assert store.retry(task.task_key)
    assert store.get(task.task_key).status is TaskStatus.QUEUED
    assert not store.retry(task.task_key)
