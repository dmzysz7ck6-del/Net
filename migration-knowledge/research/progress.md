# Progress log

Newest entries at the bottom. Planned work is never described as completed.

## 2026-11-05 — Session 1

### Environment and feasibility
- The repository already contains an unrelated project (`ossnet`). This project lives in
  `migration-knowledge/` so nothing existing is overwritten.
- **Blocking issue:** the execution environment's network policy denies HTTPS CONNECT
  (HTTP 403 at the egress proxy) to every required data host: `api.openalex.org`,
  `www.un.org`, `zenodo.org`, `api.worldbank.org`, `www.cepii.fr`, `api.crossref.org`,
  `api.semanticscholar.org`, `www.nature.com`, `doi.org`. Package indexes (PyPI) work.
  No source data could be downloaded. No data were substituted or simulated.
- The literature review runs through the session's web-search tool, which is not subject
  to the container's egress policy.

### Pre-registration
- `research/analysis_plan.md` v1.0 was written before any source data were acquired.
  SHA-256 at registration: `70e95c63559b7616cab5a8420ee09659149ee39984488d12a81502feeba09e22`.

### Phase 1 — literature and source documentation (completed with limitations)
- A 13-agent workflow ran: five topic sweeps, five DOI re-verification agents and three
  source-documentation agents.
- Result: 77 unique references. 5 were independently re-verified (V2) and 63 were
  single-pass DOI–title matches from search results (V1). 9 have no confirmed DOI (U).
- The independent re-verification pass and all three documentation agents were cut short.
  The session's web-search budget (200 calls per turn, shared by all agents) ran out, and
  WebFetch is blocked for the same hosts as the container.
- Written: `research/literature_review.md`, `research/bibliography.md` (generated) and
  `research/references.json`.
- `make verify-refs` (Crossref) will upgrade the labels once `api.crossref.org` is reachable.
- Closest prior work: Chinchilla-Rodríguez et al. 2018a, 2018b; Pei et al. 2024; El Ouahi
  et al. 2021 (mobility vs collaboration); Miguélez 2018 (diaspora gravity for patents).
  In consequence, the contribution must lie in (a) general migrant stocks as a separate
  layer, (b) null-calibrated per-origin alignment, (c) the joint
  migration-plus-mobility test, judged out of sample.

### Phase 2–4 — code (completed, tested on synthetic fixtures only)
- Acquisition:
  - UN DESA workbook download.
  - Zenodo record download with MD5 checks.
  - OpenAlex exact per-k `group_by` strategy, with symmetry, sum and truncation checks,
    work-level validation for the focus origins, caching, request logging, backoff, and a
    stop on HTTP 402.
  - WDI and CEPII downloads.
- Cleaning: country crosswalk with explicit special cases; content-located UN DESA
  parser; scholarly-flow parser; counting rules (full, fractional, inter-author,
  no-mega); time-aligned panel with integrity checks.
- Analysis:
  - Alignment: raw, size-adjusted and permutation-tested, with H1/H2 tests.
  - PPML with country fixed effects, dyadic-robust variance, cross-validation, Wald
    direction test, jackknife and NB comparison.
  - NB2 predictive residual flags with parameter uncertainty and BH.
  - Topology: participation z-scores, disparity backbones, community AMI against nulls.
  - Runner covering all robustness checks R1–R11 except R8 (work-level; computed in the
    quality report) and R10 (separate windows).
- Figures 1–6 (SVG and 300-dpi PNG) plus two interactive Plotly pages, rendered and
  inspected on the synthetic fixture for layout only.
- Reporting: data-quality report generator; claim registry with `make verify` (every
  number in rendered documents must trace to an output file); Crossref reference checker.
- Tests: 51 passing (`make test`).

### Not done: blocked on data access
- Pilot extraction (Somalia, Ethiopia, Kenya, Ghana), full extraction, cleaning on real
  files, all analyses, real figures, research report, essay, findings and the final
  editorial verdict. **None of these have been run, and no results are claimed.**
- Some source details could not be confirmed from the sources: exact UN workbook name
  and layout, Zenodo file list and columns, OpenAlex limits/pricing and group_by
  semantics. They are marked "[to confirm at acquisition]" in `research/methodology.md`.
  The code is written to fail loudly if any of them differ.

### Deviations from plan
- None so far. The plan has not been modified since registration.
