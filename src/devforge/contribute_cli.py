import argparse
import os
from pathlib import Path

from .agent_loop import ContributorLoop
from .github_writer import GitHubRepositoryWriter
from .model import OpenAICompatibleAdapter
from .queue import TaskStore
from .workspace import WorkspaceManager


def main() -> int:
    parser = argparse.ArgumentParser(prog="devforge contribute")
    parser.add_argument("--task", required=True)
    parser.add_argument("--repository-url", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--database", type=Path, default=Path("devforge.db"))
    parser.add_argument("--workspace-root", type=Path, default=Path(".devforge/workspaces"))
    parser.add_argument("--model", default=os.getenv("DEVFORGE_MODEL", "gpt-5.5"))
    parser.add_argument("--model-endpoint", default=os.getenv("DEVFORGE_MODEL_ENDPOINT", "https://api.openai.com/v1/chat/completions"))
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    if not api_key:
        parser.error("OPENAI_API_KEY is required")
    if not github_token:
        parser.error("GITHUB_TOKEN is required")

    loop = ContributorLoop(
        TaskStore(args.database),
        WorkspaceManager(args.workspace_root),
        OpenAICompatibleAdapter(api_key, args.model, args.model_endpoint),
        GitHubRepositoryWriter(github_token),
    )
    result = loop.run_once(args.task, args.repository_url, args.base_sha, args.branch)
    if result is None:
        print(f"unable to contribute task: {args.task}")
        return 1
    print(f"repository={result.repository}")
    print(f"branch={result.branch}")
    print(f"pull_request={result.pull_request_number}")
    return 0
