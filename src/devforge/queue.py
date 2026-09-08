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
                    pull_request_number INTEGER,
                    pull_request_url TEXT,
                    UNIQUE(repository, issue_number)
                )"""
            )
            self._add_column_if_missing(connection, "pull_request_number", "INTEGER")
            self._add_column_if_missing(connection, "pull_request_url", "TEXT")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _add_column_if_missing(connection: sqlite3.Connection, name: str, definition: str) -> None:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(tasks)")}
        if name not in columns:
            connection.execute(f"ALTER TABLE tasks ADD COLUMN {name} {definition}")

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

    def list(self, status: TaskStatus | None = None) -> list[CandidateTask]:
        """Return persisted tasks, optionally filtered by lifecycle status."""
        query = "SELECT * FROM tasks"
        parameters: tuple[str, ...] = ()
        if status is not None:
            query += " WHERE status = ?"
            parameters = (status.value,)
        query += " ORDER BY score DESC, repository, issue_number"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._to_task(row) for row in rows]

    def transition(self, task_key: str, expected: TaskStatus, target: TaskStatus) -> bool:
        with self._connect() as connection:
            result = connection.execute(
                "UPDATE tasks SET status = ? WHERE task_key = ? AND status = ?",
                (target.value, task_key, expected.value),
            )
        return result.rowcount == 1

    def record_publication(self, task_key: str, pull_request_number: int) -> bool:
        """Persist the draft PR created for a task without changing its lifecycle state."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT repository FROM tasks WHERE task_key = ?", (task_key,)
            ).fetchone()
            if row is None:
                return False
            result = connection.execute(
                """UPDATE tasks
                   SET pull_request_number = ?, pull_request_url = ?
                   WHERE task_key = ?""",
                (
                    pull_request_number,
                    f"https://github.com/{row['repository']}/pull/{pull_request_number}",
                    task_key,
                ),
            )
        return result.rowcount == 1

    def retry(self, task_key: str) -> bool:
        """Move one failed task back to the queue without duplicating it."""
        return self.transition(task_key, TaskStatus.FAILED, TaskStatus.QUEUED)

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
        metadata = {}
        if row["pull_request_number"] is not None:
            metadata["pull_request_number"] = row["pull_request_number"]
        if row["pull_request_url"]:
            metadata["pull_request_url"] = row["pull_request_url"]
        return CandidateTask(
            issue=issue,
            score=row["score"],
            reasons=tuple(filter(None, row["reasons"].split("\\n"))),
            status=TaskStatus(row["status"]),
            metadata=metadata,
        )
