from devforge.contributor import ContributionPlan
from devforge.github_writer import GitHubRepositoryWriter
from devforge.publisher import ContributionPublisher


def test_publisher_creates_branch_commits_files_then_pr() -> None:
    calls = []

    class FakeWriter(GitHubRepositoryWriter):
        def __init__(self):
            pass
        def create_branch(self, repository, branch, base_sha): calls.append(("branch", base_sha))
        def commit_file(self, repository, branch, path, content, message): calls.append(("file", path))
        def create_draft_pr(self, repository, branch, base, title, body=""): calls.append(("pr", title, body)); return 21

    plan = ContributionPlan("acme/app#4", "acme/app", 4, "Fix parser", ("test",))
    result = ContributionPublisher(FakeWriter()).publish(plan, "base", "feat/4", {"fix.py": "pass", "test_fix.py": ""}, body="Parser fix")
    assert result.pull_request_number == 21
    assert calls[:3] == [("branch", "base"), ("file", "fix.py"), ("file", "test_fix.py")]
    assert calls[3][0:2] == ("pr", "Fix parser")
    assert "Task: `acme/app#4`" in calls[3][2]
    assert "Closes #4" in calls[3][2]
