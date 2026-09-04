from .models import CandidateTask, Issue


class ScoreAgent:
    """Score obvious issue signals without spending an LLM call."""

    def score(self, issue: Issue) -> CandidateTask:
        title = issue.title.lower()
        labels = {label.lower() for label in issue.labels}
        points = 0.0
        reasons: list[str] = []

        if any(label in labels for label in ("good first issue", "help wanted")):
            points += 0.45
            reasons.append("community labels indicate a suitable contribution")
        if any(word in title for word in ("bug", "fix", "support", "add", "implement")):
            points += 0.25
            reasons.append("title contains an actionable change signal")
        if issue.body.strip():
            points += 0.20
            reasons.append("issue includes implementation context")
        if any(label in labels for label in ("security", "breaking-change")):
            points -= 0.35
            reasons.append("high-risk label requires manual review")

        score = max(0.0, min(1.0, points))
        return CandidateTask(issue=issue, score=score, reasons=tuple(reasons))
