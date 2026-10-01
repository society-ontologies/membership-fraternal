# Releasing

The order matters: each published step depends on the one before it.

1. **Finish the release on a branch.**
   - Version: `owl:versionInfo`, `owl:versionIRI`, `owl:priorVersion` and `owl:backwardCompatibleWith` in every ontology and codelist file, and `owl:versionInfo` in the shapes.
   - Set `dcterms:modified` to the date of the last change.
   - CITATION.cff: set `version` and `date-released`.
   - README changelog: turn "Unreleased" into the version and date.
2. **Check:**
   - `make all dl reason reuse`
   - if the mappings changed: `make mappings wikidata-check`
   - `make docs`, and commit the regenerated HTML
3. **Freeze:** `make freeze` copies the release files to `versions/<version>/`. Commit the copy. A released version is never changed afterwards.
4. **Publish:** merge to `main`, then push `main` and an annotated tag `v<version>`. GitHub Pages deploys within a minute.
   - The w3id rules send every version IRI (`https://w3id.org/membership/<version>`, `…/code/<version>`, `…/external/<version>`, `…/shapes/<version>`) to `versions/<version>/`. A release therefore needs no w3id pull request.
5. **Archive:** publish a GitHub Release from the tag. Zenodo's GitHub integration archives it and mints a version DOI under the concept DOI [10.5281/zenodo.23080656](https://doi.org/10.5281/zenodo.23080656).
   - Check the Zenodo record: it takes title, authors, ORCID, licenses and keywords from CITATION.cff.
6. **Verify:**
   - the current IRI and the new version IRI return Turtle;
   - the previous version IRI still returns the previous version;
   - the HTML docs show the new version;
   - the DOI resolves.

Release notes, commit messages and PR descriptions may credit Claude, but must not contain links into private sessions or accounts.
