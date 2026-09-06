from .models import CandidateTask, Issue


class ScoreAgent:
    """Score contribution suitability with cheap deterministic signals."""

    def score(self, issue: Issue) -> CandidateTask:
        title = issue.title.lower()
        labels = {label.lower() for label in issue.labels}
        points = 0.0
        reasons: list[str] = []

        if labels & {"good first issue", "help wanted"}:
            points += 0.35
            reasons.append("community labels indicate a suitable contribution")
        if labels & {"bug", "enhancement", "feature", "documentation"} or any(label.startswith(("component/", "sdk/")) for label in labels):
            points += 0.15
            reasons.append("repository labels classify an actionable scope")
        if labels & {"size/xs", "size/s"}:
            points += 0.10
            reasons.append("small size label suggests bounded implementation effort")
        if any(word in title for word in ("bug", "fix", "feat", "feature", "support", "add", "implement", "allow", "handle", "docs")):
            points += 0.25
            reasons.append("title contains an actionable change signal")
        body_length = len(issue.body.strip())
        if body_length:
            points += 0.10
            reasons.append("issue includes implementation context")
        if body_length >= 200:
            points += 0.10
            reasons.append("issue contains detailed context or acceptance criteria")
        if any(label in labels for label in ("security", "breaking-change")):
            points -= 0.35
            reasons.append("high-risk label requires manual review")

        score = max(0.0, min(1.0, points))
        return CandidateTask(issue=issue, score=score, reasons=tuple(reasons))
