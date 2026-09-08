from devforge.contributor import ContributionPlan
from devforge.github_writer import GitHubRepositoryWriter
from devforge.publisher import ContributionPublisher


def test_publisher_creates_branch_commits_files_then_pr() -> None:
    calls = []

    class FakeWriter(GitHubRepositoryWriter):
        def __init__(self):
            pass

        def create_branch(self, repository, branch, base_sha):
            calls.append(("branch", repository, base_sha))

        def commit_file(self, repository, branch, path, content, message):
            calls.append(("file", repository, path))

        def create_draft_pr(self, repository, branch, base, title, body="", head_repository=None):
            calls.append(("pr", repository, title, body, head_repository))
            return 21

    plan = ContributionPlan("acme/app#4", "acme/app", 4, "Fix parser", ("test",))
    result = ContributionPublisher(FakeWriter()).publish(
        plan, "base", "feat/4", {"fix.py": "pass", "test_fix.py": ""}, body="Parser fix"
    )
    assert result.pull_request_number == 21
    assert calls[:3] == [
        ("branch", "acme/app", "base"),
        ("file", "acme/app", "fix.py"),
        ("file", "acme/app", "test_fix.py"),
    ]
    assert calls[3][0:3] == ("pr", "acme/app", "Fix parser")
    assert "Task: `acme/app#4`" in calls[3][3]
    assert "Closes #4" in calls[3][3]


def test_publisher_can_publish_branch_from_fork() -> None:
    calls = []

    class FakeWriter(GitHubRepositoryWriter):
        def __init__(self):
            pass

        def create_branch(self, repository, branch, base_sha):
            calls.append(("branch", repository))

        def commit_file(self, repository, branch, path, content, message):
            calls.append(("file", repository))

        def create_draft_pr(self, repository, branch, base, title, body="", head_repository=None):
            calls.append(("pr", repository, head_repository))
            return 22

    plan = ContributionPlan("upstream/project#4", "upstream/project", 4, "Fix parser", ())
    result = ContributionPublisher(FakeWriter()).publish(
        plan,
        "base",
        "devforge/4",
        {"fix.py": "pass"},
        publish_repository="me/project",
    )

    assert result.repository == "upstream/project"
    assert calls == [
        ("branch", "me/project"),
        ("file", "me/project"),
        ("pr", "upstream/project", "me/project"),
    ]
