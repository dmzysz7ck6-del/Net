# Technical methodology

This document specifies how every quantity is defined, how it is computed, what it
assumes and how to reproduce it. The confirmatory hypotheses and decision rules are
pre-registered in `research/analysis_plan.md`; this file explains the machinery.

**Execution status (2026-11-05):** the code for every step below is implemented and
covered by tests on synthetic fixtures. **No step has been run on real data**, because
the execution environment's network policy blocks all source hosts (see
`research/progress.md`). Where a source-specific detail could not be confirmed from the
source itself, it is marked **[to confirm at acquisition]**; the pipeline is written to
fail loudly, not silently, if the detail turns out to be different.

---

## 1. Data sources

### Dataset A — UN DESA International Migrant Stock 2024 (bilateral)
- **File:** destination-and-origin workbook of the 2024 revision
  (`undesa_pd_2024_ims_stock_by_sex_destination_and_origin.xlsx`, URL in
  `config/pipeline.yaml`) **[to confirm at acquisition: exact file name and URL]**.
  It is downloaded unmodified, and its SHA-256 is recorded in `data/raw/MANIFEST.jsonl`.
- **Unit:** the number of international migrants at mid-year living in the destination.
  - "International migrant" means foreign-born where the destination reports birthplace
    (`B`), or a foreign citizen where it reports citizenship (`C`).
  - Refugees are added where flagged (`R`).
  - Values are imputed where no data exist (`I`).
- **Orientation:** each row is one destination × origin corridor. We emit the edge
  origin → destination, so that `W[i, j]` = people born in i living in j. This is tested
  in `tests/test_undesa_parse.py`.
- **Parsing:**
  - The header row is located by its content ("Location code of destination"), not by
    position.
  - Sex-specific year columns are read from the merged super-header.
  - `..`, `-` and blank cells are **missing**. A numeric 0 is a **reported zero**.
  - Corridors absent from the workbook are **unreported**. They are treated as 0 when
    networks are built, but `corridor_status` keeps the distinction.
- **Geography:**
  - UN M49 numeric codes are mapped to ISO3. Aggregates (World, regions, income groups,
    SDG groups) and residual "Other" origins do not map, are excluded, and are
    reported (`outputs/tables/undesa_excluded_rows.csv`).
  - Per destination, the share of the migrant stock attributable to identifiable origin
    countries is reported (`undesa_destination_coverage.csv`).
- **Years used:** 2010, 2015 and 2020, all from the same 2024 revision.
  Stocks are **not** flows. Differences between years are never interpreted as
  migration.

### Dataset B — Scholarly mobility (Akbaritabar, Theile & Zagheni 2024)
- **Source:** article DOI 10.1038/s41597-024-03655-9; data repository Zenodo
  10.5281/zenodo.11145735 **[to confirm at acquisition: record ID, version, licence and
  file list; all are recorded automatically from the Zenodo API, with MD5 checksums
  verified]**.
- **Unit:** inferred moves of publishing scholars between countries per year. A move is
  a change in a scholar's modal country of affiliation between publications **[to
  confirm at acquisition: the exact inference rules, whether counts are persons or
  moves, and any small-count suppression; these will be documented here from the
  article's Methods]**.
- **Versions:** the OpenAlex-derived flows are primary. The Scopus-derived flows are
  used in robustness check R6 if released bilaterally.
- **Parsing:** origin, destination, year and count columns are identified by name. The
  country-code scheme (ISO2, ISO3, numeric or names) is inferred from the values.
  Ambiguity raises an error (`tests/test_scholarly_parse.py`).
- **Caveat:** these are affiliation-based events. They do not observe citizenship,
  birthplace or residence.

### Dataset C — OpenAlex co-authorship
- **Work definition (primary):** `type:article`, `primary_location.source.type:journal`,
  `is_retracted:false`, `is_paratext:false`, publication year in the window. One work ID
  counts once.
- **Country set of a work:** the union of `authorships[].countries` and
  `authorships[].institutions[].country_code` over all authorships.
- **Pair counting rules** (`src/cleaning/openalex.py`, tested in
  `tests/test_openalex_counting.py`):
  - *Full counting:* each distinct unordered international pair in a work gets 1,
    however many authors each country contributes.
  - *Fractional counting:* a work with k distinct countries gives `1 / (k(k−1)/2)` to
    each of its pairs, so every international work carries a total weight of 1.
  - *Inter-author counting (R8):* a pair counts only if two **different** authors carry
    the two countries. This removes pairs created solely by one multi-affiliated author.
  - *No mega-collaborations (R2):* works with more than 20 countries are dropped.
- **Acquisition strategy (exact, without downloading millions of works):**
  1. For each focal country X and window, run `group_by=countries_distinct_count`.
     This gives the number of X's works with exactly k countries.
  2. For each k ≥ 2 present, run `group_by=authorships.countries` with the filter
     `countries_distinct_count:k`. This gives `n_k(X, Y)` for every partner Y.
  3. Full count = Σ_k n_k. Fractional count = Σ_k n_k / C(k, 2). Both are exact.
- **Built-in validations:**
  - *Symmetry:* `n_k(X, Y)` from X's query must equal `n_k(Y, X)` from Y's query.
  - *Sum check:* Σ_Y n_k(X, Y), including Y = X, must equal k · N_k(X). This detects
    approximate counts or a mismatch between the country definition used by
    `countries_distinct_count` and the one used by `authorships.countries`.
  - *Truncation check:* the number of groups returned must equal `meta.groups_count`.
  - *Work-level check:* for the ten focus origins, work-level records are downloaded
    and the aggregate counts are recomputed exactly. The share of pairs that survive
    inter-author counting is reported.
- **Operational safeguards:**
  - Every response is cached on disk under a hash of the URL and the non-secret
    parameters, so runs are resumable.
  - Every request is logged (`data/raw/openalex/requests.jsonl`).
  - Per-country results are checkpointed.
  - HTTP 429/5xx responses get exponential backoff. HTTP 402 stops the run (zero-cost
    policy).
  - The contact e-mail and API key come only from environment variables (`.env`,
    git-ignored).
- **Research output (capacity):** article counts per country over the capacity window.
- **Coverage:** for each year, the share of filtered articles with no country
  information and the share that are international (`coverage_by_year.csv`).

### Dataset D — Covariates
- **World Bank WDI (API v2):**
  - Indicators: population `SP.POP.TOTL`, GDP current US$ `NY.GDP.MKTP.CD`, GDP per
    capita PPP constant `NY.GDP.PCAP.PP.KD`.
  - Income groups come from the country metadata endpoint. Aggregates (region =
    "Aggregates") are removed. Licence CC BY 4.0 **[to confirm]**.
- **CEPII GeoDist (Mayer & Zignago 2011):**
  - Variables: `distw` (population-weighted distance), `dist`, `contig`, `comlang_off`,
    `comlang_ethno`, `colony`, `comcol`.
  - Directed rows are symmetrized into unordered pairs. Binary variables take the
    maximum over the two directions; distances take the mean (they are symmetric in
    GeoDist).
  - Legacy codes are mapped: ROM→ROU, ZAR→COD, TMP→TLS, PAL→PSE.
  - YUG (Serbia and Montenegro) and ANT (Netherlands Antilles) are copied to their
    successor states and flagged `geo_imputed`.
  - Countries created after 2011 (e.g. South Sudan) have no GeoDist row. Under the
    pre-registered universe rule they are excluded from all analyses, with reason
    `absent_from_cepii`, and reported. Their geography is never imputed silently.
    South Sudan is an East African country, so this exclusion is listed as a limitation
    for RQ5.
- **Regions:** UN M49 subregions and continents via `country_converter`. "Sub-Saharan
  Africa" follows M49, i.e. Africa minus Northern Africa, so Sudan is excluded; the
  World Bank classification includes it.

## 2. Country harmonization
- **Canonical key:** ISO 3166-1 alpha-3 (`src/cleaning/countries.py`).
- **Special cases:** every non-trivial decision is listed in `SPECIAL_CASES` and written
  to `outputs/tables/harmonization_special_cases.csv`:
  - Kosovo is excluded, because UN DESA includes it in Serbia.
  - The Channel Islands aggregate is excluded.
  - Taiwan is mapped explicitly (M49 158).
  - Legacy M49 codes for former Sudan and the Netherlands Antilles are excluded.
  - CEPII legacy codes are handled as in §1.
- **Unmatched codes:** each source's unmatched codes are written to
  `outputs/tables/harmonization_<source>.csv`.

## 3. Universe and time alignment
- **Universe rule** (fixed before any outcome was seen): an entity is included if all of
  the following hold.
  1. It maps unambiguously in UN DESA, OpenAlex and CEPII.
  2. Its WDI population in the covariate year is at least 500,000. Entities absent from
     WDI are excluded (reason `no_population_data`) unless allowlisted with a documented
     reason. Only Taiwan is allowlisted (plan v1.2).
  3. It has at least one international co-authored article in the window.
- **Designs:** primary 2015 / 2010–14 / 2015–19; earlier 2010 / 2005–09 / 2010–14;
  later 2020 / 2015–19 / 2020–24; contemporaneous 2015 / 2015–19 / 2015–19
  (exploratory). The columns are migrant stock year / mobility years / co-authorship
  years.
- `src/cleaning/panel.py::check_alignment` refuses to build a design whose inputs carry
  the wrong years (`tests/test_panel.py`).

## 4. Networks
- **Layers:** `G_migration` (directed), `G_scholars` (directed), `G_collaboration`
  (undirected). They are dense matrices on the common node set with a zero diagonal
  (`src/networks/build.py`).
- **Null models** (`src/networks/nulls.py`):
  - Directed layers: the independence expectation `E = x_i y_j` with observed out- and
    in-strengths and a zero diagonal, fitted by iterative proportional fitting.
  - Undirected layers: the fitness solution `E = x_i x_j` preserving strengths.
  - Random networks are Poisson draws around E. This is the maximum-likelihood
    weighted configuration ensemble with Poisson weights.
- **Retained measures** (`src/networks/metrics.py`, rationale in the module docstring):
  strength; Herfindahl concentration and effective number of partners; extra-regional
  share and participation coefficient on UN subregions; betweenness on disparity-filter
  backbones; Louvain communities and adjusted mutual information across layers; density
  and components. Raw degree centralities are not reported, because in dense weighted
  layers they mostly re-measure size.

## 5. Statistical specifications

### 5.1 Alignment (Analysis A, H1–H2)
For each origin o:
- **Profiles:** `m_o` is row o of `G_migration` (where its emigrants live) and `c_o` is
  row o of `G_collaboration` (who its researchers co-author with), over all other
  countries in the universe.
- **Raw alignment:** Spearman ρ(m_o, c_o); top-k overlap (k = 5, 10; ties broken by
  ISO3 code); Jensen–Shannon divergence in bits between the normalized profiles.
- **Size-adjusted alignment:** Spearman ρ between `ln((W+1)/(E+1))` residual profiles of
  the two layers, where E is the layer's null expectation.
  - Inference (plan v1.1): ρ is compared with a size-preserving simulation null.
    - The origin's collaboration counts are drawn 2,000 times from
      `NB2(E^C, α̂)`, with α̂ the maximum-likelihood dispersion of the whole
      collaboration layer around E^C. The migration profile is held fixed.
    - Reported: `ρ_excess = ρ − mean(ρ_null)`, a two-sided simulation p-value, and BH
      across origins.
    - Summary test: Wilcoxon signed-rank on `ρ_excess`.
  - Why not a permutation test: permuting destination labels destroys size structure.
    Zero cells give residuals `−ln(1+E)` that fall with size in both layers, so
    permutation p-values are anti-conservative. In a null simulation they gave 45%
    false positives at nominal 5%. They are still reported, labelled "not
    size-calibrated".
  - Sensitivity: rank-partial ρ controlling for `ln E^M` and `ln E^C`.
- **Size-only divergence:** the JSD between the two layers' null expectations for o
  (what size alone implies), reported as `jsd_excess = JSD_obs − JSD_size`.
- **Uncertainty:**
  - Collaboration rows are resampled at the paper level: Poisson draws of full counts,
    converted with each pair's fractional/full ratio for fractional counting
    (1,000 replicates).
  - The raw JSD is reported bias-corrected (`2ĵ − mean ĵ*`) with a basic-bootstrap
    interval. A percentile interval of the biased plug-in statistic would sit above the
    truth.
  - Migrant stocks are published estimates without sampling distributions and are
    treated as fixed. A ±25% log-normal perturbation is available as a sensitivity
    option.
- **Eligibility:** at least 50 distinct international articles in the window (from the
  per-k totals) and at least 10,000 emigrants. The set is the same for both counting
  methods.
- **H2 (plan v1.2):**
  - Statistic: Spearman correlation across origins between the **rarefied** JSD and
    ln(output), plus a partial version controlling for the share of emigrants living in
    high-income destinations.
  - Rarefied JSD: each origin's row is subsampled without replacement to 50 paper-pair
    incidences, and the JSD is averaged over 200 draws.
  - Why: the plug-in JSD's upward small-sample bias shrinks with paper count, and so
    with capacity. That would produce H2's predicted sign by itself.

### 5.2 Gravity models (Analyses B–C, H3–H4)
- **Estimator:** PPML on all unordered pairs, `ln μ_ij = α_i + α_j + x_ij′β`, with one
  fixed effect per country entering in either position (`src/analysis/gravity.py`).
- **Identification safeguards:**
  - Countries whose outcomes are all zero are dropped iteratively.
  - Constant covariates are dropped and reported.
  - A rank check runs before fitting.
- **Variance:**
  - Dyadic-robust variance for the covariate coefficients:
    `V_β = B̃⁻¹ (Σ_c S̃_c S̃_c′ − Σ_d s̃_d s̃_d′) B̃⁻¹ · G/(G−1)`.
    Here `s̃_d = x̃_d e_d` and `B̃ = X̃′WX̃`, with X̃ the covariates residualized on the
    intercept and fixed effects using weights μ (Frisch–Waugh–Lovell).
  - Why not the full matrix: computed over the full parameter vector, the meat is
    indefinite, because each country's score sum in the fixed-effect directions is
    exactly zero by the first-order conditions.
  - A brute-force double-sum test verifies the formula. A simulation test shows it
    tracks the sampling SD under node-level dependence, where HC1 understates it by
    about half.
  - If a small sample still yields a non-PSD block, eigenvalues are clipped and
    variances floored at HC1. This is flagged.
  - HC1 (full vector) is reported alongside for comparison. It is also used for the
    parameter-uncertainty draws in §5.3.
- **Models:**

| Model | Specification |
|---|---|
| M1 | ln distw, contig, comlang_off, colony, comcol |
| M2 | M1 + ln(1 + M_ij + M_ji) |
| M3 | M2 + ln(1 + S_ij + S_ji) |
| M1_mob | M1 + mobility, for the non-nested comparison with M2 |
| M3_dir | M2 with mobility split into low→high and high→low capacity directions |
| M3_dir_both | M3_dir with migration also split by direction |

- **Out-of-sample evaluation:**
  - 10-fold cross-validation over dyads with a fixed seed. Every model uses identical
    folds and an identical evaluation set.
  - Test dyads whose country has an all-zero training outcome are excluded for all
    models.
  - Comparison: the relative reduction in out-of-fold Poisson deviance, with a paired
    fold-level t interval.
- **Diagnostics:** VIF of the dyadic regressors; correlation between ln migration and ln
  mobility; country jackknife (R5); NB2 GLM comparison (R11).

### 5.3 Residual pairs (Analysis D, E1)
- **Baseline:** M2.
- **Dispersion:** NB2 α by profile maximum likelihood given the M2 means.
  - Testing on simulated NB data showed that the Cameron–Trivedi moment estimator was
    badly biased in finite samples, so it is kept only as a diagnostic.
- **Predictive distribution:** a mixture of NB2(μ_ij(β^(b)), α) over 500 draws of
  β ~ N(β̂, V̂_dyadic).
- **Test and flags:**
  - Two-sided mid-p value, then BH across testable pairs.
  - A pair is *testable* if μ̂ ≥ 5.
  - A pair is *flagged* if q < 0.05 and |ln((C+0.5)/(μ̂+0.5))| ≥ ln 2.
  - A pair is a *missing link* if μ̂ ≥ 10 and C = 0.
- **Persistence:** the same flag in the earlier design.

### 5.4 Topology (E2, plan v1.2)
- **Null model:** NB2 around the strength-preserving expectation, with the layer's own
  maximum-likelihood dispersion. NB2's relative dispersion is unit-free, so layers
  measured in persons and in papers get comparable noise; Poisson noise would not.
- **Participation:** the unit-free deviation `P_obs − mean(P_null)` is primary, from 500
  draws. The z-score is secondary.
- **Betweenness:** computed on disparity backbones at α ∈ {0.01, 0.05, 0.10}. Each
  country's value is calibrated as a mid-rank percentile of observed betweenness within
  its betweenness on 100 null networks.
- **"Collaboration-specific bridge":** requires, for every α and both counting methods:
  1. positive co-authorship betweenness;
  2. a calibrated co-authorship score above 0.5;
  3. a higher calibrated score in co-authorship than in migration.
- **Community agreement:** AMI of Louvain partitions versus AMI between partitions of
  null draws. Single-community null partitions are excluded and counted.

## 6. Figures
- **Generation:** all figures are generated by `src/visualization/` from
  `outputs/tables` and the processed data.
- **Palette:** validated with the dataviz palette validator. The three layer colours
  (blue, orange, aqua) pass adjacent-pair colour-vision-deficiency and normal-vision
  separation on the light surface. Aqua is below 3:1 contrast, so layer identity is
  always carried by text labels as well.
- **Visual conventions:**
  - Diverging encodings use blue ↔ red with a grey midpoint.
  - Measured values are filled bars or dots.
  - Model expectations are ticks or lines.
  - Predictive ranges are shaded bands.
- **Case studies (Figure 4):** chosen by a fixed rule. These are the focus origins with
  the highest and lowest mean JSD percentile across all available windows and counting
  methods.
- **Titles:** default to neutral descriptions. Message titles are set only from computed
  results (`outputs/figure_titles.json`).

## 7. Assumptions and limitations
1. **Co-authorship is not knowledge transfer.** It is one observable form of
   cross-border research connectivity. Diaspora-mediated knowledge flows that do not
   produce co-authored papers are invisible here.
2. **Affiliations are not people.** Country of affiliation is not nationality, and a
   multi-affiliated author creates a pair (R8 measures how often).
3. **No causal identification.** Lagged designs order the measurements in time. They do
   not remove common causes: shared language, colonial history, funding programmes,
   visa regimes. All coefficients are conditional associations.
4. **Measurement dependence.** In the primary analysis, mobility and co-authorship both
   come from OpenAlex affiliations (mitigations: lag, R6, R8).
5. **Undirected outcome.** "Direction" tests (H4b) concern which side of the pair a move
   started from, not the direction of knowledge flow.
6. **Migrant stock definitions and the 'Other' residual** vary by destination (R4).
7. **Database coverage.** OpenAlex coverage and affiliation completeness differ by
   country, field and language, and the database changes over time. The extraction date
   is recorded in provenance.

## 8. Reproducing the analysis
```sh
cd migration-knowledge
pip install -e .[test]              # or: pip install -r the dependencies in pyproject.toml
cp .env.example .env                # optional: OPENALEX_MAILTO, OPENALEX_API_KEY
make test                           # unit + plumbing tests (synthetic fixtures only)
make check-access                   # all data hosts must report "ok"
make pilot                          # four-origin pilot (SOM, ETH, KEN, GHA), primary window
make research                       # full pipeline: acquire → clean → analyze → quality → figures → verify
make verify-refs                    # check bibliography DOIs against Crossref
```
- Random seeds come from `config/pipeline.yaml` (`project.seed`).
- Acquisition is cached and resumable at request granularity, so re-running after an
  interruption continues where it stopped.

### Expected runtime of the analysis stage
Benchmarked on synthetic data of the real dimensions (200 countries, 19,900 dyads,
200 fixed effects; 4 CPUs):

| Step | Time |
|---|---|
| One PPML fit with dyadic-robust variance | about 10 s |
| NB predictive simulation, 500 draws | about 4 s |
| 10-fold CV for two models | about 26 s |
| Country jackknife of M3 (200 fits, primary window only) | about 35 min |
| All other models, CV and robustness fits per window | about 15 min |

The OpenAlex extraction runs at 5 requests/s. Its duration depends on how many
distinct k values each country has, which is not known before acquisition. The request
log section of the data-quality report records it.
