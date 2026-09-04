from devforge.models import CandidateTask, Issue, TaskStatus
from devforge.queue import TaskStore


def make_task() -> CandidateTask:
    return CandidateTask(
        issue=Issue("acme/app", 7, "Fix timeout", "repro", ("bug",), "https://github.com/acme/app/issues/7"),
        score=0.7,
        reasons=("actionable change signal",),
    )


def test_task_store_is_idempotent(tmp_path) -> None:
    store = TaskStore(tmp_path / "tasks.db")
    task = make_task()
    store.upsert(task)
    store.upsert(task)
    loaded = store.get("acme/app#7")
    assert loaded == task


def test_transition_is_compare_and_set(tmp_path) -> None:
    store = TaskStore(tmp_path / "tasks.db")
    store.upsert(make_task())
    assert store.transition("acme/app#7", TaskStatus.SCORED, TaskStatus.QUEUED)
    assert not store.transition("acme/app#7", TaskStatus.SCORED, TaskStatus.WORKING)
    assert store.get("acme/app#7").status is TaskStatus.QUEUED
