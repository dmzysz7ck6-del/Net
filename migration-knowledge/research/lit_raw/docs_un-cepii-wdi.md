# Dataset documentation report (A: UN DESA IMS 2024, B: CEPII GeoDist, C: WDI API v2)

**I could not confirm anything in this report from a live source.** Every item below is marked UNVERIFIED. They come from my memory of earlier releases or from assumptions already in the repo, and they are meant as a checklist to verify, not as citable facts.

**Why nothing could be checked:**
- **Web search:** the first search returned "Web search was not performed: this turn's web search budget is used up (limit: 200 WebSearch calls per turn, shared by every agent in it)". No results came back, so no URLs are cited as sources. The user can send a follow-up message to get a new budget, or raise `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION`.
- **Page fetching:** fetches to `https://www.un.org/development/desa/pd/content/international-migrant-stock` and `https://api.worldbank.org/v2/country/KEN?format=json` both failed with `getaddrinfo ENOTFOUND`. The tool said to stop trying more hosts after two failures, so I did not try `www.cepii.fr` or `api.crossref.org`.
- **Network settings:** `www.un.org`, `api.worldbank.org`, `www.cepii.fr` and `api.crossref.org` have to be allowed in the session's network settings. `/home/user/Net/migration-knowledge/research/progress.md` already records that the container proxy blocks these hosts.
- **Bash:** I did not use it for internet access, as instructed.

The candidate URLs below were not opened in this session.

## A) UN DESA International Migrant Stock 2024 — all UNVERIFIED

- **Landing page (from the task):** https://www.un.org/development/desa/pd/content/international-migrant-stock (unreachable).
- **File name and URL (as in the repo config):** `https://www.un.org/development/desa/pd/sites/www.un.org.development.desa.pd/files/undesa_pd_2024_ims_stock_by_sex_destination_and_origin.xlsx`. This follows the 2020 file's naming (`undesa_pd_2020_ims_stock_by_sex_destination_and_origin.xlsx`).
- **Release:** "International Migrant Stock 2024", which I recall came out around January 2025. Not confirmed.
- **Sheets:** in the 2020 workbook I recall `Contents`, `Table 1`, `Annex` and `Notes`. The 2024 names need checking.
- **Header row:** I recall about row 10–11 in the 2020 file. The repo parser finds the header by its content, so the exact position matters less.
- **Column order (2020 pattern; 2024 should add a 2024 column):**
  - Index
  - Region, development group, country or area of destination
  - Notes of destination
  - Location code of destination
  - Type of data of destination
  - Region, development group, country or area of origin
  - Location code of origin
  - Year columns 1990, 1995, …, 2020[, 2024], repeated for Both sexes, Male and Female, under a merged sex header.
- **"Type of data" codes (as I recall from 2020):**
  - B = foreign-born population
  - C = foreign citizens
  - R = refugees (UNHCR/UNRWA) added to the estimate
  - I = imputed (no data)
  - Combinations appear, such as "B R" and "C R".
- **Location codes:** countries use UN M49 numeric codes, all below 900 (the highest country code, Zambia, is 894). Region and income aggregates use Population Division codes, not the standard M49 region codes:
  - 900 World, 901/902 more/less developed, 941 least developed
  - 903 Africa, 947 Sub-Saharan Africa (standard M49 uses 202)
  - Sub-regions in the 9xx range (e.g. 910 Eastern Africa)
  - 55xx for Central and Southern Asia
  - 15xx for World Bank income groups
  - 18xx for SDG regions, if present
  - **Rule to verify:** country if code < 900. Exceptions to handle: 830 Channel Islands (an aggregate area), 158 Taiwan, and Serbia, which may include Kosovo.
- **"Other" / unknown origins:** I believe they appear as residual "Other" rows with their own code, which I recall as ≥ 2000 but have not confirmed. The repo's `destination_coverage()` measures this residual as the World total minus the country rows.
- **License:** the repo assumes the UN terms of use (https://www.un.org/en/about-us/terms-of-use). From memory, the 2020 IMS and WPP workbooks say "Copyright © United Nations, CC BY 3.0 IGO", so the 2024 cover sheet should be checked.

## B) CEPII GeoDist (Mayer & Zignago 2011) — all UNVERIFIED

- **Reference:** Mayer & Zignago (2011), "Notes on CEPII's distances measures: The GeoDist database", CEPII Working Paper 2011-25. I could not confirm a DOI (doi: null, verified: false).
- **Landing page (repo config):** https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=6
- **Files:**
  - Repo assumes `https://www.cepii.fr/distance/dist_cepii.zip` and `https://www.cepii.fr/distance/geo_cepii.zip`.
  - Older direct `.dta`/`.xls` links existed under `/distance/`.
  - CEPII may now require free registration and route downloads through its download page.
- **`dist_cepii` variables, as I recall them:**

| Variable | Meaning |
|---|---|
| `iso_o`, `iso_d` | ISO3 codes of origin and destination |
| `contig` | Shared border |
| `comlang_off` | Common official language |
| `comlang_ethno` | A language spoken by at least 9% of both populations |
| `colony` | Ever in a colonial link |
| `comcol` | Common colonizer after 1945 |
| `curcol` | Currently in a colonial link |
| `col45` | Colonial link after 1945 |
| `smctry` | Were or are the same country |
| `dist` | Distance in km between the most populous cities |
| `distcap` | Distance in km between capitals |
| `distw` | Population-weighted distance, theta = 1 |
| `distwces` | Population-weighted distance, theta = −1 (CES) |

- **`geo_cepii` variables (recalled):** iso2, iso3, cnum, country, area, dis_int, landlocked, continent, lat/lon, official and ethnic language fields, colonizer fields.
- **Coverage:** 225 countries.
- **Non-standard ISO3 codes:** ROM (Romania), ZAR (DR Congo), TMP (Timor-Leste), YUG (Serbia and Montenegro), PAL (Palestine), ANT (Netherlands Antilles). The repo already handles these in `SPECIAL_CASES`. Check whether SCG or other codes also appear.
- **License:** the repo assumes Etalab Open Licence 2.0, which I think CEPII adopted around 2020–21. Not confirmed.
- **Is GeoDist superseded?** My recollection is that GeoDist has not been updated since 2011. The newer CEPII Gravity database (Conte, Cotterlaz & Mayer 2022, CEPII WP 2022-05; about 252 countries, 1948–2020s) is maintained and uses different variable names: `iso3_o`/`iso3_d`, `distw_harmonic`, `distw_arithmetic`, `col_dep_ever`. GeoDist is still widely used for cross-sections. All of this is unconfirmed.

## C) World Bank WDI API v2 — all UNVERIFIED (the API host could not be reached)

- **Bulk endpoint:** `https://api.worldbank.org/v2/country/all/indicator/{CODE}?format=json&date=2010:2020&per_page=20000`. Adding `&source=2` pins the WDI source.
- **Response shape:** a list with metadata first (page, pages, per_page, total, lastupdated), then rows. Each row has indicator{id,value}, country{id,value}, countryiso3code, date, value, obs_status and decimal.
- **Indicators:**

| Measure | Code |
|---|---|
| Population | `SP.POP.TOTL` |
| GDP, current US$ | `NY.GDP.MKTP.CD` |
| GDP, PPP, constant international $ | `NY.GDP.MKTP.PP.KD` |
| GDP per capita, PPP, constant international $ (used in the repo config) | `NY.GDP.PCAP.PP.KD` |
| GDP per capita, PPP, current international $ | `NY.GDP.PCAP.PP.CD` |

  I believe the constant-PPP base year moved to 2021 after the ICP 2021 release. Not confirmed.
- **Country metadata endpoint:** `https://api.worldbank.org/v2/country?format=json&per_page=400`. Fields: id (ISO3), iso2Code, name, region{id,iso2code,value}, adminregion, incomeLevel{id,value}, lendingType, capitalCity, longitude, latitude.
- **Aggregates:** in `/v2/country` they have `region.id == "NA"` and `region.value == "Aggregates"`. `country/all` in the indicator endpoint includes aggregates, so filter them out by joining to that metadata. WB-specific codes include XKX (Kosovo) and CHI (Channel Islands).
- **License:** CC BY 4.0, per the World Bank Data Catalog listing for WDI. Not confirmed.
- **Bulk CSV alternative (recalled):** https://databank.worldbank.org/data/download/WDI_CSV.zip

## Repo assumptions to check once the hosts are reachable

- `/home/user/Net/migration-knowledge/config/pipeline.yaml` holds the unconfirmed UN DESA and CEPII URLs and license strings.
- `/home/user/Net/migration-knowledge/src/cleaning/undesa.py` assumes:
  - the header cell text "location code of destination";
  - sex labels in a merged row above the year columns;
  - a sheet named "Table 1";
  - `..` and `-` mean missing;
  - code 900 is "World".
- `/home/user/Net/migration-knowledge/src/cleaning/countries.py` assumes the CEPII legacy codes and the M49 special cases (830, 158, 736, 530).

**Status: verified = false for every item in A, B and C.**