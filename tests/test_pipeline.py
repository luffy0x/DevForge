from devforge.finder import Finder
from devforge.models import Issue, TaskStatus
from devforge.scoring import ScoreAgent


def test_finder_enforces_allowlist_and_filters_wontfix() -> None:
    issues = [
        Issue("acme/app", 1, "Fix login", labels=("bug",)),
        Issue("other/app", 2, "Fix login"),
        Issue("acme/app", 3, "Old request", labels=("wontfix",)),
    ]
    result = Finder({"acme/app"}).find(issues)
    assert [issue.number for issue in result] == [1]


def test_score_agent_returns_bounded_score_and_reasons() -> None:
    issue = Issue("acme/app", 1, "Fix login bug", "Steps to reproduce", ("bug", "help wanted"))
    task = ScoreAgent().score(issue)
    assert 0 <= task.score <= 1
    assert task.status is TaskStatus.SCORED
    assert task.reasons
