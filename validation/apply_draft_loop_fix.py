#!/usr/bin/env python
"""Restrict seven template reactions to their forward direction, on top of commit 21a8084
(the five-reaction fix), in templates/v7.0/{GramNegModelTemplateV7,GramPosModelTemplateV7,
ArchaeaTemplateV6}.json. Core-V6.json holds none of them and is not rewritten.

  rxn00014            cytochrome c peroxidase
  rxn23850            GAPN, non-phosphorylating glyceraldehyde-3-phosphate dehydrogenase
  rxn05746, rxn08933, rxn08934, rxn08935, rxn08936
                      maltodextrin glucosidases (maltotriose ... maltoheptaose)

Each reaction is edited the way 21a8084 edits a '=' reaction: direction and GapfillDirection
'>', lower_bound 0, maxrevflux 0.0. Nothing else changes (penalties, costs, upper bounds and
max forward fluxes are already those of a forward reaction).

The files are written in the serialization each one already has, so the diff touches only
the edited reactions: GramNeg, GramPos and Core are json.dumps() with default separators on
one line; Archaea is json.dumps(indent=4); none ends in a newline. Before writing, the script
checks that this serialization reproduces the file's current bytes exactly, and stops if it
does not.

    python validation/apply_draft_loop_fix.py            # edit templates/v7.0 in place
    python validation/apply_draft_loop_fix.py --check    # verify only; exit 1 if not applied
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TDIR = os.path.join(os.path.dirname(HERE), "templates", "v7.0")
REACTIONS = ("rxn00014", "rxn23850", "rxn05746", "rxn08933", "rxn08934", "rxn08935",
             "rxn08936")
FILES = ("GramNegModelTemplateV7.json", "GramPosModelTemplateV7.json",
         "ArchaeaTemplateV6.json")
UNTOUCHED = ("Core-V6.json",)
FORWARD = {"direction": ">", "GapfillDirection": ">", "lower_bound": 0, "maxrevflux": 0.0}
SERIALIZATIONS = (("default", {}), ("indent4", {"indent": 4}))


def base_id(rid):
    return rid.rsplit("_", 1)[0]


def detect_format(raw, t):
    for name, kw in SERIALIZATIONS:
        if json.dumps(t, **kw).encode() == raw:
            return name, kw
    raise SystemExit("no known serialization reproduces the current bytes; refusing to write")


def is_forward(r):
    return all(r.get(k) == v and type(r.get(k)) is type(v) for k, v in FORWARD.items())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--templates", default=TDIR, help="templates/v7.0 directory")
    ap.add_argument("--check", action="store_true", help="verify only, write nothing")
    args = ap.parse_args()
    report, ok = {}, True
    for f in FILES + UNTOUCHED:
        path = os.path.join(args.templates, f)
        raw = open(path, "rb").read()
        t = json.loads(raw)
        name, kw = detect_format(raw, t)
        hits = [r for r in t["reactions"] if base_id(r["id"]) in REACTIONS]
        if f in UNTOUCHED:
            if hits:
                raise SystemExit("%s unexpectedly holds %s" % (f, [r["id"] for r in hits]))
            report[f] = {"format": name, "edited": [], "sha256": hashlib.sha256(raw).hexdigest()}
            continue
        found = sorted(base_id(r["id"]) for r in hits)
        if found != sorted(REACTIONS):
            raise SystemExit("%s: expected each of %s once, found %s" % (f, REACTIONS, found))
        before = {r["id"]: {k: r.get(k) for k in FORWARD} for r in hits}
        if args.check:
            done = [r["id"] for r in hits if is_forward(r)]
            ok &= len(done) == len(hits)
            report[f] = {"format": name, "forward": sorted(done),
                         "not_forward": sorted(r["id"] for r in hits if not is_forward(r)),
                         "sha256": hashlib.sha256(raw).hexdigest()}
            continue
        for r in hits:
            r.update(FORWARD)
        out = json.dumps(t, **kw)
        with open(path, "w") as fh:
            fh.write(out)                               # no trailing newline, as before
        new = open(path, "rb").read()
        report[f] = {"format": name, "edited": sorted(before),
                     "before": before, "sha256": hashlib.sha256(new).hexdigest()}
    print(json.dumps(report, indent=1, sort_keys=True))
    if args.check and not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
