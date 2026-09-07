from pathlib import Path

from devforge.contributor import ContributionPlan
from devforge.execution import ContributorExecution
from devforge.workspace import CommandResult


class FakeWorkspace:
    def prepare(self, repository_url, branch):
        return Path("/tmp/devforge-test")

    def apply_files(self, workspace, files):
        self.files = files

    def run(self, workspace, command):
        return CommandResult(command, 0, "passed", "")


def test_execution_returns_validated_artifact() -> None:
    plan = ContributionPlan("acme/app#1", "acme/app", 1, "Fix bug", ())
    result = ContributorExecution(FakeWorkspace()).run(plan, "https://github.com/acme/app.git", "devforge/1", {"fix.py": "pass"}, ("pytest",))
    assert result.plan == plan
    assert result.files == {"fix.py": "pass"}
    assert result.test_result.stdout == "passed"
