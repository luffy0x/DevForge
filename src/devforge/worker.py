from collections.abc import Callable

from .contributor import ContributionPlan, ContributorAgent
from .models import TaskStatus
from .queue import TaskStore


class ContributorWorker:
    """Run one claimed task through an injected executor.

    The executor is deliberately injected so repository mutation can be tested
    and reviewed independently from queue bookkeeping.
    """

    def __init__(self, store: TaskStore, execute: Callable[[ContributionPlan], None]) -> None:
        self.agent = ContributorAgent(store)
        self.store = store
        self.execute = execute

    def run_once(self, task_key: str) -> bool:
        plan = self.agent.claim(task_key)
        if plan is None:
            return False
        try:
            self.execute(plan)
        except Exception:
            # Keep the task in working for inspection and retry policy.
            raise
        return self.store.transition(task_key, TaskStatus.WORKING, TaskStatus.FULFILLED)
