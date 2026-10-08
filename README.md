# Net

Network-science tools for social questions. The first one is **ossnet**: a
health check for open-source communities, built from nothing but a project's
git history.

## ossnet

Point it at a repository and it answers questions maintainers and researchers
care about:

- **Who would we lose?** The truck factor (the fewest people whose departure
  would leave most files without anyone who wrote them), and how much of the
  code's know-how has already walked away.
- **How concentrated is the work?** How many people make 80% of the commits,
  and whether that is shrinking.
- **What does the collaboration network look like?** Who works with whom,
  its communities, its core and periphery, and the people who bridge groups.
- **Do newcomers stay, and what predicts it?** Retention by the year people
  joined, and whether newcomers whose early work connected them to the core
  team stuck around longer.
- **How much work is AI-assisted?** Commits co-signed by coding assistants are
  counted separately, and assistants are never counted as people.

### Quick start

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e .
ossnet https://github.com/pallets/flask.git      # clones history only, no file contents
ossnet path/to/local/repo -o reports/myproject
```

It prints a summary and writes `report.html` (charts, network map, tables),
`summary.json` (everything), and `timeline.csv`, `contributors.csv` and
`newcomers.csv` for your own analysis.

```text
pallets/flask: 3,678 commits by 835 people, 2010-04-06 to 2026-10-07

Last 12 months (2025-10-07 to 2026-10-07)
  Activity       59 commits from 7 people, 5 of them new
  Concentration  1 person made 80% of commits; David Lord made 85%
  Truck factor   1: David Lord
  Know-how       80% of files have one main author; for 30%, every main author has gone a year without committing
  Network        7 people, 7 ties, 1 community (modularity 0.00), core of 2 (fit 1.00)
  Brokers        David Lord

Newcomers who stayed (committed again 12–24 months after their first commit)
  Overall        5% (42 of 814); 73% made a single commit
  Early work     1 commit: 4% (27 of 640); 2+ commits: 8% (14 of 173)
  Early core tie with: 5% (28 of 515); without: 4% (13 of 298)
```

Run `ossnet --help` for the options (time periods, retention window, extra
ignore patterns, and so on).

### A first look across six projects

Run in October 2026 on six well-known projects. "Stayed" means committing
again 12–24 months after the first commit; "overlapped with core" means the
newcomer's first 90 days of work touched files the core team was working on.

| Project | Truck factor | Files whose main authors left | Newcomers who stayed | 1 early commit | 2+ early commits | 2+, overlapped with core | 2+, no overlap |
|---|---|---|---|---|---|---|---|
| pallets/flask | 1 | 30% | 5% (42/814) | 4% (27/640) | 8% (14/173) | 10% (14/138) | 0% (0/35) |
| psf/requests | 2 | 51% | 5% (35/735) | 3% (12/470) | 8% (22/264) | 8% (20/237) | 7% (2/27) |
| networkx/networkx | 4 | 57% | 8% (58/768) | 4% (19/531) | 16% (38/236) | 19% (35/185) | 6% (3/51) |
| jqlang/jq | 3 | 79% | 5% (11/208) | 2% (3/159) | 15% (7/48) | 16% (6/37) | 9% (1/11) |
| sharkdp/bat | 8 | 79% | 6% (22/378) | 3% (7/205) | 8% (14/172) | 9% (12/139) | 6% (2/33) |
| axios/axios | 1 | 10% | 2% (11/484) | 1% (4/422) | 10% (6/61) | 11% (6/54) | 0% (0/7) |

Two patterns hold in every project:

- **Early momentum matters most.** Newcomers who made a second commit within
  90 days were far more likely to stay (Mantel–Haenszel odds ratio 3.7 across
  the six projects, p < 0.001).
- **Among those, early overlap with the core helps.** Engaged newcomers whose
  work touched the core team's files stayed more often in all six projects
  (odds ratio 2.8, p ≈ 0.007). That fits research on social capital and
  sustained participation (Zhou and Mockus 2012; Qiu et al. 2019). The
  no-overlap groups are small, though, and six hand-picked projects are a
  lead, not a finding.

### How it works

1. **History.** Non-merge commits on the default branch, read with
   `git log`. Identities sharing a name or email are merged, Co-authored-by
   trailers credit everyone on a commit, and file ids follow renames. Bots
   (matched by name patterns such as `[bot]`) and AI assistants (matched by
   their exact identities, since plenty of people are named Claude or Devin)
   are not counted as people. Lockfiles, vendored code, changelogs and contributor
   lists are ignored, and commits touching more than 50 files (reformatting,
   imports) count only as file creations.
2. **Network.** People are linked when they change the same file. Each
   shared file adds 1/(n−1) to the tie between each pair of its n editors
   (Newman 2001), so a file two people share counts for more than one ten
   people touched. Co-authoring a commit adds a direct tie.
3. **Measures.**
   - **Truck factor:** Avelino et al. (2016), with file authorship from the
     degree-of-authorship model (Fritz et al. 2014).
   - **Communities:** the Louvain method.
   - **Core and periphery:** Borgatti and Everett's discrete model, fitted by
     scanning people ranked by tie strength.
   - **Brokers:** betweenness centrality.
   - **Concentration:** the smallest group making 80% of commits (Mockus et
     al. 2002) and the Gini coefficient.
   - **Retention:** uses a fixed window (a commit 12–24 months after the first
     one), so old and recent cohorts get the same chance to qualify.

The code is small and readable: `ossnet/history.py` (git parsing),
`ossnet/network.py` (graphs), `ossnet/health.py` (measures),
`ossnet/report.py` (output).

### Limits

- Git only records accepted work. Rejected pull requests, code review, and
  issue discussion are invisible, so the "network" is who worked on the same
  code, not who talked to whom.
- File-based authorship credits people who wrote code, not maintainers who
  know it from reviewing it, so "files whose main authors left" overstates
  lost knowledge in projects with active reviewers.
- Identity merging is heuristic; add a `.mailmap` to the repository to fix
  mistakes (git applies it automatically).
- These are associations. Newcomers who stay may seek out core files rather
  than be retained by them.

**Responsible use:** the input is public commit metadata, and the output
describes projects, not individual worth. Don't use it to rank or evaluate
people.

### Where this could go next

- Pull real social ties (PR reviews and comments) from the GitHub API, and
  test whether being reviewed by core members predicts staying.
- Run it across thousands of projects with GH Archive, and fit survival
  models with proper controls.
- Track AI-assisted contributions: do projects with more of them onboard
  newcomers differently?

### Development

```sh
pip install -e '.[test]'
pytest
```

The tests build small git repositories with known answers and check each
measure against hand-computed values.
