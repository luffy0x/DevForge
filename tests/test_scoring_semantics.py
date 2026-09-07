from devforge.models import Issue
from devforge.scoring import ScoreAgent


def test_failure_title_with_detailed_body_is_actionable() -> None:
    issue = Issue("acme/app", 1, "Kubernetes snapshots should fail closed", "x" * 2303)
    task = ScoreAgent().score(issue)
    assert task.score >= 0.5
    assert any("actionable change signal" in reason for reason in task.reasons)
