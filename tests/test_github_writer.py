import json

from devforge.github_writer import GitHubRepositoryWriter


def test_writer_builds_branch_file_and_draft_pr_requests() -> None:
    calls = []

    def fake(request):
        calls.append((request.method, request.full_url, json.loads(request.data) if request.data else None))
        if request.method == "GET":
            return b'{"object":{"sha":"main-sha"}}'
        if request.method == "POST" and request.full_url.endswith("/git/refs"):
            return b'{"ref":"refs/heads/feat/1"}'
        if request.method == "PUT":
            return b'{"commit":{"sha":"commit-sha"}}'
        return b'{"number":12}'

    writer = GitHubRepositoryWriter("token", request=fake)
    assert writer.get_branch_head("acme/app", "main") == "main-sha"
    assert writer.create_branch("acme/app", "feat/1", "base-sha").endswith("feat/1")
    assert writer.commit_file("acme/app", "feat/1", "fix.py", "print(1)", "feat: fix") == "commit-sha"
    assert writer.create_draft_pr("acme/app", "feat/1", "main", "feat: fix") == 12
    assert calls[0] == ("GET", "https://api.github.com/repos/acme/app/git/ref/heads/main", None)
    assert calls[1][2]["sha"] == "base-sha"
    assert calls[2][2]["branch"] == "feat/1"
    assert calls[3][2]["draft"] is True


def test_writer_uses_fork_owner_for_cross_repository_pr() -> None:
    payloads = []

    def fake(request):
        payloads.append(json.loads(request.data))
        return b'{"number":12}'

    writer = GitHubRepositoryWriter("token", request=fake)
    writer.create_draft_pr(
        "upstream/project",
        "devforge/4",
        "main",
        "Fix parser",
        head_repository="contributor/project",
    )

    assert payloads == [{
        "title": "Fix parser",
        "head": "contributor:devforge/4",
        "base": "main",
        "body": "",
        "draft": True,
    }]
