import os
import subprocess
from pathlib import Path

import pytest

DAY = 86400
T0 = 1_600_000_000  # 2020-09-13


class RepoBuilder:
    """Builds a git repository commit by commit with chosen authors and dates."""

    def __init__(self, path: Path):
        self.path = path
        path.mkdir(parents=True)
        self._git("init", "-q", "-b", "main")
        self._git("config", "user.name", "Committer")
        self._git("config", "user.email", "committer@example.org")

    def _git(self, *args: str, env: dict | None = None) -> None:
        subprocess.run(["git", "-C", str(self.path), *args], check=True, capture_output=True,
                       env={**os.environ, **(env or {})})

    def commit(self, author: str, day: float, *, write=(), delete=(), rename=(), coauthors=()):
        """`author` is "Name <email>"; `write` is paths (or path, content pairs)."""
        for old, new in rename:
            (self.path / new).parent.mkdir(parents=True, exist_ok=True)
            self._git("mv", old, new)
        for item in write:
            path, content = (item, None) if isinstance(item, str) else item
            file = self.path / path
            file.parent.mkdir(parents=True, exist_ok=True)
            previous = file.read_text() if file.exists() else ""
            file.write_text(content if content is not None else previous + f"{author} {day}\n")
        for path in delete:
            self._git("rm", "-q", path)
        self._git("add", "-A")
        message = "change" + ("\n\n" + "\n".join(f"Co-authored-by: {c}" for c in coauthors) if coauthors else "")
        name, email = author.rstrip(">").split(" <")
        when = f"@{int(T0 + day * DAY)} +0000"
        self._git("commit", "-q", "--allow-empty", "-m", message, env={
            "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": when,
            "GIT_COMMITTER_DATE": when,
        })


@pytest.fixture
def repo(tmp_path):
    return RepoBuilder(tmp_path / "repo")
