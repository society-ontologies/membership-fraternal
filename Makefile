# Membership Organisations ontology (mbr:) <- Fraternal Orders and Sororities ontology (fraternal:)
# Needs Apache Jena (riot, shacl, sparql) and python3 on PATH; `dl` and
# `reason` also need ROBOT; `reuse` needs pipx.

SHELL := /bin/bash
BUILD := build

ONT := external/external-declarations.ttl \
       membership/membership-ontology.ttl membership/membership-codes.ttl \
       fraternal/fraternal-ontology.ttl fraternal/fraternal-codes.ttl
SHAPES := membership/membership-shapes.ttl fraternal/fraternal-shapes.ttl
MAPPINGS_TSV := $(wildcard mappings/*.sssom.tsv)
MAPPINGS_TTL := $(patsubst mappings/%.sssom.tsv,mappings/generated/%.ttl,$(MAPPINGS_TSV))
VALID := tests/data/klubb-exempel.ttl tests/data/systerskap-exempel.ttl
INVALID := $(wildcard tests/data/invalid/*.ttl)

.PHONY: all validate shacl shacl-invalid skos cq mappings wikidata-check dl reason reuse docs clean

all: validate shacl shacl-invalid skos cq

$(BUILD):
	mkdir -p $@

# --- Syntax ---------------------------------------------------------------

validate:
	@for f in $(ONT) $(SHAPES) $(MAPPINGS_TTL) tests/data/*.ttl $(INVALID); do \
	  riot --validate "$$f" || { echo "syntax error in $$f"; exit 1; }; \
	done; echo "syntax OK"

# --- Merged graphs ---------------------------------------------------------

$(BUILD)/shapes.nt: $(SHAPES) | $(BUILD)
	riot --output=nt $(SHAPES) > $@

$(BUILD)/stack.nt: $(ONT) | $(BUILD)
	riot --output=nt $(ONT) > $@

$(BUILD)/mappings.nt: $(MAPPINGS_TTL) | $(BUILD)
	riot --output=nt $(MAPPINGS_TTL) > $@

# Everything the competency questions run over: stack, mappings, all samples.
$(BUILD)/cq-dataset.nt: $(BUILD)/stack.nt $(BUILD)/mappings.nt $(VALID) tests/data/linkset-exempel.ttl
	riot --output=nt $^ > $@

$(BUILD)/skos-dataset.nt: $(BUILD)/stack.nt $(BUILD)/mappings.nt
	riot --output=nt $^ > $@

# --- SHACL -----------------------------------------------------------------

# Valid samples must produce no validation results (not even warnings).
shacl: $(BUILD)/shapes.nt $(BUILD)/stack.nt
	@for d in $(VALID); do \
	  riot --output=nt $(BUILD)/stack.nt "$$d" > $(BUILD)/data.nt; \
	  shacl validate --shapes=$(BUILD)/shapes.nt --data=$(BUILD)/data.nt > $(BUILD)/report.ttl; \
	  if grep -q 'sh:conforms *true' $(BUILD)/report.ttl; then echo "PASS  $$d"; \
	  else echo "FAIL  $$d"; cat $(BUILD)/report.ttl; exit 1; fi; \
	done

# Each invalid fixture must produce at least one sh:Violation.
shacl-invalid: $(BUILD)/shapes.nt $(BUILD)/stack.nt
	@for d in $(INVALID); do \
	  riot --output=nt $(BUILD)/stack.nt "$$d" > $(BUILD)/data.nt; \
	  shacl validate --shapes=$(BUILD)/shapes.nt --data=$(BUILD)/data.nt > $(BUILD)/report.ttl; \
	  n=$$(grep -c 'sh:Violation' $(BUILD)/report.ttl); \
	  if [ "$$n" -gt 0 ]; then echo "PASS  $$d  ($$n violation(s))"; \
	  else echo "FAIL  $$d  (expected violations, got none)"; exit 1; fi; \
	done

# --- SKOS quality checks (each query must return no rows) -------------------

skos: $(BUILD)/skos-dataset.nt
	@for q in tests/skos-checks/*.rq; do \
	  n=$$(sparql --data=$(BUILD)/skos-dataset.nt --query="$$q" --results=csv | tail -n +2 | grep -c .); \
	  if [ "$$n" -eq 0 ]; then echo "PASS  $$q"; \
	  else echo "FAIL  $$q ($$n rows)"; sparql --data=$(BUILD)/skos-dataset.nt --query="$$q"; exit 1; fi; \
	done

# --- Competency questions -------------------------------------------------

cq: $(BUILD)/cq-dataset.nt
	@for q in tests/cq/*.rq; do \
	  echo "== $$q"; sparql --data=$(BUILD)/cq-dataset.nt --query="$$q"; \
	done

# --- Mappings (SSSOM TSV -> RDF) --------------------------------------------

mappings: $(MAPPINGS_TTL)

# Stand-in for sssom-py (`sssom convert`).
mappings/generated/%.ttl: mappings/%.sssom.tsv mappings/sssom2ttl.py
	python3 mappings/sssom2ttl.py "$<" "$@"

# --- Wikidata link check ---------------------------------------------------

wikidata-check:
	python3 tests/check_wikidata.py $(ONT) $(MAPPINGS_TSV)

# --- OWL 2 DL profile and reasoning (ROBOT) ----------------------------------

# The catalog resolves owl:imports to the local files.
dl: | $(BUILD)
	robot --catalog catalog-v001.xml validate-profile --profile DL \
	      --input fraternal/fraternal-codes.ttl --output $(BUILD)/dl-report.txt

# Consistency + no unsatisfiable classes (robot reason fails otherwise), then the
# expected / forbidden inferences in tests/reasoning/ (robot verify fails on any row).
reason: | $(BUILD)
	robot --catalog catalog-v001.xml \
	  merge --input fraternal/fraternal-codes.ttl $(foreach d,$(VALID),--input $(d)) \
	  query --update tests/reasoning/00-ta-bort-datum.ru \
	  reason --reasoner HermiT --axiom-generators "ClassAssertion" --include-indirect true \
	  --output $(BUILD)/reasoned.ttl
	robot verify --input $(BUILD)/reasoned.ttl --queries tests/reasoning/*.rq --output-dir $(BUILD)

# --- Licensing (REUSE.toml + LICENSES/) --------------------------------------

reuse:
	pipx run --backend pip --spec 'reuse[charset-normalizer]' reuse lint

# --- HTML documentation for GitHub Pages (pyLODE, pinned: 3.3.x breaks on import) ---

PYLODE := pipx run --backend pip --spec 'pylode==3.2.1' pylode

docs:
	mkdir -p docs/membership docs/fraternal
	$(PYLODE) membership/membership-ontology.ttl -o docs/membership/index.html
	$(PYLODE) fraternal/fraternal-ontology.ttl -o docs/fraternal/index.html

clean:
	rm -rf $(BUILD)
