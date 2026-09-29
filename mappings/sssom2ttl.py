#!/usr/bin/env python3
"""Convert an SSSOM/TSV mapping set to Turtle, using only the standard library.

Each mapping row becomes
  * the plain triple  <subject> <predicate> <object> .   (what SPARQL queries use)
  * an owl:Axiom that annotates that triple with its SSSOM metadata
    (mapping_justification, confidence, comment, …), the same shape sssom-py
    produces for OWL output.

Stand-in for `sssom convert` from sssom-py; either can generate mappings/generated/.

Usage: python3 mappings/sssom2ttl.py INPUT.sssom.tsv OUTPUT.ttl
"""

import csv
import sys
from pathlib import Path

SSSOM = "https://w3id.org/sssom/"
FIXED_PREFIXES = {
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dcterms": "http://purl.org/dc/terms/",
    "sssom": SSSOM,
    "semapv": "https://w3id.org/semapv/vocab/",
}
# Row columns carried over as annotations on the mapping axiom.
IRI_COLUMNS = ("mapping_justification", "author_id", "mapping_tool_id")
LITERAL_COLUMNS = ("subject_label", "object_label", "comment", "mapping_date")


def parse(path):
    """Return (metadata dict, curie_map dict, list of row dicts)."""
    meta, curie_map, header_lines, body = {}, {}, [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            (header_lines if line.startswith("#") else body).append(line)

    in_curie_map = False
    for raw in header_lines:
        # "# key: value" -> "key: value";  "#   prefix: iri" keeps its indentation.
        line = raw[1:].rstrip("\n")
        if line.startswith(" "):
            line = line[1:]
        if not line.strip():
            continue
        if line.startswith((" ", "\t")) and in_curie_map:
            prefix, _, iri = line.strip().partition(":")
            curie_map[prefix.strip()] = iri.strip()
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip().strip('"')
        in_curie_map = key == "curie_map"
        if not in_curie_map:
            meta[key] = value

    rows = list(csv.DictReader(body, delimiter="\t"))
    return meta, curie_map, rows


def expand(curie, prefixes):
    if curie.startswith(("http://", "https://")):
        return curie
    prefix, sep, local = curie.partition(":")
    if not sep or prefix not in prefixes:
        raise ValueError(f"cannot expand {curie!r}: unknown prefix {prefix!r}")
    return prefixes[prefix] + local


def iri(value):
    return f"<{value}>"


def literal(value, datatype=None):
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"' + (f"^^<{datatype}>" if datatype else "")


def convert(src, dst):
    meta, curie_map, rows = parse(src)
    prefixes = {**curie_map, **FIXED_PREFIXES}
    set_id = meta.get("mapping_set_id")
    if not set_id:
        raise ValueError("mapping_set_id is required in the SSSOM header")

    out = [
        f"# Generated from {Path(src).name} by mappings/sssom2ttl.py — do not edit by hand.",
        "",
        f"{iri(set_id)} a <http://www.w3.org/2002/07/owl#Ontology>",
    ]
    set_props = []
    if "mapping_set_version" in meta:
        set_props.append(f"<http://www.w3.org/2002/07/owl#versionInfo> {literal(meta['mapping_set_version'])}")
    if "license" in meta:
        set_props.append(f"<http://purl.org/dc/terms/license> {iri(meta['license'])}")
    if "mapping_set_description" in meta:
        set_props.append(f"<http://purl.org/dc/terms/description> {literal(meta['mapping_set_description'])}")
    if "mapping_date" in meta:
        set_props.append(f"<http://purl.org/dc/terms/created> {literal(meta['mapping_date'])}")
    out[-1] += "".join(f" ;\n    {p}" for p in set_props) + " ."
    out.append("")

    # Declarations keep the output OWL 2 DL when loaded with the ontologies.
    used_predicates = sorted({expand(r["predicate_id"], prefixes) for r in rows})
    for p in used_predicates:
        if p.startswith(FIXED_PREFIXES["skos"]):
            out.append(f"{iri(p)} a <http://www.w3.org/2002/07/owl#AnnotationProperty> .")
    for col in (*IRI_COLUMNS, "confidence", *LITERAL_COLUMNS):
        out.append(f"<{SSSOM}{col}> a <http://www.w3.org/2002/07/owl#AnnotationProperty> .")
    out.append("")

    for n, row in enumerate(rows, start=2):
        try:
            s = expand(row["subject_id"], prefixes)
            p = expand(row["predicate_id"], prefixes)
            o = expand(row["object_id"], prefixes)
        except (KeyError, ValueError) as e:
            raise ValueError(f"{src}, line {n}: {e}") from e
        if not row.get("mapping_justification"):
            raise ValueError(f"{src}, line {n}: mapping_justification is required")

        out.append(f"{iri(s)} {iri(p)} {iri(o)} .")
        ann = [
            "a <http://www.w3.org/2002/07/owl#Axiom>",
            f"<http://www.w3.org/2002/07/owl#annotatedSource> {iri(s)}",
            f"<http://www.w3.org/2002/07/owl#annotatedProperty> {iri(p)}",
            f"<http://www.w3.org/2002/07/owl#annotatedTarget> {iri(o)}",
        ]
        for col in IRI_COLUMNS:
            if row.get(col):
                ann.append(f"<{SSSOM}{col}> {iri(expand(row[col], prefixes))}")
        if row.get("confidence"):
            ann.append(f"<{SSSOM}confidence> {literal(row['confidence'], FIXED_PREFIXES['xsd'] + 'double')}")
        for col in LITERAL_COLUMNS:
            if row.get(col):
                ann.append(f"<{SSSOM}{col}> {literal(row[col])}")
        out.append("[ " + " ;\n  ".join(ann) + " ] .")
        out.append("")

    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{src}: {len(rows)} mappings -> {dst}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    try:
        convert(sys.argv[1], sys.argv[2])
    except ValueError as e:
        sys.exit(f"error: {e}")
