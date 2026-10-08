from ossnet.history import _ignore_matcher, _unquote, DEFAULT_IGNORE, is_ai, is_bot, load_history

ANN = "Ann Lee <ann@example.org>"
BOB = "Bob Roe <bob@example.org>"


def test_merges_identities_that_share_a_name_or_email(repo):
    repo.commit("Ann Lee <ann@lee.dev>", 0, write=["a.py"])
    repo.commit("Ann Lee <ann@work.io>", 1, write=["a.py"])
    repo.commit("A. Lee <ANN@lee.dev>", 2, write=["a.py"])
    repo.commit("Bob Roe <you@example.com>", 3, write=["b.py"])
    repo.commit("Cy Doe <you@example.com>", 4, write=["b.py"])  # placeholder email: no merge
    h = load_history(repo.path)
    assert [c.authors for c in h.commits] == [("Ann Lee",)] * 3 + [("Bob Roe",), ("Cy Doe",)]
    assert len(h.aliases["Ann Lee"]) == 3


def test_bots_and_ai_assistants_are_not_people(repo):
    repo.commit(ANN, 0, write=["a.py"])
    repo.commit("dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>", 1, write=["a.py"])
    repo.commit(BOB, 2, write=["a.py"], coauthors=["Claude Opus 4.6 <noreply@anthropic.com>"])
    repo.commit("Claude Dupont <claude@example.org>", 3, write=["a.py"])
    h = load_history(repo.path)
    assert [c.authors for c in h.commits] == [("Ann Lee",), (), ("Bob Roe",), ("Claude Dupont",)]
    assert [c.assisted for c in h.commits] == [False, False, True, False]
    assert h.bots == {"dependabot[bot]": 1}
    assert h.assistants == {"Claude Opus 4.6": 1}


def test_coauthors_are_credited_after_the_author(repo):
    repo.commit(ANN, 0, write=["a.py"], coauthors=[BOB, "Ann Lee <ann@example.org>"])
    h = load_history(repo.path)
    assert h.commits[0].authors == ("Ann Lee", "Bob Roe")


def test_file_ids_follow_renames_and_deletions(repo):
    repo.commit(ANN, 0, write=["src/a.py", "src/b.py"])
    repo.commit(BOB, 1, rename=[("src/a.py", "lib/a.py")])
    repo.commit(BOB, 2, write=["lib/a.py"])
    repo.commit(ANN, 3, delete=["src/b.py"])
    h = load_history(repo.path)
    create, move, edit, delete = h.commits
    a = create.created[0]
    assert h.paths[a] == "lib/a.py"
    assert move.files == ()  # an unchanged rename is not an edit
    assert edit.files == (a,)
    assert delete.deleted == (create.created[1],)
    assert h.alive == {a}


def test_ignored_files_are_not_tracked(repo):
    repo.commit(ANN, 0, write=["AUTHORS.rst", "package-lock.json", "vendor/x.js", "changes.py", "CHANGELOG.md"])
    h = load_history(repo.path)
    assert sorted(h.paths.values()) == ["changes.py"]


def test_bulk_commits_are_flagged(repo):
    repo.commit(ANN, 0, write=[f"f{i}.py" for i in range(5)])
    repo.commit(ANN, 1, write=["f0.py"])
    h = load_history(repo.path, max_files=3)
    assert [c.bulk for c in h.commits] == [True, False]


def test_ignore_rules_match_names_anywhere_and_paths_from_the_root():
    ignored = _ignore_matcher(DEFAULT_IGNORE, ignore_meta=True)
    assert ignored("docs/HISTORY.rst")
    assert ignored("web/node_modules/react/index.js")
    assert ignored("Cargo.lock")
    assert not ignored("src/history.py")
    assert not ignored("vendors.py")


def test_unquotes_git_paths():
    assert _unquote('"tab\\there.txt"') == "tab\there.txt"
    assert _unquote('"caf\\303\\251.md"') == "café.md"
    assert _unquote("plain.txt") == "plain.txt"


def test_identity_classifiers():
    assert is_bot("renovate[bot]", "bot@renovateapp.com")
    assert is_bot("release-bot", "release@example.org")
    assert not is_bot("Abbott Talbot", "abbott@example.org")
    assert is_ai("Copilot", "198982749+Copilot@users.noreply.github.com")
    assert is_ai("Claude", "noreply@anthropic.com")
    assert not is_ai("Devin Sevilla", "devin@example.org")
