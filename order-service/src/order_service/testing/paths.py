from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Locate monorepo root by finding wiremock/mappings."""
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent

    for parent in (current, *current.parents):
        if (parent / "wiremock" / "mappings").is_dir():
            return parent

    raise FileNotFoundError(
        "Could not locate wiremock/mappings directory in repository"
    )


def wiremock_mappings_dir(start: Path | None = None) -> Path:
    return find_repo_root(start) / "wiremock" / "mappings"
