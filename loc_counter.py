# count_loc.py

from pathlib import Path
import sys


IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "build",
    "dist",
}


def count_lines(repo_root: str) -> int:
    root = Path(repo_root).resolve()

    if not root.exists():
        raise FileNotFoundError(
            f"Path does not exist: {root}"
        )

    total_lines = 0

    for file_path in root.rglob("*.py"):

        relative_path = file_path.relative_to(root)

        # Ignore virtual environments, caches, etc.
        if any(
            part in IGNORED_DIRS
            for part in relative_path.parts
        ):
            continue

        try:
            with file_path.open(
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as file:
                total_lines += sum(
                    1 for _ in file
                )

        except OSError:
            pass

    return total_lines


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python count_loc.py <repo_root>"
        )
        sys.exit(1)

    repo_root = sys.argv[1]

    total = count_lines(repo_root)

    print()
    print(f"Lines of code: {total:,}")
    print()


if __name__ == "__main__":
    main()
