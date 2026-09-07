# DevForge

DevForge is an agent-driven MVP for discovering actionable GitHub issues, scoring them, and turning approved tasks into implementation pull requests.

## MVP workflow

`Finder → Score → Contributor`

The MVP intentionally keeps execution explicit: the contributor claims one queued task, prepares a workspace, asks a model for a bounded file proposal, runs tests, and opens a draft pull request. Autonomous CI/CD, deployment, and automated code review remain outside the MVP.

## Run locally

Install and test:

```bash
python -m pip install -e ".[test]"
python -m pytest
```

Scan live GitHub issues (set `GITHUB_TOKEN` for private repositories or higher rate limits):

```bash
python -m devforge --github-repository owner/name
```

Inspect persisted tasks:

```bash
python -m devforge tasks
python -m devforge tasks --status queued
python -m devforge tasks --status failed
```

Claim a queued task for Contributor:

```bash
python -m devforge claim --task owner/name#123
```

Execute one claimed task and open a draft PR:

```bash
export GITHUB_TOKEN=...
export OPENAI_API_KEY=...
python -m devforge contribute \
  --task owner/name#123 \
  --repository-url https://github.com/owner/name.git \
  --base-sha <base-commit-sha> \
  --branch devforge/issue-123
```

The command uses `DEVFORGE_MODEL` (default `gpt-5.5`) and `DEVFORGE_MODEL_ENDPOINT` (default OpenAI Chat Completions endpoint) when set. It expects the model to return a JSON proposal containing `files`, `test_command`, and `summary`; proposed files are applied only inside the temporary workspace, tests must pass, and only then is a draft PR created.

If model, workspace, test, or publishing fails, the task is marked `failed` so it can be retried explicitly:

```bash
python -m devforge retry --task owner/name#123
```

## Status

MVP core pipeline is implemented. Changes enter `main` only through reviewed pull requests.
