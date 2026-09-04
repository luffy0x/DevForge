from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeConfig:
    repositories: tuple[str, ...]
    threshold: float = 0.5

    def __post_init__(self) -> None:
        if not self.repositories:
            raise ValueError("at least one repository is required")
        if any("/" not in repository or repository.startswith("/") for repository in self.repositories):
            raise ValueError("repositories must use owner/name format")
        if not 0 <= self.threshold <= 1:
            raise ValueError("threshold must be between 0 and 1")
