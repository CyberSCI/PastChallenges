# This script just helps pack things up
import tarfile
from pathlib import Path

from gitignore_filter import git_ignore_filter

PROJECT_DIR = Path(__file__).parent.parent.absolute()
RELEASE_DIR = PROJECT_DIR.parent / "release_files"
CUSTOM_PATTERNS = [
    "scripts/data/*",
    "!scripts/data/fixtures.json",
    "devenv.local.nix",
    ".opencode",
    ".serena",
]


def main():
    release_files = git_ignore_filter(
        PROJECT_DIR.as_posix(), custom_patterns=CUSTOM_PATTERNS
    )
    server_files = git_ignore_filter(PROJECT_DIR.as_posix())

    with (
        tarfile.open(RELEASE_DIR / "source.tar.xz", "w:xz") as source,
        tarfile.open(PROJECT_DIR / "server.tar.xz", "w:xz") as server,
    ):
        for file in release_files:
            source.add(file)
        for file in server_files:
            server.add(file)


if __name__ == "__main__":
    main()
