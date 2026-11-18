#!/usr/bin/env python
"""Set rxn00598 (3-oxoadipyl-CoA thiolase, pcaF/paaJ, EC 2.3.1.174) to its thiolysis direction in
every template that carries it: Archaea, GramNeg and GramPos in templates/v5.0, v6.0 and v7.0.
The Core templates do not carry rxn00598; templates/legacy is not touched.

  rxn00598 as written: acetyl-CoA + succinyl-CoA (+ 5 H+ in the templates) => CoA + 3-oxoadipyl-CoA
  forward = condensation; the beta-ketoadipate and phenylacetate pathways run it backwards
  (thiolytic cleavage of 3-oxoadipyl-CoA). Until now every one of these templates had it '>'
  (condensation only), so a model could never run the pathway's last step.

Edit, per template entry (the convention the templates already use for a '<' reaction):
  direction '<', GapfillDirection '<', lower_bound -1000, upper_bound 0, maxforflux 0,
  maxrevflux 1000.0. Penalties, costs, stoichiometry and complexes are unchanged.

Each file is written back in the serialization it already has, so the diff touches only these
fields: the script checks that json.dumps with that serialization reproduces the file's current
bytes exactly before writing, and stops if no candidate does.

    python validation/apply_thiolase_direction.py            # edit in place
    python validation/apply_thiolase_direction.py --check    # verify only; exit 1 if not applied
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TROOT = os.path.join(os.path.dirname(HERE), "templates")
REACTION = "rxn00598_c"
FILES = (
    "v5.0/ArchaeaModelTemplateV5.json",
    "v5.0/GramNegModelTemplateV5.json",
    "v5.0/GramPosModelTemplateV5.json",
    "v6.0/ArchaeaTemplateV6.json",
    "v6.0/GramNegModelTemplateV6.json",
    "v6.0/GramPosModelTemplateV6.json",
    "v7.0/ArchaeaTemplateV6.json",
    "v7.0/GramNegModelTemplateV7.json",
    "v7.0/GramPosModelTemplateV7.json",
)
UNTOUCHED = (
    "v5.0/CoreModelTemplateV5.json",
    "v6.0/Core-V5.2.json",
    "v7.0/Core-V6.json",
)
REVERSE = {
    "direction": "<",
    "GapfillDirection": "<",
    "lower_bound": -1000,
    "upper_bound": 0,
    "maxforflux": 0,
    "maxrevflux": 1000.0,
}
FIELDS = tuple(REVERSE)
SERIALIZATIONS = (
    ("default", {}, ""),
    ("indent4", {"indent": 4}, ""),
    ("indent2", {"indent": 2}, ""),
    ("default+nl", {}, "\n"),
    ("indent4+nl", {"indent": 4}, "\n"),
    ("indent2+nl", {"indent": 2}, "\n"),
)


def detect_format(raw, t):
    for name, kw, tail in SERIALIZATIONS:
        if (json.dumps(t, **kw) + tail).encode() == raw:
            return name, kw, tail
    raise SystemExit(
        "no known serialization reproduces the current bytes; refusing to write"
    )


def is_reverse(r):
    return all(r.get(k) == v and type(r.get(k)) is type(v) for k, v in REVERSE.items())


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--templates", default=TROOT, help="the templates/ directory")
    ap.add_argument("--check", action="store_true", help="verify only, write nothing")
    args = ap.parse_args()
    report, ok = {}, True
    for f in FILES + UNTOUCHED:
        path = os.path.join(args.templates, f)
        raw = open(path, "rb").read()
        t = json.loads(raw)
        name, kw, tail = detect_format(raw, t)
        hits = [r for r in t["reactions"] if r["id"] == REACTION]
        if f in UNTOUCHED:
            if hits:
                raise SystemExit(f"{f} unexpectedly holds {REACTION}")
            report[f] = {
                "format": name,
                "edited": False,
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
            continue
        if len(hits) != 1:
            raise SystemExit(f"{f}: expected {REACTION} once, found {len(hits)}")
        r = hits[0]
        if args.check:
            ok &= is_reverse(r)
            report[f] = {
                "format": name,
                "applied": is_reverse(r),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
            continue
        before = {k: r.get(k) for k in FIELDS}
        r.update(REVERSE)
        with open(path, "w") as fh:
            fh.write(json.dumps(t, **kw) + tail)
        new = open(path, "rb").read()
        report[f] = {
            "format": name,
            "before": before,
            "after": {k: r.get(k) for k in FIELDS},
            "sha256_before": hashlib.sha256(raw).hexdigest(),
            "sha256_after": hashlib.sha256(new).hexdigest(),
        }
    print(json.dumps(report, indent=1, sort_keys=True))
    if args.check and not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
