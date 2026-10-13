# Releasing

The order matters: each published step depends on the one before it.

1. **Finish the release on a branch.**
   - Version: `owl:versionInfo`, `owl:versionIRI`, `owl:priorVersion` and `owl:backwardCompatibleWith` in every ontology and codelist file (the external declarations too), and `owl:versionInfo` in the shapes.
   - The version also stands in the first-line comment of the six `.ttl` files in `membership/` and `fraternal/` ("— v1.1.0"), in `index.html` (the Version column, two cells, each also the link to the version IRI `https://w3id.org/<ontology>/<version>`), in the "Status: version" line of the README and in `version:` of CITATION.cff. Find every place with `grep -rn '<old version>' . --exclude-dir=versions --exclude-dir=docs --exclude-dir=.git`.
   - Set `dcterms:modified` to the date of the last change.
   - Mappings: set `mapping_set_version` and `mapping_date` in the header of every `mappings/*.sssom.tsv` that changed since the last release, then `make mappings`. The mapping sets are served from `mappings/generated/` by their unversioned IRIs, so `make freeze` does not copy them.
   - CITATION.cff: set `version` and `date-released`.
   - README changelog: turn the "Unreleased" blocks into the version and date, and say what is stricter, what is looser and what changed in a term that was already released.
2. **Check:**
   - `make all dl reason reuse` (`all` includes the competency questions, which must equal `tests/cq/expected/`)
   - if the mappings changed: `make mappings wikidata-check`
   - compare with the last release: no subject or codelist triple removed, no shape made stricter without a changelog line (`git diff v<old version> -- membership fraternal external`)
   - `make docs`, and commit the regenerated HTML
3. **Freeze:** `make freeze` copies the release files to `versions/<version>/`. Commit the copy. A released version is never changed afterwards.
4. **Publish:** merge to `main`, then push `main` and an annotated tag `v<version>`. GitHub Pages deploys within a minute.
   - The w3id rules send every version IRI (`https://w3id.org/membership/<version>`, `…/code/<version>`, `…/external/<version>`, `…/shapes/<version>`) to `versions/<version>/`. A release therefore needs no w3id pull request.
5. **Archive:** publish a GitHub Release from the tag. Zenodo's GitHub integration archives it and mints a version DOI under the concept DOI [10.5281/zenodo.23080656](https://doi.org/10.5281/zenodo.23080656).
   - Check the Zenodo record: it takes title, authors, ORCID, licenses and keywords from CITATION.cff.
   - Submit the new version to [Linked Open Vocabularies](https://lov.linkeddata.es/) (only 1.1.0 has been sent so far).
6. **Verify:**
   - the current IRI and the new version IRI return Turtle;
   - the previous version IRI still returns the previous version;
   - the HTML docs show the new version;
   - the DOI resolves.

Release notes, commit messages and PR descriptions may credit Claude, but must not contain links into private sessions or accounts.
