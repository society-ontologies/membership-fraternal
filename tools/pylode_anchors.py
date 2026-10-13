#!/usr/bin/env python3
"""pyLODE with anchors that are the local names of the IRIs.

pyLODE 3.2.1 makes the HTML id of a term from its label, with spaces and every non-ASCII
character removed. A term's IRI is https://w3id.org/membership#MembershipOrganization, so
the link .../membership#MembershipOrganization should land on id="MembershipOrganization",
but the English page had id="MembershipOrganisation" (the British label), and the German
one id="Mitgliederorganisation". A label in Greek or Hungarian would lose most or all of
its letters. The IRI is the stable thing, so the id is taken from it.

This runs pyLODE's own command line with its fragment-id function replaced. It takes the
same arguments as `python -m pylode`. `tools/i18n.py docs` runs it; `tools/i18n.py anchors`
checks the result.
"""
import pylode.utils as utils

_original = utils.generate_fid


def generate_fid(title_, iri, fids):
    """The local name of the IRI (after '#', else the last path segment), if it is a plain
    name that no other term has; otherwise pyLODE's own choice."""
    if iri is None:
        return _original(title_, iri, fids)
    s_iri = str(iri)
    if s_iri in fids:
        return fids[s_iri]
    name = s_iri.rsplit("#", 1)[-1] if "#" in s_iri else s_iri.rstrip("/").rsplit("/", 1)[-1]
    if name and name.isascii() and name.isidentifier() and name not in fids.values():
        fids[s_iri] = name
        return name
    return _original(title_, iri, fids)


utils.generate_fid = generate_fid

from pylode.cli import main  # noqa: E402  (after the patch, so it uses the patched function)

if __name__ == "__main__":
    main()
