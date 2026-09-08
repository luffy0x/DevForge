import sqlite3

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


def test_list_can_filter_by_status(tmp_path) -> None:
    store = TaskStore(tmp_path / "tasks.db")
    queued = make_task()
    failed = CandidateTask(Issue("acme/app", 8, "Retry build"), 0.9, status=TaskStatus.FAILED)
    store.upsert(queued)
    store.upsert(failed)
    assert [task.task_key for task in store.list()] == ["acme/app#8", "acme/app#7"]
    assert [task.task_key for task in store.list(TaskStatus.FAILED)] == ["acme/app#8"]


def test_task_store_records_publication_result(tmp_path) -> None:
    store = TaskStore(tmp_path / "tasks.db")
    store.upsert(make_task())
    assert store.record_publication("acme/app#7", 42)
    assert store.get("acme/app#7").metadata == {
        "pull_request_number": 42,
        "pull_request_url": "https://github.com/acme/app/pull/42",
    }


def test_task_store_records_failure_and_clears_it_on_retry(tmp_path) -> None:
    store = TaskStore(tmp_path / "tasks.db")
    store.upsert(make_task())
    assert store.transition("acme/app#7", TaskStatus.SCORED, TaskStatus.WORKING)
    assert store.fail("acme/app#7", "RuntimeError: test command failed")
    assert store.get("acme/app#7").metadata["last_error"] == "RuntimeError: test command failed"
    assert store.retry("acme/app#7")
    retried = store.get("acme/app#7")
    assert retried.status is TaskStatus.QUEUED
    assert "last_error" not in retried.metadata


def test_task_store_migrates_existing_database(tmp_path) -> None:
    database = tmp_path / "tasks.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            """CREATE TABLE tasks (
                task_key TEXT PRIMARY KEY,
                repository TEXT NOT NULL,
                issue_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                labels TEXT NOT NULL,
                url TEXT NOT NULL,
                score REAL NOT NULL,
                reasons TEXT NOT NULL,
                status TEXT NOT NULL,
                UNIQUE(repository, issue_number)
            )"""
        )

    store = TaskStore(database)
    store.upsert(make_task())
    assert store.record_publication("acme/app#7", 42)
    assert store.get("acme/app#7").metadata["pull_request_number"] == 42
