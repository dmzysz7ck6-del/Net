# Reproducible entry points. `make research` runs everything end to end.
PY ?= python3
RUN = $(PY) -m src.pipeline

.PHONY: research check-access acquire pilot clean-data analyze figures quality report test verify

research: test check-access acquire clean-data analyze quality figures verify

check-access:          ## test reachability of every data host
	$(RUN) check-access

pilot:                 ## four-origin pilot (SOM, ETH, KEN, GHA), primary window
	$(RUN) acquire --pilot

acquire:               ## download all sources (cached, resumable)
	$(RUN) acquire

clean-data:            ## build the processed data contract
	$(RUN) clean

analyze:               ## all pre-registered analyses, all windows
	$(RUN) analyze

figures:               ## regenerate figures from outputs
	$(RUN) figures

quality:               ## data-quality report
	$(RUN) quality

verify:                ## check that every number quoted in the reports exists in generated outputs
	$(PY) -m src.reporting.verify_claims

test:                  ## unit and plumbing tests (synthetic fixtures only)
	$(PY) -m pytest -q tests

verify-refs:           ## check every DOI in research/references.json against Crossref
	$(PY) -m src.reporting.verify_refs
	$(PY) -m src.reporting.bibliography
