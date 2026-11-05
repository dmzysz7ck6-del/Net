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
1. **Plan v1.1 (2026-11-05, before any data were acquired): H1 inference changed.** A null
   simulation showed the registered permutation test is anti-conservative: 45% false
   positives at nominal 5%, caused by size-dependent pseudo-count residuals of zero cells.
   - New primary: a size-preserving negative-binomial simulation null; the statistic is
     the excess over it.
   - Details are in `research/analysis_plan.md` (Amendment v1.1).
   - The v1.0 statistic and p-values are still reported for transparency.
   - SHA-256 of the amended plan (v1.1): `d09d48d457a216518d70e505eb7c065369b8eee02c4dbd1ba4cda2a6688ab7ec`.
2. **Plan v1.2 (2026-11-05, before any data were acquired).** These changes follow the
   adversarial code review: rarefied JSD for H2; an article-based eligibility rule;
   paper-level sampling for fractional counts; a WDI-absent allowlist (Taiwan only);
   NB2 unit-free topology nulls with calibrated betweenness and a corrected bridge rule;
   and the corrected FWL dyadic variance. Details are in `research/analysis_plan.md`
   (Amendment v1.2). SHA-256 of plan v1.2: `98187b0bfd82174605c190d3eaff8cc5e108dc9ae4d0fb73337a6c0792c41330`.

### Adversarial code review (8-agent workflow, completed)
- Four dimension reviewers (statistics, data semantics, networks, orchestration) each
  reported findings. Each finding was then checked independently by a verifier that
  tried to refute it, using the committed code and its own scripts.
- **Result:** 28 findings. 24 were confirmed against the code as reviewed. 3 network
  findings were already resolved by fixes made during the review (the verifier checked
  them against the newer code). 1 was confirmed in a narrower form. All are now fixed:
  - **Statistics:**
    - FWL dyadic variance (the full-matrix version was indefinite with fixed effects).
    - Rarefied JSD for H2, because the plug-in bias tracks capacity.
    - Paper-level fractional sampling.
    - Bias-corrected JSD intervals.
    - Article-based eligibility.
  - **Data semantics:**
    - WDI-absent micro-territories excluded.
    - Scholarly column detection that raises on ambiguity.
    - Duplicate flow files de-duplicated.
    - k-bin sum check reported, with R1 gated on it.
    - GeoDist split-diagonal pairs removed.
    - xlsx 'NA' (Namibia) preserved.
    - Regex UN sex headers.
    - Correct group_by completeness check.
  - **Networks:**
    - NB2 unit-free nulls.
    - Null-calibrated betweenness.
    - Corrected bridge rule.
    - Degenerate AMI nulls excluded.
    - Fractional topology nulls drawn in whole papers.
  - **Orchestration:**
    - Figure 2 colour key corrected.
    - Quality-report crash fixed.
    - R4 keeps all origins.
    - Missing links shown in Figure 3.
    - Figure 5 shows `ρ_excess`.
    - Unqueried countries excluded, and pilot data refused as a full network.
    - `make verify` detects stale numbers.
    - Gravity coefficients exported to JSON.
    - R3 labels corrected.
    - R5 jackknifes M2 and M3.
    - Secrets redacted from logs.
- The analysis-relevant changes are recorded as plan amendment v1.2, still before any
  data. Tests went from 51 to 64.
