from devforge.contributor import ContributorAgent
from devforge.models import CandidateTask, Issue, TaskStatus
from devforge.queue import TaskStore


def test_contributor_claims_only_queued_tasks(tmp_path) -> None:
    store = TaskStore(tmp_path / "tasks.db")
    task = CandidateTask(Issue("acme/app", 8, "Add retry policy"), 0.8)
    store.upsert(task)
    agent = ContributorAgent(store)
    assert agent.claim(task.task_key) is None
    assert store.transition(task.task_key, TaskStatus.SCORED, TaskStatus.QUEUED)

    plan = agent.claim(task.task_key)
    assert plan is not None
    assert plan.objective == "Add retry policy"
    assert store.get(task.task_key).status is TaskStatus.WORKING
    assert agent.claim(task.task_key) is None
