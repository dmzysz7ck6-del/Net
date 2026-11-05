# Editorial assessment

**Verdict: DO NOT PUBLISH (no empirical results).**

This verdict does not mean the hypothesis failed. It means no data could be acquired,
so nothing has been tested. The execution environment's network policy blocks every
data host the study needs. As a result:
- no observation from UN DESA, the scholarly migration database, OpenAlex, WDI or
  CEPII has been analysed;
- no research report, essay or findings have been written;
- writing them now would mean inventing results.

What *can* be assessed is the readiness of the design.

## Assessment of the design, by criterion

| Criterion | Assessment | Basis |
|---|---|---|
| Novelty | **Uncertain, positioned narrowly.** The headline association (migration or mobility ↔ collaboration) is established. So is the divergence between *scholarly-mobility* and collaboration networks for low-capacity countries (Chinchilla-Rodríguez et al. 2018a, b; Pei et al. 2024). What remains plausibly new: *general* migrant stocks as a separate layer; null-calibrated per-origin distributional alignment; the joint out-of-sample test of migration and scholarly mobility; the Sub-Saharan focus. The literature search was single-pass and partly unverified, so this positioning is provisional. | `research/literature_review.md` §1–3 |
| Methodological rigour | **Strong on paper.** Hypotheses, decision thresholds and robustness checks were pre-registered before any data were seen. The design uses exact counting rules, size-preserving nulls, PPML with country fixed effects and dyadic-robust inference, out-of-sample comparison, NB predictive tests with parameter uncertainty and false-discovery control, and claim-to-output traceability. None of this has met real data, and real data usually reveal problems a plan does not anticipate. | `research/analysis_plan.md`, `research/methodology.md`, 51 tests |
| Conceptual depth | **Adequate, with one unresolved tension.** The study separates migration, scholarly mobility and co-authorship. It never equates co-authorship with knowledge transfer. But the working title still invites that equation (see below). | — |
| Empirical robustness | **Not assessable.** | — |
| Clarity | **Good for a technical reader.** The methodology and plan are explicit. The general-reader essay does not exist. | — |
| General-reader relevance | **Potentially high, not demonstrated.** The question of whether diasporas are research bridges matters for science and development policy in Sub-Saharan Africa. Relevance depends entirely on results that do not yet exist. | — |

## Weakest inference, and a more defensible rewrite

There is no essay. The weakest inference is in the working title and premise:

> *"The Migration Network Is Not the Knowledge Network."*

This makes two leaps.
1. It treats co-authorship as "the knowledge network", although co-authorship is one
   observable channel of knowledge connectivity.
2. It asserts non-identity before testing. Some divergence between two networks is
   guaranteed, so non-identity is trivially true and therefore uninformative.

A defensible formulation, to be adopted only if H1 and H3/H4 come out as described in
`analysis_plan.md` §7:

> *"Where a country's emigrants live is a weak guide to where its researchers publish
> with foreign partners, once the sheer size of destinations is accounted for; the
> paths of moving scholars are a better guide."*

If the results contradict the premise (§7), the title should be changed to reflect that,
for example *"Diasporas do map onto research partnerships — mostly through geography."*

## What must happen before publication can be considered

1. Allow the data hosts, run `make pilot`, then `make research`.
2. Run `make verify-refs` and repeat the novelty search with full Crossref and Semantic
   Scholar access.
3. Read in full the closest prior work: Chinchilla-Rodríguez et al. 2018a, b; Pei et al.
   2024; Miguélez 2018; Fry 2023. Restate the contribution against them.
4. Complete the adversarial assessment in `analysis_plan.md` §7 and the falsification
   questions on real results. Only then write the report and essay through the
   claim-registry templates, so every number traces to an output.
