import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


class WorkspaceError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class WorkspaceManager:
    """Prepare an isolated git workspace and run argv-only commands."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def prepare(self, repository_url: str, branch: str, base_branch: str = "main") -> Path:
        parsed = urlparse(repository_url)
        if parsed.scheme not in {"https", "ssh"} or not parsed.netloc:
            raise WorkspaceError("repository_url must be an https or ssh URL")
        self._validate_branch(branch)
        self._validate_branch(base_branch)
        repository_name = Path(parsed.path.rstrip("/")).stem
        if not repository_name:
            raise WorkspaceError("repository_url must contain a repository name")
        workspace = self.root / repository_name
        if not (workspace / ".git").exists():
            self._run(("git", "clone", "--depth", "1", repository_url, str(workspace)), cwd=self.root)
        status = self._run(("git", "status", "--porcelain"), cwd=workspace)
        if status.stdout.strip():
            raise WorkspaceError("workspace has uncommitted changes; refusing to reuse it")
        self._run(("git", "fetch", "origin", base_branch), cwd=workspace)
        self._run(("git", "checkout", "-B", branch, f"origin/{base_branch}"), cwd=workspace)
        return workspace

    @staticmethod
    def _validate_branch(branch: str) -> None:
        if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch) or branch.startswith((".", "/", "-")) or ".." in branch:
            raise WorkspaceError("branch must be a safe git branch name")

    def apply_files(self, workspace: Path, files: dict[str, str]) -> None:
        workspace = workspace.resolve()
        for relative_path, content in files.items():
            target = (workspace / relative_path).resolve()
            if workspace not in target.parents:
                raise WorkspaceError(f"file path escapes workspace: {relative_path}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    def run(self, workspace: Path, command: tuple[str, ...], timeout: int = 600) -> CommandResult:
        if not command or any(not isinstance(part, str) or not part for part in command):
            raise WorkspaceError("command must be a non-empty argv tuple")
        return self._run(command, cwd=workspace, timeout=timeout)

    @staticmethod
    def _run(command: tuple[str, ...], cwd: Path, timeout: int = 120) -> CommandResult:
        try:
            completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise WorkspaceError(str(exc)) from exc
        result = CommandResult(command, completed.returncode, completed.stdout, completed.stderr)
        if result.returncode != 0:
            raise WorkspaceError(f"command failed ({result.returncode}): {' '.join(command)}\\n{result.stderr}")
        return result
