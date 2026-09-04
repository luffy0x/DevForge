import json

from devforge.github import GitHubIssueSource


def test_source_filters_pull_requests_and_normalizes_labels() -> None:
    payload = [
        {"number": 1, "title": "Fix bug", "body": None, "labels": [{"name": "bug"}], "html_url": "u"},
        {"number": 2, "title": "A PR", "pull_request": {}, "labels": []},
    ]
    source = GitHubIssueSource(request=lambda request: json.dumps(payload).encode())
    issues = source.list_open_issues("acme/app")
    assert len(issues) == 1
    assert issues[0].number == 1
    assert issues[0].labels == ("bug",)
    assert issues[0].body == ""


def test_source_clamps_page_size() -> None:
    seen = []
    source = GitHubIssueSource(request=lambda request: seen.append(request.full_url) or b"[]")
    source.list_open_issues("acme/app", per_page=1000)
    assert "per_page=100" in seen[0]
