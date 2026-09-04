# DevForge MVP

## Goal

Turn actionable GitHub issues into a controlled implementation queue and, later, pull requests.

## Workflow

1. **Finder** reads issues for configured repositories and emits normalized candidates.
2. **Score** evaluates candidates using deterministic checks first; an LLM is an optional fallback for ambiguous descriptions.
3. **Contributor** claims an approved task, prepares an implementation plan, and executes changes in an isolated workspace. Every mutation must be reviewable through a pull request.

## Task state

`pending → scored → queued → working → fulfilled | rejected`

State transitions are persisted and idempotent. A task is deduplicated by repository plus issue number.

## Deliberate exclusions

The MVP does not autonomously merge PRs, deploy services, build images, or run a separate CI/Code Review agent. GitHub Actions and deployment automation are follow-up phases.

## Safety boundaries

- Never work on an issue without a repository allow-list.
- Never execute destructive commands without an explicit task policy.
- Never merge or push directly to the default branch.
- Preserve issue URL, score reasons, and execution logs for auditability.
