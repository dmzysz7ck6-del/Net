# Data quality report

Generated 2026-11-05T01:46:34+00:00 by `make quality` from the processed data and outputs. Every number below is computed. Nothing is hand-entered.


## 0. Data access

No access check recorded.


## 1. Provenance

No files have been acquired (MANIFEST.jsonl is empty).


## 2. UN DESA migrant stocks

_Not available: data not acquired._


## 3. Scholarly mobility

_Not available: data not acquired._


## 4. OpenAlex co-authorship

_Not available: data not acquired._


## 5. Country universe and exclusions

_Not available: analysis not run._


## 6. Known biases and limitations of the inputs

* **OpenAlex affiliation coverage** varies by country, language and field. Works without any country information
  cannot enter the network, and a work where only some authors have affiliations understates its international ties.
* **Institutional, not personal, geography.** Co-authorship pairs come from institutional affiliations. A single author
  with affiliations in two countries creates a pair; R8 quantifies this for the focus origins.
* **Mega-collaborations** (more than 20 countries; consortia such as Global Burden of Disease or particle-physics
  experiments) can dominate small countries' full counts; R2 removes them exactly.
* **UN DESA stocks** are estimates, mix birthplace- and citizenship-based destination data, add refugees in some
  destinations, and lump many origins into 'Other' for some destinations (Section 2).
* **Scholarly mobility** is inferred from changes in modal affiliation country between publications. It misses
  non-publishing movers, is sensitive to affiliation errors, and is built from the same bibliographic source
  (OpenAlex) as the outcome in the primary analysis.
