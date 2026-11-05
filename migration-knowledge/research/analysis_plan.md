# Analysis plan (pre-registration)

**Project:** The Migration Network Is Not the Knowledge Network
**Plan version:** 1.0 — written 2026-11-05, before any substantive data were acquired or inspected.
**Status of data at writing:** no observations from UN DESA, the scholarly migration
database, OpenAlex, WDI or CEPII had been downloaded. The execution environment's
network policy blocked all of those hosts (see `research/progress.md`). So this plan
was necessarily written blind to outcomes. The SHA-256 of this file at registration
is recorded in `research/progress.md`. Any later change is logged there under
"Deviations from plan", with its reason.

The premise is treated as a falsifiable hypothesis, not a conclusion. Section 7
states in advance what result would count against it.

---

## 1. Objects of study and notation

Countries are indexed by ISO 3166-1 alpha-3 codes after harmonization
(`src/cleaning/countries.py`). For a design window *w* (Section 3):

| Symbol | Definition | Direction | Source |
|---|---|---|---|
| `M_ij` | Mid-year stock of people born in *i* (or citizens of *i* where the destination reports citizenship) living in *j* | directed i→j | UN DESA IMS 2024 |
| `S_ij` | Number of inferred scholarly moves from *i* to *j*, summed over the mobility years | directed i→j | Akbaritabar, Theile & Zagheni (2024), OpenAlex-derived release; Scopus-derived release as robustness |
| `C_ij` | Full count: number of distinct journal articles (one OpenAlex work ID counts once) with at least one author affiliation in *i* and at least one in *j* | undirected | OpenAlex |
| `F_ij` | Fractional count: Σ over works containing *i* and *j* of `1 / (k(k−1)/2)`, where *k* is the work's number of distinct countries | undirected | OpenAlex |
| `P_i` | Research output: articles with at least one affiliation in *i* (capacity window) | monadic | OpenAlex |

A "journal article" is an OpenAlex work with `type = article`,
`primary_location.source.type = journal`, `is_retracted = false` and
`is_paratext = false`. Co-authorship is measured through institutional
affiliations. It says nothing about authors' birthplace or nationality. We never
describe `C_ij` as diaspora knowledge transfer. It is one observable form of
cross-border research connectivity.

## 2. Country universe (fixed in `config/pipeline.yaml`)

1. The entity maps unambiguously to one ISO3 code in UN DESA, OpenAlex and CEPII,
   or through an explicit crosswalk entry. Kosovo is excluded because UN DESA
   reports it within Serbia. Aggregates and "Other" origins are excluded and
   their volumes reported.
2. WDI population is at least 500,000 in the window's covariate year. Entities
   absent from WDI (Taiwan) are kept and flagged.
3. The entity has at least one international co-authored article in the window.

Focus origins (RQ5): SOM, ETH, KEN, UGA, TZA, RWA, GHA, NGA, SEN, ZAF.
Pilot (run first to validate the pipeline): SOM, ETH, KEN, GHA.
Comparison origins: for each focus origin, the two non-African countries
nearest in standardized (log population, log GDP per capita PPP) in the
covariate year. The rule does not use outcomes.

Because the OpenAlex query strategy yields full partner vectors for every
country, the confirmatory analyses use **all** countries in the universe. The
focus and comparison origins are used for case-study displays and for RQ5.

## 3. Time-aligned designs

| Design | Migrant stock | Scholarly mobility | Co-authorship | Capacity (`P_i`) | Role |
|---|---|---|---|---|---|
| **Primary** | 2015 | 2010–2014 | 2015–2019 | 2010–2014 | confirmatory |
| Earlier | 2010 | 2005–2009 | 2010–2014 | 2005–2009 | temporal |
| Later | 2020 | 2015–2019 | 2020–2024 | 2015–2019 | temporal |
| Contemporaneous | 2015 | 2015–2019 | 2015–2019 | 2015–2019 | exploratory only |

Stocks are not flows, so changes in stocks are never interpreted as migration.
All stock years come from one revision (2024), so revisions do not differ
across years. Lagging mobility before co-authorship orders the measurements in
time. It does not identify causal effects.

## 4. Confirmatory hypotheses

All tests are two-sided at α = 0.05 unless stated otherwise. Origin-level tests
use origins meeting the minimum-information rule: at least 50 international
co-authored articles and at least 10,000 emigrants in the window.

### H1 — Alignment beyond size (RQ1)
For origin *o* and destinations *d* ≠ *o* in the common universe, compute
margin-adjusted residuals in each layer:
`r^M_od = ln((M_od + 1)/(E^M_od + 1))` and `r^C_od = ln((C_od + 1)/(E^C_od + 1))`.
Here `E` is the independence expectation that preserves each node's total
(out- and in-strength for migration, strength for co-authorship), fitted by
iterative proportional fitting with structural zeros on the diagonal.
The statistic is the within-origin Spearman correlation `ρ_o = ρ(r^M_o·, r^C_o·)`.

* **Test.** The median `ρ_o` across eligible origins is greater than 0
  (Wilcoxon signed-rank; we caveat that origins are not independent). Per-origin
  permutation p-values come from 2,000 permutations of destination labels of
  `r^C_o·`, with Benjamini–Hochberg adjustment across origins.
* **Reported alongside:** raw-profile alignment, namely Spearman ρ between
  `M_o·` and `C_o·`, top-5 and top-10 overlap, and Jensen–Shannon divergence
  (base 2) between the normalized distributions, with parametric-bootstrap
  intervals from multinomial resampling of paper counts.

### H2 — Heterogeneity of alignment (RQ1)
The divergence between an origin's migrant-destination and
collaboration-partner distributions decreases with its research capacity.
* **Test.** Spearman correlation across eligible origins between `JSD_o`
  (full counting) and `ln P_o`. Predicted sign: negative. A partial version
  controls for the share of the origin's emigrants living in high-income
  destinations, which mechanically affects overlap with research hubs.

### H3 — Migration adds information beyond gravity (RQ2/RQ3)
PPML on all unordered pairs {i, j} in the universe, outcome `C_ij`:

* **M1:** `ln μ_ij = α_i + α_j + β₁ ln distw_ij + β₂ contig_ij + β₃ comlang_off_ij + β₄ colony_ij + β₅ comcol_ij`
* **M2:** M1 + `γ ln(1 + M_ij + M_ji)`

`α_i` and `α_j` are country fixed effects. Each country has one effect, which
enters whichever position it holds in the pair, so the effects absorb output,
GDP, population and every other country-level attribute. Inference uses
dyadic-robust (Aronow–Samii–Assenova) standard errors.
* **Test.** γ > 0 with a 95% CI excluding 0, **and** a 10-fold cross-validated
  (random folds of dyads, fixed seed) reduction in out-of-fold Poisson deviance
  for M2 relative to M1, with a fold-level paired CI excluding 0.

### H4 — Scholarly mobility adds information beyond migration (RQ3)
* **M3:** M2 + `δ ln(1 + S_ij + S_ji)`, with mobility taken from the lagged
  window and the OpenAlex-derived release.
* **Test.** δ > 0 with a 95% CI excluding 0, **and** a cross-validated deviance
  reduction for M3 relative to M2 with a CI excluding 0. We report the
  attenuation of γ from M2 to M3, and the non-nested comparison of
  M1 + migration against M1 + mobility.
* **H4b (direction, two-sided, no predicted sign).** Replace δ with
  `δ_up ln(1 + S_{low→high}) + δ_down ln(1 + S_{high→low})`, where "low" and
  "high" order the pair by capacity-window output `P`. Test `δ_up = δ_down`
  with a Wald test using the dyadic-robust covariance. Migration is decomposed
  the same way for comparison.

## 5. Exploratory analyses (pre-specified, not confirmatory)

* **E1 — Unexpectedly strong and weak pairs (RQ2).** The baseline is M2
  (structure plus migration), as RQ2 asks about collaboration "expected given
  migration, research capacity, geography".
  * For each pair, compute the predictive p-value of the observed count under
    a negative binomial (NB2) predictive distribution with mean `μ̂_ij` from M2
    and dispersion α̂ estimated from the M2 residuals.
  * Uncertainty in `μ̂` is propagated by parametric simulation from the
    coefficient covariance.
  * A pair is flagged only if all of the following hold: BH-adjusted
    q < 0.05; `μ̂ ≥ 5`; and `|ln((C+0.5)/(μ̂+0.5))| ≥ ln 2`.
  * A pair with `μ̂ ≥ 10` and `C = 0` is a "missing link".
  * Persistence: a flag is called persistent if the same pair has the same
    sign and q < 0.05 in the earlier design.
  * We keep four categories separate: high absolute collaboration, high
    relative to expectation, low relative to expectation, and missing or
    unobserved. "Untapped opportunity" language is not used.
* **E2 — Topology and bridging (RQ4).** Each layer is restricted to the common
  universe. Measures:
  1. Strength and partner concentration (Herfindahl, effective number of
     partners).
  2. Extra-regional share and participation coefficient, using UN M49
     subregions as an exogenous partition. Using a fixed partition avoids
     depending on unstable community detection.
  3. Betweenness on disparity-filter backbones at α ∈ {0.01, 0.05, 0.10}.
  4. Louvain communities, compared across layers by adjusted mutual
     information.

  Every layer comparison is benchmarked against 500 strength-preserving
  randomizations (Poisson draws from the maximum-likelihood independence model).
  A country is a "collaboration-specific bridge" only if its normalized
  bridging rank is higher in co-authorship than in migration under all three
  backbone thresholds and both counting methods.
* **E3 — Temporal comparison (RQ1/RQ4).** H1, H2 and M1–M3 are recomputed in
  the earlier and later designs. With three points per origin we describe
  change. We do not estimate dynamics.
* **E4 — Sub-Saharan focus (RQ5).** Focus origins are placed within the global
  distribution of each alignment statistic. Their E1 pairs and comparisons with
  the rule-based comparison origins are reported as well. Examples are chosen
  for the robustness of the pattern, not for narrative appeal.
* **E5 — Contemporaneous design.** Reported separately and labelled as
  non-lagged.

## 6. Robustness checks (all pre-specified)

| ID | Change |
|---|---|
| R1 | Fractional instead of full counting |
| R2 | Drop works with more than 20 distinct countries (exact, using per-k counts) |
| R3 | `dist` instead of `distw`; `comlang_ethno` instead of `comlang_off` |
| R4 | Drop destinations whose UN DESA data are citizenship-based or imputed |
| R5 | Country jackknife: re-estimate M1–M3 dropping each country in turn; report the range of γ and δ and the most influential countries |
| R6 | Scopus-derived instead of OpenAlex-derived mobility (if bilateral flows are released) |
| R7 | Stricter universe: population ≥ 5 million |
| R8 | Inter-author pairs only: for focus origins, work-level data exclude pairs created only by a single multi-affiliated author |
| R9 | `ln M` with a zero indicator instead of `ln(1+M)` |
| R10 | Earlier and later designs |
| R11 | Negative binomial GLM instead of PPML |

## 7. Decision rules for the premise

The working title claims that general migration is a poor guide to where a
country's research connections are, and that scholarly mobility is not
interchangeable with general migration. In advance we define:

* **Contradicts the premise:** H1 holds with strong residual alignment (median
  `ρ_o` ≥ 0.5); migration improves out-of-fold deviance by ≥ 5% over M1; and
  mobility adds nothing beyond migration (δ CI includes 0, or the CV gain of
  M3 over M2 is < 1%).
* **Supports a divergence reading:** median residual `ρ_o` < 0.3; migration's
  CV gain over M1 is < 5%; and mobility's CV gain over M2 is positive with a CI
  excluding 0.
* **Anything in between** is reported as partial alignment, with the specific
  pattern described rather than forced into a binary.

The 0.3, 0.5, 1% and 5% thresholds are interpretive conventions we chose
before seeing the data. They are not statistical tests.

## 8. Multiple testing and reporting

* BH correction is applied across origins (H1 per-origin tests) and across
  pairs (E1). The confirmatory tests H1–H4 are reported without family-wise
  adjustment, but all four are always reported together.
* Every number in the report must come from a file in `outputs/tables` or
  `outputs/models` that the pipeline generates.
* Results that weaken or reverse under R1–R11 are reported in the main text.

## 9. Known threats recorded in advance

* **Measurement dependence.** Mobility and co-authorship both derive from
  bibliographic affiliations, and mobility in the primary analysis comes from
  OpenAlex. A multi-affiliated author can generate both a "move" and a
  "collaboration". Mitigations: the lag between windows, R6 and R8.
* **Coverage bias.** OpenAlex affiliation completeness varies by country,
  field and language. We report the share of works without country information
  by year.
* **Migrant stock definitions.** UN DESA mixes birthplace- and
  citizenship-based destination data, and refugee additions. Corridors absent
  from the workbook are treated as zero but flagged as "unreported".
* **Undirected outcome.** Directional claims (H4b) concern which side of a
  pair a move started from. They say nothing about direction of knowledge flow.

---

## Amendment v1.1 (2026-11-05, still before any data were acquired)

**What changed.** The inference for H1. The statistic `ρ_o` is unchanged.

**Why.** A simulation check of the v1.0 procedure (`tests/test_alignment.py::test_size_artefact_is_removed_by_simulation_null`)
showed that the registered destination-permutation test is anti-conservative for this
statistic. The two layers were simulated with **no** shared pair affinity.
- With the `+1` pseudo-count, a zero cell's residual is `−ln(1+E)`, which falls with
  destination size in both layers.
- So `ρ_o` is positive even without shared structure: the median `ρ_o` was 0.24 in that
  simulation.
- Permuting destination labels destroys this size structure, so 45% of origins were
  "significant" at p < 0.05.

**New primary inference for H1.**
- Null: collaboration counts for origin o are drawn from a negative binomial around the
  independence expectation, `NB2(E^C_od, α̂)`, with the migration profile held fixed.
  `α̂` is the dispersion of the observed collaboration layer around `E^C`, estimated by
  maximum likelihood.
- This null keeps each destination's size in both layers. It reproduces the zero-cell
  artefact and treats the collaboration layer's own pair structure as independent of
  migration.
- The statistic is `ρ_excess,o = ρ_o − mean(ρ_null,o)`.
- Per-origin p-values come from 2,000 null draws, with BH adjustment across origins.
- Summary test: Wilcoxon signed-rank of `ρ_excess,o` across eligible origins against 0.
- In the same simulation the new null gives a median `ρ_excess` of 0.01 and 0% of
  origins with q < 0.05. With genuinely shared affinity it still detects alignment: every
  origin in the detection test has `ρ_excess` > 0.2.

**Unchanged.**
- The decision thresholds in §7 now apply to the median `ρ_excess` instead of the median
  `ρ_o`. Both values are always reported, together with the permutation p-values,
  labelled "not size-calibrated".
- A rank-partial version of `ρ_o`, controlling for `ln E^M` and `ln E^C`, is reported as
  a sensitivity statistic.
