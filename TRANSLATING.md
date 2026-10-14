# Translating

English is the source language. Every translation is a language-tagged literal next to its English
text, in the ontology file itself. So `https://w3id.org/membership` and the other IRIs return every
language in one file:

```turtle
mbr:Branch a owl:Class ;
    rdfs:label "Branch"@en , "Avdelning"@sv , "Zweigstelle"@de ;
    skos:definition "A part of a membership organisation."@en ,
                    "En del av en medlemsorganisation."@sv ,
                    "Ein nachgeordneter Teil einer Mitgliederorganisation."@de .
```

## Adding a language

1. Register the language in `LANGUAGE_NAMES` in `tools/i18n.py`: its [BCP 47](https://www.rfc-editor.org/info/bcp47)
   code (`de`, `pt-BR`) and the name it calls itself. The check rejects every other code, which
   catches typos: Swedish is `sv`, and `se` is Northern Sami.
2. List what is left to translate: `pipx run --backend pip --spec 'pylode==3.2.1' python tools/i18n.py missing de membership/membership-ontology.ttl`
   prints each term, property and English text that has no `@de` yet. Do the same for the other
   ontology and codelist files you want to cover.
3. Add the translations beside the English text, tagged `@de`. A partial translation is fine: a
   term without one is shown in English in the documentation.
4. Run `make i18n`. It must say `i18n OK`.
5. Run `make docs`. It writes the documentation in your language to `docs/<ontology>/<language>/`.
   Then add the language to both rows of `index.html`, with the same markup as the others: the
   link to the page, and the Library of Congress IRI of the language (`http://id.loc.gov/vocabulary/iso639-1/<code>`)
   in `dcterms:language`.
6. Open a pull request. Say who translated it and whether a native speaker has reviewed it, and
   mark machine translations so they are not mistaken for reviewed ones. A translator who agrees
   can be credited as `dcterms:contributor` in the ontology header (none is yet; the README says
   which languages a native speaker has reviewed).

By contributing you license your translation under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
like the ontologies.

## What `make i18n` checks

- Every language tag is well formed and registered.
- Every term that has text in another language also has English text for the same property, which
  is the fallback.
- A SKOS concept has one `skos:prefLabel` per language (`make skos`).

`tests/i18n/` has a valid example and invalid ones for the first two points (a malformed tag, an
unregistered language, text with no English). The third point is checked by `make skos`.

## Validation messages

The `sh:message` texts in the `*-shapes.ttl` files are not language-tagged. Each is one plain string with
the languages in a fixed order, English first, separated by ` | `:

```turtle
sh:message "The end date is before the start date. | Slutdatumet ligger före startdatumet. | La date de fin est antérieure à la date de début. | Das Enddatum liegt vor dem Startdatum. | La data di fine è anteriore alla data di inizio. | La fecha de fin es anterior a la fecha de inicio. | A data de fim é anterior à data de início. | A záró dátum korábbi a kezdő dátumnál. | Η ημερομηνία λήξης είναι πριν από την ημερομηνία έναρξης. | De einddatum ligt vóór de begindatum."
```

The order is English, Swedish, French, German, Italian, Spanish, Portuguese, Hungarian, Greek, Dutch.

Tagged messages (`"…"@en , "…"@sv`) would be cleaner, but Apache Jena's `shacl` rejects more than one
`sh:message` on a shape ("More than one match"), and `make shacl` uses it. A new language therefore adds
` | <text>` at the end of each message, keeping `{?placeholders}` as they are. `make i18n` does not check
these files.

## Documentation per language

pyLODE cannot show more than one language at a time: it runs a term's titles together
("Membership OrganisationMedlemsorganisation"). `tools/i18n.py` therefore gives it one language at
a time, with English text wherever a term has no translation, and adds a language switcher:
English at `docs/<ontology>/`, the others at `docs/<ontology>/<language>/`.

**Anchors.** pyLODE builds the anchor of a term from its label, with spaces and every non-ASCII
character removed. Then `https://w3id.org/membership#MembershipOrganization` missed the English page
(`#MembershipOrganisation`) and the German one (`#Mitgliederorganisation`), and a label in Greek
or Hungarian would lose most of its letters. `tools/pylode_anchors.py` runs pyLODE with the
anchor taken from the IRI instead, so the anchor is the same on every page and in every language.
This holds only if the local name of a term is plain ASCII, which is the rule for all IRIs here
(a Greek term gets an English local name). `make docs` ends with `tools/i18n.py anchors`, which
fails if a term has no element with its local name as id, if a term id is repeated, or if a link
to `#name` has no target.
