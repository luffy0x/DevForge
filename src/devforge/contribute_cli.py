import argparse
import os
from pathlib import Path

from .agent_loop import ContributorLoop
from .github import normalize_repository
from .github_writer import GitHubRepositoryWriter
from .model import OpenAICompatibleAdapter
from .queue import TaskStore
from .workspace import WorkspaceManager


def main() -> int:
    parser = argparse.ArgumentParser(prog="devforge contribute")
    parser.add_argument("--task", required=True)
    parser.add_argument("--repository-url", required=True)
    parser.add_argument("--publish-repository", help="Repository that receives the branch; defaults to the task repository")
    parser.add_argument("--base-sha")
    parser.add_argument("--base-branch", default="main")
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
    if "#" not in args.task:
        parser.error("--task must use owner/name#issue-number format")

    task_repository = args.task.rsplit("#", 1)[0]
    publish_repository = normalize_repository(args.publish_repository) if args.publish_repository else task_repository
    writer = GitHubRepositoryWriter(github_token)
    base_sha = args.base_sha or writer.get_branch_head(publish_repository, args.base_branch)
    loop = ContributorLoop(
        TaskStore(args.database),
        WorkspaceManager(args.workspace_root),
        OpenAICompatibleAdapter(api_key, args.model, args.model_endpoint),
        writer,
        args.base_branch,
    )
    result = loop.run_once(
        args.task,
        args.repository_url,
        base_sha,
        args.branch,
        publish_repository=publish_repository,
    )
    if result is None:
        print(f"unable to contribute task: {args.task}")
        return 1
    print(f"repository={result.repository}")
    print(f"publish_repository={publish_repository}")
    print(f"base_sha={base_sha}")
    print(f"branch={result.branch}")
    print(f"pull_request={result.pull_request_number}")
    return 0
