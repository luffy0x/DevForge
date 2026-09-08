import json

from devforge.contributor import ContributionPlan
from devforge.model import OpenAICompatibleAdapter


def test_workspace_context_excludes_git_and_sensitive_files(tmp_path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('ok')", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("remote=secret", encoding="utf-8")
    (tmp_path / ".env").write_text("API_KEY=secret", encoding="utf-8")
    (tmp_path / "credential.pem").write_text("private key", encoding="utf-8")

    context = OpenAICompatibleAdapter._workspace_context(tmp_path)

    assert context == {"src/app.py": "print('ok')"}


def test_prompt_includes_bounded_repository_context(tmp_path) -> None:
    (tmp_path / "package.json").write_text('{"name": "demo"}', encoding="utf-8")
    plan = ContributionPlan(
        task_key="acme/demo#7",
        repository="acme/demo",
        issue_number=7,
        objective="Fix timeout",
        constraints=(),
    )

    prompt = json.loads(OpenAICompatibleAdapter._prompt(plan, tmp_path))

    assert prompt["repository_context"] == {"package.json": '{"name": "demo"}'}
    assert "workspace" not in prompt
