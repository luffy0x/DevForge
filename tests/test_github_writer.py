import json

from devforge.github_writer import GitHubRepositoryWriter


def test_writer_builds_branch_file_and_draft_pr_requests() -> None:
    calls = []

    def fake(request):
        calls.append((request.method, request.full_url, json.loads(request.data)))
        if request.method == "POST" and request.full_url.endswith("/git/refs"):
            return b'{"ref":"refs/heads/feat/1"}'
        if request.method == "PUT":
            return b'{"commit":{"sha":"commit-sha"}}'
        return b'{"number":12}'

    writer = GitHubRepositoryWriter("token", request=fake)
    assert writer.create_branch("acme/app", "feat/1", "base-sha").endswith("feat/1")
    assert writer.commit_file("acme/app", "feat/1", "fix.py", "print(1)", "feat: fix") == "commit-sha"
    assert writer.create_draft_pr("acme/app", "feat/1", "main", "feat: fix") == 12
    assert calls[0][2]["sha"] == "base-sha"
    assert calls[1][2]["branch"] == "feat/1"
    assert calls[2][2]["draft"] is True
