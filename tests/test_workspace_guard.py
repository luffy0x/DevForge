from pathlib import Path

import pytest

from devforge.workspace import CommandResult, WorkspaceError, WorkspaceManager


def test_prepare_rejects_unsafe_branch(tmp_path: Path) -> None:
    manager = WorkspaceManager(tmp_path / "root")
    with pytest.raises(WorkspaceError, match="safe git branch"):
        manager.prepare("https://github.com/acme/app.git", "../main")


def test_prepare_rejects_dirty_existing_workspace(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "root"
    workspace = root / "app"
    (workspace / ".git").mkdir(parents=True)
    manager = WorkspaceManager(root)

    def fake_run(command, cwd, timeout=120):
        if command == ("git", "status", "--porcelain"):
            return CommandResult(command, 0, " M src/app.py\n", "")
        return CommandResult(command, 0, "", "")

    monkeypatch.setattr(manager, "_run", fake_run)
    with pytest.raises(WorkspaceError, match="uncommitted changes"):
        manager.prepare("https://github.com/acme/app.git", "devforge/1")
