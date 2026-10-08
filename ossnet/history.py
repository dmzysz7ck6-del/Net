"""Turn `git log` output into a clean, analysis-ready commit history.

Every non-merge commit reachable from HEAD becomes a `Commit` with merged
contributor identities and stable file ids that survive renames. Bot
accounts lose their credit, and files that say little about who knows the
code (lockfiles, vendored code, changelogs, contributor lists) are ignored.
"""

from __future__ import annotations

import fnmatch
import functools
import re
import subprocess
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

_RECORD, _FIELD, _TRAILER = "\x1e", "\x1f", "\x1d"
_FORMAT = "%x1e%H%x1f%aN%x1f%aE%x1f%at%x1f%(trailers:key=Co-authored-by,valueonly,separator=%x1d)"
_EARLIEST = 315532800  # 1980-01-01; older author dates are clock errors

DEFAULT_IGNORE = (
    "*.lock",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "pnpm-lock.yaml",
    "go.sum",
    "vendor/*",
    "*/vendor/*",
    "_vendor/*",
    "*/_vendor/*",
    "vendored/*",
    "*/vendored/*",
    "third_party/*",
    "*/third_party/*",
    "node_modules/*",
    "*/node_modules/*",
)

# Files nearly everyone touches. They would tie together people who never
# worked on the same code.
_META_FILE = re.compile(
    r"(authors|contributors|changelog|changes|history|news|release[-_]?notes)"
    r"(\.(md|rst|txt|markdown|adoc))?",
    re.IGNORECASE,
)

_BOT = re.compile(
    r"\[bot\]|(?<![a-z])bot(?![a-z])|dependabot|renovate|github-actions|"
    r"pre-commit-ci|greenkeeper|snyk|imgbot|semantic-release|allcontributors|"
    r"codecov|weblate|transifex|crowdin",
    re.IGNORECASE,
)

# AI coding assistants that sign commits as an author or co-author. Matched
# on exact identities: plenty of people are named Claude or Devin.
_AI = re.compile(
    r"noreply@anthropic\.com|^claude (code|opus|sonnet|haiku|fable)\b|"
    r"(^|\+)copilot(@|$)|copilot-swe-agent|cursoragent@cursor\.com|"
    r"codex@openai\.com|chatgpt-codex|google-labs-jules|gemini-code-assist|"
    r"devin-ai-integration",
    re.IGNORECASE,
)
_AIDER_SUFFIX = " (aider)"  # aider appends this to the human author's name

# Placeholder identities that must not be used to merge different people.
_GENERIC_NAMES = {
    "", "root", "unknown", "admin", "administrator", "user", "ubuntu", "github",
    "anonymous", "none", "nobody", "your name", "you",
}
_GENERIC_EMAIL = re.compile(
    r"^$|^\(?none\)?$|@(localhost|example\.(com|org))$|^(root|user|you|admin)@",
    re.IGNORECASE,
)
_IDENT = re.compile(r"^\s*(.*?)\s*<([^>]*)>\s*$")
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\", "a": "\a", "b": "\b",
            "f": "\f", "r": "\r", "v": "\v"}


class GitError(RuntimeError):
    pass


@dataclass(frozen=True)
class Commit:
    """One non-merge commit.

    `authors` lists the author first, then any Co-authored-by people; it is
    empty for commits made only by bots or AI agents, which are kept so file
    creations, renames and deletions stay in sync. `files` holds the ids of
    files whose content changed. A `bulk` commit touched more than
    `max_files` files (mass reformatting, vendoring, imports) and is not
    counted as editing. `assisted` marks commits signed by an AI assistant.
    """

    sha: str
    time: int
    authors: tuple[str, ...]
    files: tuple[int, ...]
    created: tuple[int, ...]
    deleted: tuple[int, ...]
    bulk: bool
    assisted: bool = False


@dataclass
class History:
    repo: str
    head: str
    commits: list[Commit]          # oldest first, parents before children
    aliases: dict[str, list[str]]  # person -> raw "Name <email>" identities
    paths: dict[int, str]          # file id -> latest known path
    alive: frozenset[int]          # file ids present at HEAD
    bots: Counter                  # excluded bot identity -> commit count
    assistants: Counter            # excluded AI assistant identity -> commit count
    max_files: int                 # commits touching more files than this are bulk

    @property
    def human_commits(self) -> list[Commit]:
        return [c for c in self.commits if c.authors]


@dataclass(frozen=True)
class _Change:
    status: str
    path: str
    old_path: str | None = None
    similarity: int = 100


@dataclass(frozen=True)
class _RawCommit:
    sha: str
    author: tuple[str, str]
    time: int
    coauthors: tuple[tuple[str, str], ...]
    changes: tuple[_Change, ...]


def is_bot(name: str, email: str) -> bool:
    return bool(_BOT.search(name) or _BOT.search(email.split("@")[0]))


def is_ai(name: str, email: str) -> bool:
    return bool(_AI.search(name) or _AI.search(email))


def load_history(
    repo: str | Path,
    *,
    renames: bool = True,
    since: str | None = None,
    keep_bots: bool = False,
    ignore: tuple[str, ...] = DEFAULT_IGNORE,
    ignore_meta: bool = True,
    max_files: int = 50,
) -> History:
    raw = [
        c for c in _parse_log(_git_log(repo, renames=renames, since=since))
        if _EARLIEST <= c.time <= time.time() + 86400
    ]

    bots: Counter = Counter()
    assistants: Counter = Counter()
    idents: Counter = Counter()
    for c in raw:
        for ident in (c.author, *c.coauthors):
            if is_ai(*ident):
                assistants[ident[0] or ident[1]] += 1
            elif not keep_bots and is_bot(*ident):
                bots[ident[0] or ident[1]] += 1
            else:
                idents[_strip_aider(ident)] += 1
    person = _merge_identities(idents)

    tracker = _FileTracker(_ignore_matcher(ignore, ignore_meta))
    commits = []
    for c in raw:
        files, created, deleted = tracker.apply(c.changes)
        signers = (c.author, *c.coauthors)
        authors = tuple(dict.fromkeys(
            person[_strip_aider(i)] for i in signers if _strip_aider(i) in person
        ))
        commits.append(Commit(
            sha=c.sha, time=c.time, authors=authors, files=tuple(files),
            created=tuple(created), deleted=tuple(deleted), bulk=len(files) > max_files,
            assisted=any(is_ai(*i) or i[0].endswith(_AIDER_SUFFIX) for i in signers),
        ))

    aliases: dict[str, list[str]] = {}
    for (name, email), label in person.items():
        aliases.setdefault(label, []).append(f"{name} <{email}>")
    return History(
        repo=repo_name(repo),
        head=_git(repo, "rev-parse", "HEAD"),
        commits=commits,
        aliases=aliases,
        paths=tracker.paths,
        alive=frozenset(tracker.ids.values()),
        bots=bots,
        assistants=assistants,
        max_files=max_files,
    )


def _strip_aider(ident: tuple[str, str]) -> tuple[str, str]:
    name, email = ident
    return (name.removesuffix(_AIDER_SUFFIX), email)


def repo_name(repo: str | Path) -> str:
    try:
        url = _git(repo, "config", "--get", "remote.origin.url")
    except GitError:
        url = ""
    if url:
        parts = re.split(r"[/:]", url.rstrip("/").removesuffix(".git"))
        return "/".join(p for p in parts[-2:] if p)
    return Path(repo).resolve().name.removesuffix(".git")


def clone(url: str, cache_dir: Path, *, refresh: bool = False) -> Path:
    """Bare, blobless clone of `url` under `cache_dir`: full history, no file contents."""
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", url.split("://")[-1].removesuffix(".git")).strip("_")
    dest = cache_dir / f"{slug}.git"
    if not dest.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        _run(["git", "clone", "--quiet", "--bare", "--filter=blob:none", url, str(dest)])
    elif refresh:
        _run(["git", "-C", str(dest), "fetch", "--quiet", "origin", "+refs/heads/*:refs/heads/*"])
    return dest


def _git_log(repo: str | Path, *, renames: bool, since: str | None) -> str:
    cmd = [
        "git", "-C", str(repo), "-c", "core.quotePath=false", "log", "--no-merges",
        "--date-order", "--reverse", "--name-status", f"--format={_FORMAT}",
        "-M" if renames else "--no-renames",
    ]
    if since:
        cmd.append(f"--since={since}")
    cmd.append("HEAD")
    return _run(cmd)


def _git(repo: str | Path, *args: str) -> str:
    return _run(["git", "-C", str(repo), *args]).strip()


def _run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise GitError(proc.stderr.decode(errors="replace").strip() or f"{cmd[0]} failed")
    return proc.stdout.decode("utf-8", errors="replace")


def _parse_log(text: str):
    for record in text.split(_RECORD)[1:]:
        header, _, body = record.partition("\n")
        sha, name, email, ts, trailers = header.split(_FIELD)
        yield _RawCommit(
            sha=sha,
            author=(name.strip(), email.strip()),
            time=int(ts),
            coauthors=tuple(_parse_ident(v) for v in trailers.split(_TRAILER) if v.strip()),
            changes=tuple(c for line in body.splitlines() if (c := _parse_change(line))),
        )


def _parse_ident(value: str) -> tuple[str, str]:
    m = _IDENT.match(value)
    return (m.group(1), m.group(2).strip()) if m else (value.strip(), "")


def _parse_change(line: str) -> _Change | None:
    parts = line.split("\t")
    if len(parts) < 2 or not parts[0]:
        return None
    kind, score = parts[0][0], parts[0][1:]
    if kind in "RC" and len(parts) >= 3:
        return _Change(kind, _unquote(parts[2]), _unquote(parts[1]), int(score) if score.isdigit() else 100)
    return _Change(kind, _unquote(parts[1]))


def _unquote(path: str) -> str:
    """Undo git's C-style quoting of unusual file names."""
    if len(path) < 2 or path[0] != '"' or path[-1] != '"':
        return path
    body, out, i = path[1:-1], bytearray(), 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body):
            octal = body[i + 1:i + 4]
            if len(octal) == 3 and all(d in "01234567" for d in octal):
                out.append(int(octal, 8))
                i += 4
                continue
            out += _ESCAPES.get(body[i + 1], body[i + 1]).encode()
            i += 2
            continue
        out += ch.encode()
        i += 1
    return out.decode("utf-8", errors="replace")


def _merge_identities(idents: Counter) -> dict[tuple[str, str], str]:
    """Map each raw (name, email) to one person, joining identities that share
    a real name or email address. Each person is labelled with their most
    used name."""
    parent: dict = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for name, email in idents:
        node = ("ident", name, email)
        find(node)
        normalized = " ".join(name.split()).casefold()
        if normalized not in _GENERIC_NAMES:
            union(node, ("name", normalized))
        if not _GENERIC_EMAIL.search(email.strip()):
            union(node, ("email", email.strip().casefold()))

    names: dict = {}
    for (name, email), n in idents.items():
        names.setdefault(find(("ident", name, email)), Counter())[name] += n
    labels, used = {}, Counter()
    for root, counts in sorted(names.items(), key=lambda kv: -sum(kv[1].values())):
        label = counts.most_common(1)[0][0] or "unknown"
        used[label] += 1
        labels[root] = label if used[label] == 1 else f"{label} ({used[label]})"
    return {ident: labels[find(("ident", *ident))] for ident in idents}


def _ignore_matcher(patterns: tuple[str, ...], ignore_meta: bool):
    by_name = [p.lower() for p in patterns if "/" not in p]
    by_path = [p.lower() for p in patterns if "/" in p]

    @functools.lru_cache(maxsize=None)
    def ignored(path: str) -> bool:
        path = path.lower()
        name = path.rsplit("/", 1)[-1]
        return (
            (ignore_meta and _META_FILE.fullmatch(name) is not None)
            or any(fnmatch.fnmatchcase(name, p) for p in by_name)
            or any(fnmatch.fnmatchcase(path, p) for p in by_path)
        )

    return ignored


class _FileTracker:
    """Gives each file a stable id that follows it through renames."""

    def __init__(self, ignored):
        self.ignored = ignored
        self.ids: dict[str, int] = {}    # current path -> id
        self.paths: dict[int, str] = {}  # id -> latest path

    def _new(self, path: str) -> int:
        fid = len(self.paths)
        self.ids[path] = fid
        self.paths[fid] = path
        return fid

    def apply(self, changes: tuple[_Change, ...]):
        files, created, deleted = [], [], []
        for ch in changes:
            if ch.status == "D":
                fid = self.ids.pop(ch.path, None)
                if fid is not None:
                    deleted.append(fid)
                continue
            old = self.ids.pop(ch.old_path, None) if ch.status == "R" else None
            if self.ignored(ch.path):
                if old is not None:
                    deleted.append(old)  # moved somewhere we don't track
                continue
            if old is not None:
                self.ids[ch.path] = old
                self.paths[old] = ch.path
                if ch.similarity < 100:
                    files.append(old)
            elif ch.path in self.ids:
                # Already tracked: re-added on another branch, or a type change.
                files.append(self.ids[ch.path])
            else:
                # New file, a copy, or a file whose creation predates the history.
                fid = self._new(ch.path)
                files.append(fid)
                if ch.status in "ARC":
                    created.append(fid)
        return files, created, deleted
