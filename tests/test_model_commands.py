import json
from pathlib import Path
from unittest.mock import patch

import pytest

from devforge.contributor import ContributionPlan
from devforge.model import ModelAdapterError, OpenAICompatibleAdapter


class FakeResponse:
    def __init__(self, command):
        self.command = command

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({
            "choices": [{"message": {"content": json.dumps({
                "files": {"src/fix.py": "pass"},
                "test_command": self.command,
            })}}]
        }).encode()


def test_model_rejects_shell_syntax(tmp_path: Path) -> None:
    adapter = OpenAICompatibleAdapter("key", "model")
    plan = ContributionPlan("acme/app#1", "acme/app", 1, "Fix bug", ())
    with patch("devforge.model.urlopen", return_value=FakeResponse(["python", "-m", "pytest; rm -rf ."])):
        with pytest.raises(ModelAdapterError, match="shell syntax"):
            adapter.propose(plan, tmp_path)


def test_model_rejects_unknown_executable(tmp_path: Path) -> None:
    adapter = OpenAICompatibleAdapter("key", "model")
    plan = ContributionPlan("acme/app#1", "acme/app", 1, "Fix bug", ())
    with patch("devforge.model.urlopen", return_value=FakeResponse(["curl", "https://example.com"])):
        with pytest.raises(ModelAdapterError, match="not allowed"):
            adapter.propose(plan, tmp_path)
