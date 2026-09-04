import json

from devforge.github import GitHubIssueSource
from devforge.models import TaskStatus
from devforge.queue import TaskStore
from devforge.workflow import DevForgeWorkflow


def test_workflow_scans_and_claims_queued_task(tmp_path) -> None:
    payload = [{"number": 3, "title": "Fix parser bug", "body": "repro", "labels": [{"name": "bug"}]}]
    source = GitHubIssueSource(request=lambda request: json.dumps(payload).encode())
    workflow = DevForgeWorkflow(("acme/app",), TaskStore(tmp_path / "db"), source)
    result = workflow.scan()
    assert result.queued == 1
    plan = workflow.claim("acme/app#3")
    assert plan is not None
    assert plan.issue_number == 3
    assert workflow.pipeline.store.get("acme/app#3").status is TaskStatus.WORKING
