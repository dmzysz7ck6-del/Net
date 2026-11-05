# Akbaritabar, Theile & Zagheni (2024): released data report

**Status: blocked. None of the five questions could be checked against a source in this run, so every field below is unverified.**

## Access problems

- **The article could not be fetched.** WebFetch failed on `https://pmc.ncbi.nlm.nih.gov/articles/PMC11269605/` and on `https://www.nature.com/articles/s41597-024-03655-9`, with the error `getaddrinfo ENOTFOUND`. Both hosts are outside this session's allowed network domains.
- **I did not try further sites.** After two hosts failed, the tool said to stop trying more. So `zenodo.org`, `api.crossref.org` and the MPIDR/Scholarly Migration Database pages were not attempted. `research/progress.md` already records that `zenodo.org`, `www.nature.com`, `api.crossref.org` and `doi.org` are blocked at the container proxy (HTTP 403).
- **Web search was used up.** WebSearch returned "Web search was not performed: this turn's web search budget is used up". The limit is 200 searches per turn, shared by all agents. No searches ran.
- **To finish this task:** either allow `pmc.ncbi.nlm.nih.gov`, `www.nature.com`, `zenodo.org` and `api.crossref.org` in the session's network settings, or re-run this step in a follow-up turn with a fresh search budget. Alternatively, raise `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION`.

## 1. Repository record, versions, license, files

- **Not verified.** The Zenodo DOI 10.5281/zenodo.11145735 is unconfirmed. It comes only from the user and is hard-coded in `/home/user/Net/migration-knowledge/config/pipeline.yaml` (`zenodo_record: "11145735"`, `zenodo_api: https://zenodo.org/api/records/11145735`).
- License, version list and file inventory are unknown. That includes file names, formats and sizes, and the split between OpenAlex and Scopus files and between country-level and bilateral files.
- Once the network is open, `https://zenodo.org/api/records/11145735` returns all of this as JSON: `metadata.version`, `metadata.license`, `files[].key/size/checksum`, and the `versions` link. `/home/user/Net/migration-knowledge/src/acquisition/scholarly.py` already records licence, version and checksums from that endpoint at download time.

## 2. Columns of the bilateral flow files

- **Not verified.** It is unknown whether country codes are ISO2 or ISO3, and the names of the year, count and rate columns are unknown. It is also unknown whether small counts are padded or suppressed.
- The project's parser, `/home/user/Net/migration-knowledge/src/cleaning/scholarly.py`, does not depend on these answers. It finds columns by regex and infers the code scheme (ISO2, ISO3, M49 or names) from the values, and it fails loudly if anything is ambiguous. Confirm its regex lists against the real headers when the files arrive.

## 3. How a "move" is inferred

- **Not verified.** The parser's docstring states, citing "the source article", that a move is a change in a scholar's modal country of affiliation between publications. It also points to `research/methodology.md` (Dataset B) for confirmation, but that file does not exist in the repo. Until someone reads the Methods section, treat the docstring as unconfirmed.
- Points to confirm from the Methods section:
  - whether the modal country is computed per year
  - how ties and multiple affiliations are handled
  - the minimum number of publications or active years required
  - which year a move is assigned to
  - whether the first publication defines academic origin, and whether that counts as a move
  - whether return moves are included
  - whether the counts are persons or moves
  - what denominator the rates use

## 4. Stated limitations, validation, caveats

- **Not verified.** I read nothing on coverage biases (language, field, Global South, OpenAlex vs Scopus). I also have no Scopus–OpenAlex correlation figures or authors' advice on low counts and small countries.
- These matter most for the focus origins: Somalia, Rwanda, Uganda and other small Sub-Saharan producers. Pull them from the Technical Validation and Usage Notes sections of the article.

## 5. Later version (for example SMD v2, 1998–2024)

- **Not verified.** I did not determine whether a newer release exists. Check the "versions" list on the Zenodo record and the MPIDR / Scholarly Migration Database site. I have no confirmed URL for that site.

Nothing was cited because no source was successfully read.