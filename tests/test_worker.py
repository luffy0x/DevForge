import pytest

from devforge.models import CandidateTask, Issue, TaskStatus
from devforge.queue import TaskStore
from devforge.worker import ContributorWorker


def test_worker_executes_once_and_fulfills(tmp_path) -> None:
    store = TaskStore(tmp_path / "db")
    task = CandidateTask(Issue("acme/app", 9, "Add metrics", "context"), 0.8, status=TaskStatus.QUEUED)
    store.upsert(task)
    seen = []
    worker = ContributorWorker(store, lambda plan: seen.append(plan.task_key))
    assert worker.run_once(task.task_key)
    assert seen == [task.task_key]
    assert store.get(task.task_key).status is TaskStatus.FULFILLED
    assert not worker.run_once(task.task_key)


def test_worker_keeps_working_task_when_executor_fails(tmp_path) -> None:
    store = TaskStore(tmp_path / "db")
    task = CandidateTask(Issue("acme/app", 10, "Fix bug"), 0.8, status=TaskStatus.QUEUED)
    store.upsert(task)
    worker = ContributorWorker(store, lambda plan: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(RuntimeError, match="boom"):
        worker.run_once(task.task_key)
    assert store.get(task.task_key).status is TaskStatus.WORKING
