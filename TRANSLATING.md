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
6. Open a pull request. Say who translated it and whether a native speaker has reviewed it, and
   mark machine translations so they are not mistaken for reviewed ones. Translators are credited
   as `dcterms:contributor` in the ontology header.

By contributing you license your translation under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
like the ontologies.

## What `make i18n` checks

- Every language tag is well formed and registered.
- Every term that has text in another language also has English text for the same property, which
  is the fallback.
- A SKOS concept has one `skos:prefLabel` per language (`make skos`).

`tests/i18n/` has a valid example and one invalid example per check.

## Documentation per language

pyLODE cannot show more than one language at a time: it runs a term's titles together
("Membership OrganisationMedlemsorganisation"). `tools/i18n.py` therefore gives it one language at
a time, with English text wherever a term has no translation, and adds a language switcher:
English at `docs/<ontology>/`, the others at `docs/<ontology>/<language>/`.
