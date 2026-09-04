# DevForge

DevForge is an agent-driven MVP for discovering actionable GitHub issues, scoring them, and turning approved tasks into implementation pull requests.

## MVP workflow

`Finder → Score → Contributor`

The MVP intentionally excludes autonomous CI/CD, deployment, and automated code review. Those will be added only after the issue-to-PR loop is stable.

## Run locally

Use sample input:

```bash
python -m devforge --issues-file examples/issues.json --repository acme/app
```

Scan live GitHub issues (set `GITHUB_TOKEN` for private repositories or higher rate limits):

```bash
python -m devforge --github-repository owner/name
```

## Status

MVP core pipeline is implemented on the development branch. Changes enter `main` only through reviewed pull requests.
