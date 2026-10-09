#!/usr/bin/env python3
"""Separate the multilingual titles that pyLODE runs together.

pyLODE 3.2.1 (and current upstream) sets the heading of a class or property from
the whole list of its titles, so a term labelled "Membership Organisation"@en and
"Medlemsorganisation"@sv gets the heading "Membership OrganisationMedlemsorganisation":
the titles are joined without a separator, in the h1, every h3, the table of contents
and the links between terms. The element ids use only the first title, so they are
not affected.

This reads the labels from the ontology and replaces each such run-together string in
the generated HTML with the titles joined by " / " (English first, then the other
languages). It does nothing if pyLODE has been fixed and no string is found.

Needs rdflib, so run it with the pyLODE environment (see `make docs`).

Usage: python3 tools/fix_pylode_titles.py ONTOLOGY.ttl DOCS.html
"""
import html
import sys
from itertools import permutations

from rdflib import Graph, Literal
from rdflib.namespace import DC, DCTERMS, RDFS, SKOS

# The properties pyLODE copies into dcterms:title (profiles/ontpub.py).
TITLE_PROPERTIES = (DC.title, DCTERMS.title, RDFS.label, SKOS.prefLabel)


def multilingual_titles(graph):
    """Yield, for every subject with more than one title, its titles in display order."""
    titles = {}
    for prop in TITLE_PROPERTIES:
        for subject, value in graph.subject_objects(prop):
            if isinstance(value, Literal):
                titles.setdefault(subject, set()).add(value)
    for values in titles.values():
        if len(values) > 1:
            # English first, then the other languages alphabetically.
            yield [str(v) for v in sorted(values, key=lambda v: (v.language != "en", v.language or "", str(v)))]


def replacements(graph):
    """Map each run-together string, in any order pyLODE may have used, to the fixed title."""
    found = {}
    for ordered in multilingual_titles(graph):
        fixed = " / ".join(ordered)
        for perm in permutations(ordered):
            found["".join(perm)] = fixed
    return found


def main(ontology, html_file):
    graph = Graph().parse(ontology)
    with open(html_file, encoding="utf-8") as f:
        text = f.read()
    count = 0
    # Longest first, so that a string is never replaced inside a longer one.
    for joined, fixed in sorted(replacements(graph).items(), key=lambda kv: -len(kv[0])):
        # The HTML has the text as pyLODE wrote it: escaped or not.
        for quote in (False, True):
            old, new = html.escape(joined, quote=quote), html.escape(fixed, quote=quote)
            count += text.count(old)
            text = text.replace(old, new)
        count += text.count(joined)
        text = text.replace(joined, fixed)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"{html_file}: separated {count} run-together titles")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
