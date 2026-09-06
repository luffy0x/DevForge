# DevForge

DevForge is an agent-driven MVP for discovering actionable GitHub issues, scoring them, and turning approved tasks into implementation pull requests.

## MVP workflow

`Finder → Score → Contributor`

The MVP intentionally excludes autonomous CI/CD, deployment, and automated code review. Those will be added only after the issue-to-PR loop is stable.

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

Claim a queued task for Contributor:

```bash
python -m devforge claim --task owner/name#123
```

## Status

MVP core pipeline is implemented. Changes enter `main` only through reviewed pull requests.
