from devforge.models import Issue
from devforge.scoring import ScoreAgent


def test_component_and_size_labels_can_queue_detailed_issue() -> None:
    issue = Issue("acme/app", 1, "feat: improve SDK behavior", "x" * 250, ("component/server", "size/S"))
    task = ScoreAgent().score(issue)
    assert task.score >= 0.5
