#!/usr/bin/env python3
"""Translations inside the ontology files: checks, a to-do list, and one HTML page per language.

English is the source language. Every translation is a language-tagged literal next to its
English text in the ontology file itself ("Zweigstelle"@de beside "Branch"@en), so each
file holds everything a reader of its IRI needs. See TRANSLATING.md.

  check    Language tags are well formed and registered in LANGUAGE_NAMES below, and every
           translated term also has English text for the same property (the fallback).
  missing  List the English text of every term that has no text in a language yet, for a
           translator to work through.
  docs     Write the pyLODE documentation of one ontology once per language: the English
           page at OUTDIR/index.html, the others at OUTDIR/<language>/index.html, each with
           a language switcher. A term without a translation shows its English text. The
           anchor of a term is the local name of its IRI (tools/pylode_anchors.py).
  anchors  Check the pages `docs` wrote: every term has an element with the local name of its
           IRI as id, no term id is repeated, every link to #name has a target.

Needs rdflib and pyLODE, so run it with the pyLODE environment (see `make docs`, `make i18n`).

Usage: python3 tools/i18n.py check FILE.ttl [FILE.ttl ...]
       python3 tools/i18n.py missing LANGUAGE FILE.ttl [FILE.ttl ...]
       python3 tools/i18n.py docs ONTOLOGY.ttl OUTDIR
       python3 tools/i18n.py anchors ONTOLOGY.ttl OUTDIR
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from rdflib import RDF, BNode, Graph, Literal
from rdflib.namespace import DCTERMS, OWL, RDFS, SKOS

# The languages the ontologies are written in, with the name shown in the language switcher.
# Adding a language means adding it here, which also catches a mistyped code: "se" is
# Northern Sami, Swedish is "sv".
LANGUAGE_NAMES = {"en": "English", "sv": "Svenska", "de": "Deutsch", "fr": "Français",
                  "es": "Español", "it": "Italiano", "nl": "Nederlands", "da": "Dansk",
                  "nb": "Norsk bokmål", "fi": "Suomi", "pl": "Polski", "pt": "Português", "la": "Latina",
                  "hu": "Magyar"}

# Well-formed BCP 47 tag, as written in Turtle: "de", "pt-BR", "zh-Hans".
LANGUAGE_TAG = re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$")

# Properties whose English text every translated term must also have.
TEXT_PROPERTIES = (RDFS.label, RDFS.comment, SKOS.prefLabel, SKOS.definition,
                   DCTERMS.title, DCTERMS.description)

# What a translator is asked to translate (`missing`).
TRANSLATED_PROPERTIES = (RDFS.label, SKOS.prefLabel, SKOS.definition, SKOS.scopeNote, SKOS.note,
                         RDFS.comment, DCTERMS.title, DCTERMS.description)


def parse(files):
    graph = Graph()
    for file in files:
        graph.parse(file)
    return graph


def primary(tag):
    return tag.split("-")[0].lower()


def tagged(graph, s, p):
    return [o for o in graph.objects(s, p) if isinstance(o, Literal) and o.language]


def check(files):
    problems = []
    for file in files:
        graph = parse([file])
        for s, p, o in graph:
            if not (isinstance(o, Literal) and o.language):
                continue
            if not LANGUAGE_TAG.match(o.language):
                problems.append(f"{file}: <{s}> <{p}>: malformed language tag @{o.language}")
            elif primary(o.language) not in LANGUAGE_NAMES:
                problems.append(f"{file}: <{s}> <{p}>: language @{o.language} is not registered "
                                "in LANGUAGE_NAMES (tools/i18n.py)")
        for p in TEXT_PROPERTIES:
            for s in set(graph.subjects(p)):
                values = tagged(graph, s, p)
                if values and not any(primary(o.language) == "en" for o in values):
                    problems.append(f"{file}: <{s}> <{p}>: translated but no English text")
    return problems


def missing(language, files):
    """Print `term<TAB>property<TAB>English text` for each English text without one in `language`."""
    count = 0
    for file in files:
        graph = parse([file])
        print(f"# {file}")
        for s in dict.fromkeys(graph.subjects(RDF.type, None)):
            for p in TRANSLATED_PROPERTIES:
                values = tagged(graph, s, p)
                english = [o for o in values if primary(o.language) == "en"]
                if english and not any(primary(o.language) == language for o in values):
                    for o in english:
                        print(f"{graph.namespace_manager.normalizeUri(s)}\t"
                              f"{graph.namespace_manager.normalizeUri(p)}\t{o}")
                        count += 1
    print(f"# {count} texts without @{language}")


def languages(graph):
    found = {primary(o.language) for o in graph.objects(None, RDFS.label)
             if isinstance(o, Literal) and o.language}
    return ["en"] + sorted(found - {"en"})


def in_language(graph, language):
    """The triples of the graph, in its order, with one language: for each (subject,
    property), the text in `language`, else the English text, else all of it. Untagged
    literals are kept. The order matters: pyLODE lists the terms in the order it reads them."""
    groups = {}
    for s, p, o in graph:
        if isinstance(o, Literal) and o.language:
            groups.setdefault((s, p), []).append(o)
    keep = set()
    for (s, p), values in groups.items():
        for wanted in (language, "en"):
            chosen = [o for o in values if primary(o.language) == wanted]
            if chosen:
                break
        else:
            chosen = values
        keep.update((s, p, o) for o in chosen)
    for s, p, o in graph:
        if not (isinstance(o, Literal) and o.language) or (s, p, o) in keep:
            yield s, p, o


def write_ntriples(graph, triples, path):
    """Write the triples grouped by subject, the typed subjects first in the order the
    ontology file lists them (the order pyLODE shows the terms in), then any others."""
    by_subject = {}
    for s, p, o in triples:
        by_subject.setdefault(s, []).append((p, o))
    typed = dict.fromkeys(graph.subjects(RDF.type, None))
    order = [s for s in typed if s in by_subject] + [s for s in by_subject if s not in typed]
    # rdflib gives blank nodes a new random identifier at every parse, and pyLODE's output
    # depends on them, so number them in the order they are written.
    blank = {}

    def term(t):
        if isinstance(t, BNode):
            return "_:b" + str(blank.setdefault(t, len(blank)))
        return t.n3()

    with open(path, "w", encoding="utf-8") as f:
        for s in order:
            for p, o in by_subject[s]:
                f.write(f"{term(s)} {term(p)} {term(o)} .\n")


def switcher(language, available):
    """The language links, relative to the page of `language`."""
    down = "" if language == "en" else "../"
    links = []
    for target in available:
        name = LANGUAGE_NAMES.get(target, target)
        if target == language:
            links.append(f'<strong lang="{target}">{name}</strong>')
        else:
            href = (down or "./") if target == "en" else f"{down}{target}/"
            links.append(f'<a lang="{target}" href="{href}">{name}</a>')
    return f'<p class="languages" style="margin:0 0 1em">{" · ".join(links)}</p>'


def docs(ontology, outdir):
    ontology, outdir = Path(ontology), Path(outdir)
    graph = parse([ontology])
    available = languages(graph)
    with tempfile.TemporaryDirectory() as tmp:
        for language in available:
            page = outdir / ("index.html" if language == "en" else f"{language}/index.html")
            page.parent.mkdir(parents=True, exist_ok=True)
            source = Path(tmp) / f"{ontology.stem}-{language}.nt"
            write_ntriples(graph, in_language(graph, language), source)
            # pylode_anchors.py is `python -m pylode` with the anchors taken from the IRIs
            subprocess.run([sys.executable, str(Path(__file__).with_name("pylode_anchors.py")),
                            str(source), "-o", str(page)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            html = page.read_text(encoding="utf-8")
            html = html.replace("</h1>", "</h1>\n" + switcher(language, available), 1)
            html = html.replace("<html>", f'<html lang="{language}">', 1)
            page.write_text(html, encoding="utf-8")
            print(f"{page}: {LANGUAGE_NAMES.get(language, language)}")


def anchors(ontology, outdir):
    """Check the anchors of the pages `docs` wrote: every term of the ontology has an element
    with its IRI's local name as id, so that https://w3id.org/membership#Term lands on the
    term; no term id occurs more often than pyLODE lists the term; every link to #name points
    to an id on the page. Returns the pages, the terms and the problems."""
    graph = parse([ontology])
    namespaces = [str(s) + "#" for s in graph.subjects(RDF.type, OWL.Ontology)]
    kinds = (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty,
             OWL.NamedIndividual)
    # pyLODE lists a property once with its kind and once more under each characteristic
    # (functional, symmetric ...), so such a term legitimately occurs more than once.
    characteristics = (OWL.FunctionalProperty, OWL.InverseFunctionalProperty, OWL.SymmetricProperty,
                       OWL.AsymmetricProperty, OWL.TransitiveProperty, OWL.ReflexiveProperty,
                       OWL.IrreflexiveProperty)
    allowed = {}
    for kind in kinds:
        for s in graph.subjects(RDF.type, kind):
            for ns in namespaces:
                if str(s).startswith(ns) and len(str(s)) > len(ns):
                    allowed[str(s)[len(ns):]] = 1 + sum((s, RDF.type, c) in graph for c in characteristics)
    terms = sorted(allowed)
    outdir = Path(outdir)
    pages = [outdir / "index.html"] + sorted(outdir.glob("*/index.html"))
    problems = []
    for page in pages:
        html = page.read_text(encoding="utf-8")
        ids = re.findall(r'\bid="([^"]*)"', html)
        # only the ids of terms: pyLODE's own page furniture (the logo repeats id="Path") is not ours
        for name in terms:
            if ids.count(name) > allowed[name]:
                problems.append(f"{page}: id=\"{name}\" occurs {ids.count(name)} times, at most {allowed[name]} expected")
        for name in terms:
            if name not in ids:
                problems.append(f"{page}: no element with id=\"{name}\" for the term {name}")
        for name in sorted({h for h in re.findall(r'href="#([^"]+)"', html) if h not in ids}):
            problems.append(f"{page}: a link to #{name} has no target")
    return pages, terms, problems


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check").add_argument("files", nargs="+")
    m = commands.add_parser("missing")
    m.add_argument("language")
    m.add_argument("files", nargs="+")
    d = commands.add_parser("docs")
    d.add_argument("ontology")
    d.add_argument("outdir")
    a = commands.add_parser("anchors")
    a.add_argument("ontology")
    a.add_argument("outdir")
    args = parser.parse_args()
    if args.command == "check":
        found = check(args.files)
        print("\n".join(found) if found else "i18n OK")
        sys.exit(1 if found else 0)
    elif args.command == "missing":
        missing(args.language, args.files)
    elif args.command == "anchors":
        pages, terms, found = anchors(args.ontology, args.outdir)
        print("\n".join(found) if found else f"anchors OK: {len(terms)} terms on {len(pages)} pages")
        sys.exit(1 if found else 0)
    else:
        docs(args.ontology, args.outdir)
