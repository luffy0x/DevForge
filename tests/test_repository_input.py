import pytest

from devforge.github import normalize_repository


@pytest.mark.parametrize(
    "value",
    [
        "opensandbox-group/OpenSandbox",
        "https://github.com/opensandbox-group/OpenSandbox",
        "https://github.com/opensandbox-group/OpenSandbox.git",
        "  opensandbox-group/OpenSandbox/ ",
    ],
)
def test_normalize_repository(value: str) -> None:
    assert normalize_repository(value) == "opensandbox-group/OpenSandbox"


def test_normalize_repository_rejects_other_hosts() -> None:
    with pytest.raises(ValueError, match="github.com"):
        normalize_repository("https://gitlab.com/acme/app")
