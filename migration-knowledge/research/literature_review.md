# Literature review

**Scope and method.** This is a targeted review of six literatures:
1. scientific diasporas and migrant scientists' networks;
2. migration and knowledge diffusion beyond co-authorship;
3. bibliometric scholarly mobility;
4. international co-authorship networks and gravity models, with an African focus;
5. multilayer network comparison and null models;
6. estimation methods.

On 2026-11-05 five search agents each covered one topic using web search. Each returned
structured records with title, authors, venue, DOI, research question, data, methods and
findings. A second set of agents then tried to re-verify every DOI and claimed finding
independently.

**Verification status. Read before citing.**
- The container's network policy blocks `api.crossref.org`, `doi.org` and the publisher
  sites, so DOIs could not be resolved directly.
- The session's web-search budget (200 calls per turn) ran out during the
  independent-verification pass.
- Each entry in the bibliography therefore carries one of three labels:

| Label | Meaning | Count |
|---|---|---|
| **V2** | DOI–title match confirmed independently by a second agent from a source it read | 5 |
| **V1** | DOI–title match seen in search results by the compiling agent (one pass, not re-checked) | 63 |
| **U** | No DOI found, or DOI not confirmed (working papers, arXiv, grey literature) | 9 |

`make verify-refs` checks every DOI against Crossref (title similarity, year, first author)
as soon as `api.crossref.org` is reachable. It upgrades or flags entries in
`research/references_verified.json`. **Most findings below are abstract-level summaries.**
None of the 77 works was read in full text in this session. The machine-readable record,
including where each claim came from, is in `research/references.json`. The raw agent
outputs are in `research/lit_raw/`.

---

## 1. What is already established

### 1.1 Mobility and co-authorship are associated at the country-pair level. This is not new.
- **Appelt et al. (2015, OECD STI WP)** model bilateral scientist mobility from
  Scopus affiliation changes in a gravity framework. Prior collaboration is one of the
  strongest correlates of mobility, alongside geographic, economic and scientific
  distance, visa restrictions, and student flows in the opposite direction.
- **Kato & Ando (2017, *Scientometrics*)** use *Nature*/*Science* papers. They report
  that researcher migration helps explain international collaboration, with the
  relationship running from mobility to collaboration. They also point out a mechanical
  problem that matters directly here. When a researcher moves from A to B, an earlier
  A–B collaboration becomes domestic, and a new tie to A becomes international.
- **Moed, Aisati & Plume (2013)** find that language similarity matters more for
  migration than for co-authorship. This is an early indication that the two layers
  have different determinants.

Any finding of the form "migration or mobility is positively associated with
collaboration" restates known results. It cannot be the contribution.

### 1.2 Mobility and collaboration networks differ, more so for low-capacity countries
- **Chinchilla-Rodríguez, Miao et al. (2018, *Frontiers in Research Metrics and
  Analytics*)** compare global mobility and collaboration networks (WoS, 2008–2015)
  across national-capacity tiers.
  - Mobility is everywhere smaller than collaboration.
  - The two are related mainly in prolific countries.
  - Country positions are inconsistent across the two networks, especially for
    lower-income countries.
- **Pei et al. (2024, *Scientometrics*)** report closer alignment between mobility and
  collaboration for advanced than for lagging countries (Scopus).
- **El Ouahi, Robinson-García & Costas (2021, *QSS*)** find different hubs in the two
  layers for the Middle East and North Africa: Saudi Arabia leads in mobility and
  Turkey in collaboration.
- **Chinchilla-Rodríguez, Bu et al. (2018, *Scientometrics*)** is the closest
  methodological precedent for our per-origin comparison.
  - It covers the 2017 US travel-ban countries, including **Somalia**.
  - It computes size-adjusted affinity and asymmetry indexes separately for
    collaboration and for mobility, and flags mismatches between them.
  - It notes that the probabilistic affinity index is very sensitive to country size.

So "the scholarly-mobility layer and the collaboration layer diverge, especially for
low-capacity countries" has published support. For mobility versus collaboration, our
H2 is a replication with different data, not a discovery.

### 1.3 Migrant and returnee scientists connect origin and destination (individual level)
- **Scellato, Franzoni & Stephan (2015, *Research Policy*)** use the GlobSci survey
  across 16 countries.
  - Foreign-born scientists collaborate internationally more than natives.
  - Many of them collaborate with their country of origin.
  - Network benefits are larger for migrants from stronger science systems.
- Return migrants carry ties home:
  - **Jonkers & Cruz-Castro (2013)** for Argentina.
  - **Fry (2023, *Organization Science*)** for US-trained African HIV/AIDS researchers.
    Non-migrant colleagues at receiving African institutions publish more after a
    returnee arrives, especially those without prior links to top institutions.
  - **Fry (2025)** for female scientists from developing countries trained in other
    developing countries. Brokerage depends on gender parity and institutional support.
- **Ito et al. (2025, *J. Development Economics*)** reconstruct the mobility paths and
  co-authorship of Colombian scientists. Mobile scientists connect non-mobile
  colleagues to foreign co-authors, but these ties are short-lived without the
  mobile intermediary.
- **Freeman & Huang (2015)** document ethnic homophily in US co-authorship.

These are the micro-level mechanisms behind a "diaspora" link in co-authorship. They
concern *scientists*, not migrant populations in general.

### 1.4 Diaspora and knowledge diffusion in patents and trade
- Diasporas carry knowledge:
  - **Agrawal, Cockburn & McHale (2006)**: co-ethnic and former-location ties shape
    patent citations.
  - **Kerr (2008, *REStat*)**: ethnic scientific communities in the US speed
    technology diffusion to home countries.
- That knowledge is not automatically a gain for the origin:
  - **Agrawal et al. (2011)**: emigration of innovators is on average harmful to
    knowledge access in India, but diaspora-channelled knowledge is valuable for
    the most important inventions.
  - **Breschi, Lissoni & Miguélez (2017)**: no brain gain for India despite a
    diaspora effect.
- **Miguélez (2018, *WBER*)** is the closest econometric template. It estimates
  gravity models of international co-patenting on inventor-diaspora stocks and finds
  robust positive associations.
- **Miguélez & Noumedem Temgoua (2020, *Research Policy*)** show the effect runs
  mostly toward home countries, and mainly for developing origins.
- **Bahar & Rapoport (2018)** link migration to comparative advantage in new
  products. **Parsons & Vézina (2018)** give quasi-experimental evidence on migrant
  networks and trade. **Docquier & Rapoport (2012)** review brain drain and
  development.
- The "scientific diaspora" and "brain circulation" concepts come from **Meyer & Brown
  (1999)**, **Meyer (2001)** and **Saxenian (2005)**.

### 1.5 Migration as one layer among economic networks
Complex-network studies compare bilateral migration stocks with trade and FDI:
- **Fagiolo & Mastrorillo (2014, *PLoS ONE*)**;
- **Sgrignoli et al. (2015, *Physica A*)**;
- **Garas, Lapatinas & Poulios (2016)**.

They find strong correlation between layers, largely explained by country size and
distance, plus a residual positive association. The lesson for us: a raw correlation
between migration and any bilateral flow is mostly the gravity structure. Any claim
about alignment must be judged **after** that structure is removed.

### 1.6 African research collaboration
African co-authorship is dominated by extra-African partners, often former colonial
powers and the US. Intra-African ties are comparatively weak.
- **Tijssen (2007)**: Africa's research output and partners.
- **Boshoff (2009)**: in Central Africa about 80% of papers involve a partner outside
  the region and about 35% a former colonial power.
- **Onyancha & Maluleka (2011)**: collaborative research in Sub-Saharan Africa.
- **Mêgnigbêto (2013)**: West Africa.
- **Adams et al. (2014)**: collaboration clusters explained by history, culture and
  language more than geography.
- **Pouris & Ho (2014)**: research emphasis and collaboration in Africa.

African *migration*, in contrast, is largely intra-regional, including refugee
populations in neighbouring countries. Combined, these two literatures imply that
migration and collaboration profiles diverge for many Sub-Saharan origins. As far as
our search found, nobody has measured that divergence jointly.

### 1.7 Data and methods
- **OpenAlex.** It covers non-Western and African publications more broadly than
  Scopus or WoS, but has weaker affiliation metadata (**Alperin et al. 2024**;
  **Alonso-Álvarez et al. 2024**).
- **The scholarly-migration database (Akbaritabar, Theile & Zagheni 2024,
  *Scientific Data*).** It releases country-level and bilateral flows from Scopus and
  OpenAlex, 1998–2020. The two sources agree best for Western countries, and flow
  magnitudes differ between them.
- **Estimation and inference:**
  - PPML: **Santos Silva & Tenreyro 2006**; **Correia, Guimarães & Zylkin 2020**;
    **Head & Mayer 2014**.
  - Dyadic-robust inference: **Aronow, Samii & Assenova 2015**; **Cameron, Gelbach &
    Miller 2011**.
- **Network tools:**
  - Multilayer comparison: **Kivelä et al. 2014**; **Battiston, Nicosia & Latora 2014**
    (edge overlap); **De Domenico et al. 2015** (layer reducibility via Jensen–Shannon
    distances).
  - Null models and backbones: **Squartini & Garlaschelli 2011**; **Mastrandrea et al.
    2014**; **Serrano, Boguñá & Vespignani 2009** (disparity filter).
  - Gravity residuals and topology: **Fagiolo 2010**; **Dueñas & Fagiolo 2013**;
    **Almog, Squartini & Garlaschelli 2015**.
- **Migration data background:** **Özden et al. (2011)** on bilateral stocks;
  **Abel & Cohen (2019)** on why stocks are not flows.

## 2. What remains unresolved

1. **General migration versus scholarly mobility.** We found no study that asks, in
   one country-pair model, whether *general-population* migrant stocks (UN DESA)
   carry information about co-authorship beyond geography, language, colonial ties
   and country fixed effects, and beyond bibliometric scholarly mobility.
   - **Gui, Liu & Du (2019)** add international-student flows in a QAP model.
   - **Miguélez (2018)** uses *inventor* diasporas for patents.
   - The mobility–collaboration studies in §1.2 never include general migration.
2. **Per-origin distributional alignment with size-preserving nulls.** Affinity
   indexes (§1.2) compare layers pair by pair. We found no study that compares an
   origin's whole migrant-destination distribution with its whole
   collaboration-partner distribution, using rank correlation, top-k overlap and
   Jensen–Shannon divergence, against a strength-preserving null.
3. **Sub-Saharan Africa and the Horn.** The African-collaboration literature (§1.6)
   and migration statistics separately imply divergence. The size, robustness and
   persistence of that divergence for specific origins (Somalia, Ethiopia, Kenya,
   Ghana and others), relative to comparable non-African origins, are unmeasured.
4. **Measurement dependence.** Bibliometric mobility and co-authorship come from the
   same affiliation records. Kato & Ando's mechanical-reclassification point has not,
   to our knowledge, been handled with time-lagged layers, a second bibliographic
   source and an inter-author robustness check together.
5. **Temporal stability.** How alignment between migration and collaboration changed
   across 2010, 2015 and 2020 within one revision of the UN data is undocumented.

## 3. What this project could plausibly contribute

Each item below is conditional on the results surviving the pre-registered tests and
robustness checks. None is claimed in advance.

- **A null-calibrated mismatch measure.** Per-origin alignment between where emigrants
  live and where co-authors are, after removing each destination's overall size in
  both layers (H1). This extends §1.2 from *scholarly* mobility to the *general*
  diaspora, and from pairwise affinity to full distributions.
- **A joint test of three layers.** Does general migration add predictive information
  beyond gravity structure? Does scholarly mobility add information beyond general
  migration? (H3, H4.) Both are judged out of sample, not only by coefficient
  significance.
- **An interpretable list of unexpectedly strong and weak pairs.** Pairs with
  credible deviations from structure plus migration (E1), with explicit uncertainty
  and multiple-testing control.
- **Evidence specific to Sub-Saharan origins** set against rule-based non-African
  comparators (E4).

**What would *not* be a contribution:**
- a positive migrant-stock coefficient on its own (§1.1, §1.4, §1.5);
- divergence between scholarly mobility and collaboration on its own (§1.2);
- "African collaboration is extra-African" (§1.6).

**Novelty caveat.** The search was a single, budget-limited pass, and the independent
verification pass was cut short. We cannot rule out unpublished or non-indexed work
along the lines of §3. Before any novelty claim is published, the search should be
repeated with full Crossref and Semantic Scholar access. The specific queries are:
- "migrant stock" AND "co-authorship" AND gravity;
- "diaspora" AND "international collaboration" AND "Jensen-Shannon";
- "UN DESA" AND bibliometric.

## 4. Annotated bibliography

The full annotated bibliography, generated from `research/references.json`, is in
`research/bibliography.md`. It lists each work's research question, data, methods,
findings, DOI or URL, and verification label.
