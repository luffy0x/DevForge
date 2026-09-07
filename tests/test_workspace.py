from pathlib import Path

import pytest

from devforge.workspace import WorkspaceError, WorkspaceManager


def test_apply_files_rejects_path_escape(tmp_path: Path) -> None:
    manager = WorkspaceManager(tmp_path / "root")
    workspace = tmp_path / "root" / "repo"
    workspace.mkdir(parents=True)
    with pytest.raises(WorkspaceError, match="escapes workspace"):
        manager.apply_files(workspace, {"../escape.txt": "bad"})


def test_run_uses_argument_vector(tmp_path: Path) -> None:
    manager = WorkspaceManager(tmp_path / "root")
    result = manager.run(tmp_path, ("python", "-c", "print('ok')"))
    assert result.stdout.strip() == "ok"
