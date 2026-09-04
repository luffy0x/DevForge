import sqlite3
from pathlib import Path

from .models import CandidateTask, Issue, TaskStatus


class TaskStore:
    """Small SQLite-backed store with repository/issue idempotency."""

    def __init__(self, database: str | Path = "devforge.db") -> None:
        self.database = str(database)
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS tasks (
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

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        return connection

    def upsert(self, task: CandidateTask) -> None:
        issue = task.issue
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO tasks
                   (task_key, repository, issue_number, title, body, labels, url,
                    score, reasons, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(task_key) DO UPDATE SET
                     title=excluded.title, body=excluded.body,
                     labels=excluded.labels, url=excluded.url,
                     score=excluded.score, reasons=excluded.reasons""",
                (
                    task.task_key,
                    issue.repository,
                    issue.number,
                    issue.title,
                    issue.body,
                    "\\n".join(issue.labels),
                    issue.url,
                    task.score,
                    "\\n".join(task.reasons),
                    task.status.value,
                ),
            )

    def get(self, task_key: str) -> CandidateTask | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE task_key = ?", (task_key,)).fetchone()
        return self._to_task(row) if row else None

    def transition(self, task_key: str, expected: TaskStatus, target: TaskStatus) -> bool:
        with self._connect() as connection:
            result = connection.execute(
                "UPDATE tasks SET status = ? WHERE task_key = ? AND status = ?",
                (target.value, task_key, expected.value),
            )
        return result.rowcount == 1

    @staticmethod
    def _to_task(row: sqlite3.Row) -> CandidateTask:
        issue = Issue(
            repository=row["repository"],
            number=row["issue_number"],
            title=row["title"],
            body=row["body"],
            labels=tuple(filter(None, row["labels"].split("\\n"))),
            url=row["url"],
        )
        return CandidateTask(
            issue=issue,
            score=row["score"],
            reasons=tuple(filter(None, row["reasons"].split("\\n"))),
            status=TaskStatus(row["status"]),
        )
