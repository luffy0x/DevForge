import json

from devforge.github import GitHubIssueSource
from devforge.models import TaskStatus
from devforge.queue import TaskStore
from devforge.workflow import DevForgeWorkflow


def test_workflow_accepts_repository_url_and_queues_issue(tmp_path) -> None:
    payload = [{"number": 1, "title": "Fix bug", "body": "steps", "labels": [{"name": "help wanted"}]}]
    source = GitHubIssueSource(request=lambda request: json.dumps(payload).encode())
    workflow = DevForgeWorkflow(("https://github.com/acme/app.git",), TaskStore(tmp_path / "db"), source)
    result = workflow.scan()
    assert result.discovered == 1
    assert result.queued == 1
    assert result.tasks[0].status is TaskStatus.QUEUED
