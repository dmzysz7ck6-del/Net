# OpenAlex API (late 2026): documentation review, blocked

## Access status: read this first

**I could not read any current OpenAlex documentation, so nothing below is verified for late 2026.**

- **WebSearch:** the first call came back "budget used up (200 calls per turn, shared by all agents)".
- **WebFetch:** `docs.openalex.org` and `developers.openalex.org` both failed with `ENOTFOUND`. The tool says this means the host is outside the session's allowed network domains, or does not exist. Its instructions say to stop trying other hosts after that, so I did not try `help.openalex.org`, the blog or GitHub pages.
- **GitHub MCP:** `ourresearch/openalex-docs` was refused. This session only allows `dmzysz7ck6-del/net`.
- **The API itself:** `api.openalex.org` is also blocked at the container's egress, per `/home/user/Net/migration-knowledge/research/progress.md`.

So every item below is my background knowledge, with a training cutoff of June 2026, plus a confidence level and a check you can run at no cost. **No source URL is given, because I saw none.** Nothing here should be cited in the paper until it is checked.

**To unblock:** allow `docs.openalex.org`, `developers.openalex.org`, `help.openalex.org`, `api.openalex.org` and `openalex.s3.amazonaws.com` (the free snapshot) in the session's network settings. Or send a follow-up message, so the search budget resets, and re-run this step.

## Facts (all UNVERIFIED; confidence H/M/L)

### 1. Authentication, limits and cost
- **F1 (H for the past, L for now).** From 2022 to 2024 no key was needed. Limits were 100,000 calls per day and 10 requests per second. Adding `mailto=` or an email in the User-Agent put you in the "polite pool".
- **F2 (L on details).** In 2025–26 OpenAlex moved to API keys and usage-based pricing. Different request types cost different amounts: single-record lookups, list/filter, search, and full-text downloads. There is a free daily allowance and paid usage above it. I don't reliably remember:
  - whether a key is now mandatory;
  - the size of the free allowance;
  - whether a `group_by` call costs the same as a list call.
- **F3 (M).** A paid "Premium" tier for higher limits existed earlier.
- **Check / zero-cost rule:**
  - Read the authentication and rate-limit page.
  - Send one call with `api_key` and one without, and compare the response headers (any rate-limit or credit headers) and the `meta` block.
  - Never add a payment method to the account.
  - Make the client stop on HTTP 402 or 429 instead of retrying.

### 2. Works fields
- **`authorships[].countries` (M).** A list of ISO-2 codes per author. It comes from the matched institutions. My recollection is that it is also filled from raw affiliation strings when no institution could be matched.
- **`authorships[].institutions[].country_code` (H).** The country of the matched (ROR-linked) institution.
- **`authorships[].raw_affiliation_strings` and `authorships[].affiliations[]` (M-H).** The raw strings, plus the institution IDs each string was matched to.
- **`countries_distinct_count` and `institutions_distinct_count` (H that they exist; L-M on how they are computed).** Distinct countries or institutions across all authorships. It is unclear whether the country count is built from `authorships.countries` or only from institution country codes. This matters for the k-bin method below.
- **`type` (M-H).** Values since 2023:
  - article, book-chapter, dataset, preprint, dissertation, book, review, paratext, libguides, letter;
  - other, reference-entry, report, editorial, peer-review, erratum, standard, grant, supplementary-material, retraction.

  OpenAlex assigns review, paratext, letter, editorial and erratum with its own rules. `type_crossref` keeps the Crossref type, such as journal-article.
- **`primary_location.source.type` (M).** journal, repository, conference, ebook platform, book series, metadata, other.
- **Other fields (M-H).** `is_retracted` and `is_paratext` are booleans and `publication_year` is an integer. `has_fulltext` means OpenAlex holds the full text; it says nothing about affiliations. `indexed_in` lists sources such as crossref, pubmed, doaj and arxiv.
- **Walden, the 2025 rewrite (L).** I recall it reprocessed works and added a large batch of non-Crossref records. I believe they are flagged `is_xpac` and excluded by default. Type assignment and affiliation matching may also have changed.
  - **Check:** run `group_by=type` and `group_by=countries_distinct_count` for a fixed filter, compare against older figures, and record the data date in provenance.

### 3. Filter syntax
- **Basics (H).**
  - A comma means AND across filters.
  - `|` means OR within one filter, e.g. `authorships.countries:KE|UG`. There is a cap on the number of OR values; I recall 50, confidence L.
  - A leading `!` negates, e.g. `type:!paratext`.
  - `>` and `<` work on numbers, e.g. `countries_distinct_count:>1`.
  - A hyphen gives a range, e.g. `publication_year:2015-2019`.
  - `+` may mean AND within one filter (L-M).
- **Repeating a filter (M-H).** `authorships.countries:KE,authorships.countries:US` returns works that include both KE and US. This was documented for `institutions.country_code`.
  - **Check:** its count should equal the US bucket of `group_by=authorships.countries` run under the filter `authorships.countries:KE`.
- **Ranges on the country count (M).** `countries_distinct_count:>1,countries_distinct_count:<5` should give works with 2 to 4 countries.

### 4. group_by
- **Format (H).** The request is `group_by=<field>`. The response has a `group_by` list of `{key, key_display_name, count}` entries and `meta.groups_count`.
- **Groupable fields (M / L-M).** `authorships.countries` can be grouped (M). Whether `countries_distinct_count` can be is L-M, and the existing code assumes it can.
- **Number of groups (M / L-M).** Historically at most 200 groups per page (M). Cursor paging for `group_by`, via `meta.next_cursor`, is L-M. There are only about 250 countries, so this means at most 2 pages.
- **Unknown group (L-M).** Works with no value can appear under the key `unknown`. A suffix such as `:include_unknown` may control this.
- **Exact or approximate counts (L).** I'm not sure whether the counts are exact. The backend is Elasticsearch, whose grouped counts can be approximate. The sum checks below will show whether they are.

### 5. Paging
- **(H)** `per_page` runs from 1 to 200 (default 25).
- **(H)** `page=N` only reaches the first 10,000 results. For anything deeper, use `cursor=*` and follow `meta.next_cursor` until it is null.
- **(M)** `select=` takes top-level fields only, with no nested selection. I believe it can't be combined with `group_by` (L).

### 6. Data-quality caveats
These are leads to confirm. The papers are named from memory: DOIs are null and none are verified.
- **Missing institutions or affiliations.** Many authorships have no institution, especially for older works and some publishers. Those works get k = 0 or too small a k. Lead: Zhang et al., *Scientometrics* 2024, "Missing institutions in OpenAlex…".
- **Country derived from affiliation strings can be wrong.** Likely confusions: Niger vs Nigeria, Guinea vs Guinea-Bissau vs Equatorial Guinea, the two Congos, and the US state of Georgia vs the country.
- **Document types differ from WoS and Scopus.** Some editorial items are labelled article, and reviews are detected differently. Lead: Haupka et al., arXiv 2024.
- **Wider coverage.** OpenAlex covers more Global South and non-English journals than WoS or Scopus. Leads: Alperin et al., arXiv 2024; Céspedes et al., *JASIST* 2025. One consequence: African output will look larger in OpenAlex than in the Scopus-based Akbaritabar et al. mobility data, which will distort the layer comparison.
- **Counts change over time.** Monthly updates and the Walden reprocessing shift numbers. Record the date of every extraction.
- **Mega-collaborations.** Papers with 20+ countries inflate full counts. Fractional counting and the existing threshold of 20 (`mega_country_threshold`) address this.

## Recommended query strategy

**Base filter F:** `type:article,primary_location.source.type:journal,is_retracted:false,is_paratext:false,publication_year:Y1-Y2`. This matches `config/pipeline.yaml`. As a sensitivity check, also run with `type_crossref:journal-article` and with reviews included.

**(c) Article output per country-year.** One call per year covers every country: `group_by=authorships.countries` with F and `publication_year:y`. Also run `group_by=countries_distinct_count` per year to track the share of works with no country (k = 0 or unknown). This is about 1–2 calls per year, instead of one per country.

**(a) and (b) for a focal country X and window w:**
1. Run `group_by=countries_distinct_count` with F and `authorships.countries:X`. This gives N_k(X), the number of X's works with exactly k countries.
2. For each k ≥ 2 with N_k > 0 and k ≤ K* (about 25), run `group_by=authorships.countries` with F, `authorships.countries:X` and `countries_distinct_count:k`. This gives n_k(X,Y) for every partner Y. Drop Y = X.
3. For the tail (k > K*), either run per-k calls only for the k values that actually occur, or download those works once per window for all countries together. For the download, use cursor paging with `select=id,countries_distinct_count,authorships` and compute the weights exactly.
4. Full count: full(X,Y) = Σ_k n_k(X,Y).
5. Fractional count: frac(X,Y) = Σ_k n_k(X,Y) · 2/(k(k−1)). Each work then carries a total weight of 1 across its pairs.

**Cost.** Each (X, window) needs about 1 + (number of k values present) calls. For roughly 200 focal countries, 3 windows and about 20 k values on average, that is about 12,000 calls; year by year it is about 60,000. The gravity models need every dyad, so every country has to be queried as X. If F2 turns out to make that many calls cost money, use the free S3 snapshot instead. It allows exact local computation, including the R8 inter-author variant; its terms are also unverified.

**Free consistency checks (no extra calls):**
- **Sum check.** Σ_Y n_k(X,Y), including Y = X, should equal k·N_k(X). If it doesn't, one of three things is true:
  - the counts are approximate;
  - groups were cut off;
  - `countries_distinct_count` is built from a different country source than `authorships.countries`.
- **Symmetry.** X's query and Y's query should give the same n_k(X,Y). `aggregate_k_table` already checks this.
- **Totals.** Σ_k N_k(X) plus the unknown or k = 0 group should equal the plain count for F with `authorships.countries:X`.
- **Spot check.** For about 20 pairs, the count for `authorships.countries:X,authorships.countries:Y,countries_distinct_count:>1` should equal full(X,Y).

**Problems in the existing code (`/home/user/Net/migration-knowledge/src/acquisition/openalex.py`):**
- `int(str(g["key"]).rsplit("/",1)[-1])` will crash if the API returns an `unknown` key. This affects `country_k_table`, `country_output` and `coverage`.
- `group_by()` should assert that `len(groups) == meta.groups_count`. Otherwise it can silently keep only the first 200 groups if cursor paging isn't supported for `group_by`.
- `cleaning/openalex.py::work_countries` sets k from the union of `authorships.countries` and `institutions[].country_code`. The API's k bins may use a different definition, so the work-level validation should compute k both ways.

**Next step:** once the hosts are allowed, re-run this step to replace the confidence labels with cited facts. Everything in Facts 1–5, and the existence of each paper in 6, can be checked from the documentation pages or with one or two zero-cost API calls each.