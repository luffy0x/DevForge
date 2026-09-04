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
        def create_draft_pr(self, repository, branch, base, title, body=""): calls.append(("pr", title)); return 21

    plan = ContributionPlan("acme/app#4", "acme/app", 4, "Fix parser", ("test",))
    result = ContributionPublisher(FakeWriter()).publish(plan, "base", "feat/4", {"fix.py": "pass", "test_fix.py": ""})
    assert result.pull_request_number == 21
    assert calls == [("branch", "base"), ("file", "fix.py"), ("file", "test_fix.py"), ("pr", "Fix parser")]
