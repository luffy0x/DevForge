import json
from pathlib import Path
from unittest.mock import patch

import pytest

from devforge.contributor import ContributionPlan
from devforge.model import ModelAdapterError, OpenAICompatibleAdapter


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({
            "choices": [{"message": {"content": json.dumps({
                "files": {"../escape.py": "pass"},
                "test_command": ["python", "-m", "pytest"],
            })}}]
        }).encode()


def test_model_rejects_path_traversal(tmp_path: Path) -> None:
    adapter = OpenAICompatibleAdapter("key", "model")
    plan = ContributionPlan("acme/app#1", "acme/app", 1, "Fix bug", ())
    with patch("devforge.model.urlopen", return_value=FakeResponse()):
        with pytest.raises(ModelAdapterError, match="repository-relative"):
            adapter.propose(plan, tmp_path)
