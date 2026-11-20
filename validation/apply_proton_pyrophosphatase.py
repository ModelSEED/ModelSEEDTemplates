#!/usr/bin/env python
"""Give the role ftr05360 'Pyrophosphate-energized proton pump (EC 3.6.1.1)' its reaction: add rxn42569_c, the membrane
H+-translocating pyrophosphatase (H+-PPase, HppA family, EC 7.1.3.1), with one new single-role complex, to every template
that carries the role: Archaea, GramNeg and GramPos in templates/v5.0, v6.0 and v7.0. The Core templates do not carry the
role; templates/legacy is not touched.

  rxn42569 (ModelSEED): (1) cpd00001[0] + (1) cpd00012[0] => (2) cpd00009[0] + (1) cpd00067[1]
  template form:        H2O[c] + PPi[c] -> 2 Pi[c] + H+[e]   (one proton pumped out per PPi hydrolysed)

Before this change the role is orphan in all nine files (no complex lists it, so no reaction can receive its genes). A genome
whose only pyrophosphatase is the membrane pump therefore gets no PPi hydrolysis in its draft model. rxn00001 (soluble
inorganic pyrophosphatase) keeps its five complexes; nothing else changes.

Entry, per file: rxn42569_c with direction and GapfillDirection '>', lower_bound 0, upper_bound 1000, maxforflux 1000,
maxrevflux 0.0, type 'conditional', base_cost / forward_penalty / reverse_penalty copied from that file's rxn00001_c, and one
complex tcpx01431 (role ftr05360, triggering 1, optional_role 0). The script stops if the role is not orphan, if rxn42569_c or
tcpx01431 already exists, or if a compound of the reaction is missing.

Each file is written back in the serialization it already has: the script checks that json.dumps with that serialization
reproduces the file's current bytes exactly before writing, and stops if no candidate does.

    python validation/apply_proton_pyrophosphatase.py            # edit in place
    python validation/apply_proton_pyrophosphatase.py --check    # verify only; exit 1 if not applied
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TROOT = os.path.join(os.path.dirname(HERE), "templates")
ROLE, ROLE_NAME = "ftr05360", "Pyrophosphate-energized proton pump (EC 3.6.1.1)"
RXN, CPX = "rxn42569_c", "tcpx01431"
REAGENTS = (("cpd00001_c", -1), ("cpd00012_c", -1), ("cpd00009_c", 2), ("cpd00067_e", 1))
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
    raise SystemExit("no known serialization reproduces the current bytes; refusing to write")


def _id(ref):
    return ref.split("/")[-1]


def complexes_with_role(t, role):
    return [c["id"] for c in t["complexes"] if any(_id(x["templaterole_ref"]) == role for x in c["complexroles"])]


def applied(t):
    r = [x for x in t["reactions"] if x["id"] == RXN]
    c = [x for x in t["complexes"] if x["id"] == CPX]
    if len(r) != 1 or len(c) != 1:
        return False
    r, c = r[0], c[0]
    st = {_id(x["templatecompcompound_ref"]): x["coefficient"] for x in r["templateReactionReagents"]}
    return (st == dict(REAGENTS) and r["direction"] == ">" and r["GapfillDirection"] == ">" and r["type"] == "conditional"
            and [_id(x) for x in r["templatecomplex_refs"]] == [CPX]
            and [(_id(x["templaterole_ref"]), x["triggering"], x["optional_role"]) for x in c["complexroles"]] == [(ROLE, 1, 0)]
            and complexes_with_role(t, ROLE) == [CPX])


def edit(t, f):
    roles = {r["id"]: r for r in t["roles"]}
    if ROLE not in roles or roles[ROLE]["name"] != ROLE_NAME:
        raise SystemExit(f"{f}: role {ROLE} missing or renamed")
    if complexes_with_role(t, ROLE):
        raise SystemExit(f"{f}: role {ROLE} is not orphan ({complexes_with_role(t, ROLE)})")
    if any(r["id"] == RXN for r in t["reactions"]) or any(c["id"] == CPX for c in t["complexes"]):
        raise SystemExit(f"{f}: {RXN} or {CPX} already present")
    cc = {c["id"] for c in t["compcompounds"]}
    miss = [m for m, _ in REAGENTS if m not in cc]
    if miss:
        raise SystemExit(f"{f}: compcompounds {miss} missing")
    src = [r for r in t["reactions"] if r["id"] == "rxn00001_c"]
    if len(src) != 1:
        raise SystemExit(f"{f}: rxn00001_c not found once")
    src = src[0]
    t["complexes"].append({"complexroles": [{"optional_role": 0, "templaterole_ref": f"~/roles/id/{ROLE}", "triggering": 1}],
                           "confidence": 0, "id": CPX, "name": CPX, "reference": "ModelSEED 2.0", "source": "ModelSEED"})
    t["reactions"].append({
        "GapfillDirection": ">", "base_cost": src["base_cost"], "direction": ">", "forward_penalty": src["forward_penalty"],
        "id": RXN, "lower_bound": 0, "maxforflux": 1000, "maxrevflux": 0.0,
        "name": "diphosphate phosphohydrolase (H+-translocating)", "reaction_ref": "kbase/default/reactions/id/rxn42569",
        "reverse_penalty": src["reverse_penalty"],
        "templateReactionReagents": [{"coefficient": c, "templatecompcompound_ref": f"~/compcompounds/id/{m}"} for m, c in REAGENTS],
        "templatecompartment_ref": "~/compartments/id/c", "templatecomplex_refs": [f"~/complexes/id/{CPX}"],
        "type": "conditional", "upper_bound": 1000})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--templates", default=TROOT, help="the templates/ directory")
    ap.add_argument("--check", action="store_true", help="verify only, write nothing")
    args = ap.parse_args()
    report, ok = {}, True
    for f in FILES + UNTOUCHED:
        path = os.path.join(args.templates, f)
        raw = open(path, "rb").read()
        t = json.loads(raw)
        name, kw, tail = detect_format(raw, t)
        if f in UNTOUCHED:
            if ROLE in {r["id"] for r in t["roles"]} or any(r["id"] == RXN for r in t["reactions"]):
                raise SystemExit(f"{f} unexpectedly holds {ROLE} or {RXN}")
            report[f] = {"format": name, "edited": False, "sha256": hashlib.sha256(raw).hexdigest()}
            continue
        if args.check:
            ok &= applied(t)
            report[f] = {"format": name, "applied": applied(t), "sha256": hashlib.sha256(raw).hexdigest()}
            continue
        edit(t, f)
        with open(path, "w") as fh:
            fh.write(json.dumps(t, **kw) + tail)
        new = open(path, "rb").read()
        t2 = json.loads(new)
        if not applied(t2):
            raise SystemExit(f"{f}: written file does not verify")
        report[f] = {"format": name, "sha256_before": hashlib.sha256(raw).hexdigest(),
                     "sha256_after": hashlib.sha256(new).hexdigest(),
                     "reactions": [len(t2["reactions"]) - 1, len(t2["reactions"])],
                     "complexes": [len(t2["complexes"]) - 1, len(t2["complexes"])]}
    print(json.dumps(report, indent=1))
    if args.check and not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
