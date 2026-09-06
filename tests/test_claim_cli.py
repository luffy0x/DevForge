import sys

from devforge.claim_cli import main
from devforge.models import CandidateTask, Issue, TaskStatus
from devforge.queue import TaskStore


def test_claim_command_prints_plan(tmp_path, capsys) -> None:
    database = tmp_path / "tasks.db"
    store = TaskStore(database)
    store.upsert(CandidateTask(Issue("acme/app", 1, "Fix parser"), 0.8, status=TaskStatus.QUEUED))
    sys.argv = ["devforge", "--task", "acme/app#1", "--database", str(database)]
    assert main() == 0
    assert "claimed=acme/app#1" in capsys.readouterr().out
