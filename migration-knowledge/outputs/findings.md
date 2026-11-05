# Executive findings

**There are no empirical findings yet.**

The study could not acquire any of its data. The execution environment's network policy
blocks HTTPS to OpenAlex, UN DESA, Zenodo, the World Bank, CEPII and Crossref. Nothing
below is a result.

## What has been established without data

1. **The premise is only partly novel.** This is a literature finding, not an empirical
   one.
   - Country-pair associations between mobility and co-authorship are established
     (Appelt et al. 2015; Kato & Ando 2017).
   - So is the divergence between scholarly-mobility and collaboration networks, larger
     for low-capacity countries (Chinchilla-Rodríguez et al. 2018a, b; Pei et al. 2024).
   - The study can add something only by:
     - using *general* migrant stocks as a separate layer;
     - testing alignment against size-preserving nulls;
     - testing migration and scholarly mobility jointly out of sample.
2. **Decision rules are fixed in advance.** `research/analysis_plan.md` §7 states which
   results would support the premise, which would contradict it, and which would count
   as partial alignment.

## What the analysis, once run, still cannot establish

- **Causal effects of migration or mobility on collaboration.** All models are
  conditional associations. Lags order the measurements in time but do not remove
  common causes.
- **Knowledge transfer as such.** Co-authorship is one observable channel.
- **The nationality or birthplace of co-authors.** Affiliations are institutional.

## Which findings could be differentiated from prior work

The following would be new, and only if they survive the robustness checks:
- per-origin size-adjusted alignment between diaspora and co-authorship distributions;
- the incremental out-of-sample value of general migration versus scholarly mobility;
- the specific pattern for Sub-Saharan and Horn of Africa origins.
