#!/usr/bin/env python3
"""Check that every Wikidata item/property referenced in the given files exists.

Finds `wd:Q123` / `wd:P123` CURIEs and full http://www.wikidata.org/entity/ IRIs,
asks the Wikidata API (wbgetentities, 50 ids per request) and reports
  * MISSING  — deleted or never existed (fails the check)
  * REDIRECT — merged into another item (fails the check; update the link)
and prints each target's English label so wrong-but-existing links are easy to spot.

Usage: python3 tests/check_wikidata.py FILE [FILE ...]
"""

import json
import re
import sys
import urllib.parse
import urllib.request

API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "membership-fraternal-ontology-link-check/1.0 (https://w3id.org/membership)"
ID_PATTERN = re.compile(r"(?:\bwd:|http://www\.wikidata\.org/entity/)([QP][0-9]+)\b")


def collect_ids(paths):
    found = {}
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                for match in ID_PATTERN.finditer(line):
                    found.setdefault(match.group(1), []).append(f"{path}:{lineno}")
    return found


def fetch(ids):
    params = urllib.parse.urlencode({
        "action": "wbgetentities",
        "ids": "|".join(ids),
        "props": "labels|info",
        "languages": "en|sv",
        "format": "json",
    })
    request = urllib.request.Request(f"{API}?{params}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def label(entity):
    labels = entity.get("labels", {})
    for lang in ("en", "sv"):
        if lang in labels:
            return labels[lang]["value"]
    return "(no label)"


def main(paths):
    found = collect_ids(paths)
    if not found:
        print("no Wikidata references found")
        return 0

    problems = 0
    ids = sorted(found, key=lambda i: (i[0], int(i[1:])))
    for start in range(0, len(ids), 50):
        batch = ids[start:start + 50]
        entities = fetch(batch).get("entities", {})
        # Redirected ids come back under the target id, with a "redirects" note.
        redirected = {e["redirects"]["from"]: e for e in entities.values() if "redirects" in e}
        for wid in batch:
            where = found[wid][0] + (f" (+{len(found[wid]) - 1} more)" if len(found[wid]) > 1 else "")
            if wid in redirected:
                target = redirected[wid]
                print(f"REDIRECT {wid} -> {target['id']} {label(target)!r}  at {where}")
                problems += 1
            elif "missing" in entities.get(wid, {"missing": ""}):
                print(f"MISSING  {wid}  at {where}")
                problems += 1
            else:
                print(f"ok       {wid} {label(entities[wid])!r}")

    print(f"\n{len(ids)} Wikidata ids checked, {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
