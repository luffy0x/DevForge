import pytest

from devforge.config import RuntimeConfig


def test_runtime_config_accepts_valid_values() -> None:
    assert RuntimeConfig(("acme/app",), 0.7).threshold == 0.7


@pytest.mark.parametrize("repositories", [(), ("app",), ("/acme/app",)])
def test_runtime_config_rejects_invalid_repositories(repositories) -> None:
    with pytest.raises(ValueError):
        RuntimeConfig(repositories)


def test_runtime_config_rejects_invalid_threshold() -> None:
    with pytest.raises(ValueError):
        RuntimeConfig(("acme/app",), 1.1)
