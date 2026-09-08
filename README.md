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

Scan live GitHub issues once (set `GITHUB_TOKEN` for private repositories or higher rate limits):

```bash
python -m devforge --github-repository owner/name
```

Continuously rescan issues and upsert new queue entries every five minutes:

```bash
python -m devforge watch \
  --github-repository owner/name \
  --interval 300
```

Use `--once` to validate the watch configuration without looping. The watcher only performs Finder/Score/queue work; it never claims or executes a Contributor task automatically.

Inspect persisted tasks:

```bash
python -m devforge tasks
python -m devforge tasks --status queued
python -m devforge tasks --status failed
```

Completed tasks include their generated draft-PR URL. Failed tasks include their most recent execution error; `devforge retry` clears that error before returning a task to the queue. Existing SQLite databases are migrated automatically when DevForge starts.

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
  --branch devforge/issue-123
```

DevForge resolves the current SHA of `main` automatically. Use `--base-branch` for a different target branch, or `--base-sha` to pin an explicit commit. The command uses `DEVFORGE_MODEL` (default `gpt-5.5`) and `DEVFORGE_MODEL_ENDPOINT` (default OpenAI Chat Completions endpoint) when set. It sends the model a bounded, text-only repository snapshot (excluding Git metadata, dotenv files, and common private-key formats), then expects a JSON proposal containing `files`, `test_command`, and `summary`. Proposed paths must be repository-relative; absolute paths and `..` traversal are rejected. Test commands must use an approved executable in argv form; shell syntax and unknown executables are rejected. Files are applied only inside the temporary workspace, tests must pass, and only then is a draft PR created. The generated PR body includes the DevForge task key and `Closes #<issue>` linkage.

Contributor workspaces must be clean before reuse, and generated branch names are validated before checkout. If model, workspace, test, or publishing fails, the task is marked `failed` so it can be retried explicitly:

```bash
python -m devforge retry --task owner/name#123
```

## Status

MVP core pipeline is implemented. Changes enter `main` only through reviewed pull requests.
