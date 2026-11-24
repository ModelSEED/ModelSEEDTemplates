#!/usr/bin/env python
"""Restrict rxn09388_c (Zn2+-exporting P-type ATPase, ZntA family) to its database direction, ATP hydrolysis with Zn2+
export, in every template that carries it: Archaea, GramNeg and GramPos in templates/v5.0, v6.0 and v7.0. The Core
templates do not carry it; templates/legacy is not touched.

  rxn09388 (ModelSEED database, '>'): (1) cpd00001[0] + (1) cpd00002[0] + (1) cpd00034[0]
                                      => (1) cpd00008[0] + (1) cpd00009[0] + (1) cpd00034[1] + (1) cpd00067[0]
  template form:                      H2O[c] + ATP[c] + Zn2+[c] -> ADP[c] + Pi[c] + Zn2+[e] + H+[c]

In all nine files the entry is reversible ('='). Run backwards it is an ATP synthase driven by a Zn2+ gradient: paired
with Zn2+:H+ symport (rxn43657) it makes ATP from the proton gradient, and with Na+/Pi symport, Na+/H+ antiport and a
pyrophosphate exit it makes ATP from imported phosphate alone (2 Pi + H+ -> PPi + H2O, uphill). The edit, per file,
follows the convention of the earlier direction fixes: direction and GapfillDirection '>', lower_bound 0, maxrevflux 0.0;
upper_bound, maxforflux, base_cost, penalties, type, reagents and complexes unchanged.

The script stops if the entry is missing, if ATP is not a reactant of the stored stoichiometry (the forward direction
must be hydrolysis), or if no known serialization reproduces the file's current bytes.

    python validation/apply_zn_atpase_direction.py            # edit in place
    python validation/apply_zn_atpase_direction.py --check    # verify only; exit 1 if not applied
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TROOT = os.path.join(os.path.dirname(HERE), "templates")
RXN = "rxn09388_c"
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
SERIALIZATIONS = (
    ("default", {}, ""),
    ("indent4", {"indent": 4}, ""),
    ("indent2", {"indent": 2}, ""),
    ("default+nl", {}, "\n"),
    ("indent4+nl", {"indent": 4}, "\n"),
    ("indent2+nl", {"indent": 2}, "\n"),
)
TARGET = {"direction": ">", "GapfillDirection": ">", "lower_bound": 0, "maxrevflux": 0.0}


def detect_format(raw, t):
    for name, kw, tail in SERIALIZATIONS:
        if (json.dumps(t, **kw) + tail).encode() == raw:
            return name, kw, tail
    raise SystemExit("no known serialization reproduces the current bytes; refusing to write")


def entry(t, path):
    rs = [r for r in t["reactions"] if r["id"] == RXN]
    if len(rs) != 1:
        raise SystemExit(f"{path}: {len(rs)} entries for {RXN}")
    r = rs[0]
    st = {x["templatecompcompound_ref"].split("/")[-1]: x["coefficient"] for x in r["templateReactionReagents"]}
    if not st.get("cpd00002_c", 0) < 0 or not st.get("cpd00034_e", 0) > 0:
        raise SystemExit(f"{path}: {RXN} is not stored as ATP hydrolysis with Zn2+ export: {st}")
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    bad = 0
    for rel in FILES:
        path = os.path.join(TROOT, rel)
        raw = open(path, "rb").read()
        t = json.loads(raw)
        r = entry(t, rel)
        done = all(r.get(k) == v for k, v in TARGET.items())
        if a.check:
            print(f"{rel}: {'applied' if done else 'NOT applied'} ({r['direction']}, lb {r['lower_bound']})")
            bad += not done
            continue
        if done:
            print(f"{rel}: already applied")
            continue
        name, kw, tail = detect_format(raw, t)
        was = {k: r.get(k) for k in TARGET}
        r.update(TARGET)
        open(path, "wb").write((json.dumps(t, **kw) + tail).encode())
        print(f"{rel}: {was} -> {TARGET} ({name})")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
