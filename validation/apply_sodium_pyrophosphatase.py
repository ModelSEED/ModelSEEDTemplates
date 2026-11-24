#!/usr/bin/env python
"""Give two pyrophosphatase roles a reaction in every Archaea / GramNeg / GramPos template of v5.0, v6.0 and v7.0:

1. NEW role tftr01203 'sodium-translocating pyrophosphatase' (the RAST function string of the membrane Na+-translocating
   pyrophosphatase, Na+-PPase, EC 7.2.3.1). No template carries this role, so a genome whose only pyrophosphatase is the
   Na+ pump gets no PPi hydrolysis in its draft model. Add rxn54366_c with one new single-role complex tcpx01432:

     rxn54366 (ModelSEED): (1) cpd00001[0] + (1) cpd00012[0] + (1) cpd00971[0] <=> (2) cpd00009[0] + (1) cpd00067[0] + (1) cpd00971[1]
     template form:        H2O[c] + PPi[c] + Na+[c] -> 2 Pi[c] + H+[c] + Na+[e]   (one Na+ pumped out per PPi hydrolysed)

   Direction '>' (hydrolysis), as for rxn00001_c (soluble pyrophosphatase) and rxn42569_c (H+-PPase, ModelSEED PR #17): the
   database lists rxn54366 as '=', but the physiological direction of the Na+-PPase is PPi hydrolysis driving Na+ export.

2. ORPHAN role ftr33579 'inorganic diphosphatase (EC 3.6.1.1)' (the KEGG / newer RAST name of the soluble pyrophosphatase,
   already in these templates but listed by no complex): add one new single-role complex tcpx01433 to rxn00001_c.

Entries copy base_cost / forward_penalty / reverse_penalty from the file's rxn00001_c; type 'conditional'. The script stops if
an id it adds already exists, if ftr33579 is not orphan, or if a compound is missing. The Core templates are not touched.
Each file is written back in the serialization it already has (the script checks that json.dumps with that serialization
reproduces the current bytes before writing).

    python validation/apply_sodium_pyrophosphatase.py            # edit in place
    python validation/apply_sodium_pyrophosphatase.py --check    # verify only; exit 1 if not applied
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TROOT = os.path.join(os.path.dirname(HERE), "templates")
NA_ROLE, NA_ROLE_NAME = "tftr01203", "sodium-translocating pyrophosphatase"
NA_RXN, NA_CPX = "rxn54366_c", "tcpx01432"
NA_REAGENTS = (("cpd00001_c", -1), ("cpd00012_c", -1), ("cpd00971_c", -1), ("cpd00009_c", 2), ("cpd00067_c", 1),
               ("cpd00971_e", 1))
KEGG_ROLE, KEGG_ROLE_NAME, KEGG_CPX, SOL_RXN = "ftr33579", "inorganic diphosphatase (EC 3.6.1.1)", "tcpx01433", "rxn00001_c"
FILES = (
    "v5.0/ArchaeaModelTemplateV5.json", "v5.0/GramNegModelTemplateV5.json", "v5.0/GramPosModelTemplateV5.json",
    "v6.0/ArchaeaTemplateV6.json", "v6.0/GramNegModelTemplateV6.json", "v6.0/GramPosModelTemplateV6.json",
    "v7.0/ArchaeaTemplateV6.json", "v7.0/GramNegModelTemplateV7.json", "v7.0/GramPosModelTemplateV7.json",
)
UNTOUCHED = ("v5.0/CoreModelTemplateV5.json", "v6.0/Core-V5.2.json", "v7.0/Core-V6.json")
SERIALIZATIONS = (("default", {}, ""), ("indent4", {"indent": 4}, ""), ("indent2", {"indent": 2}, ""),
                  ("default+nl", {}, "\n"), ("indent4+nl", {"indent": 4}, "\n"), ("indent2+nl", {"indent": 2}, "\n"))


def detect_format(raw, t):
    for name, kw, tail in SERIALIZATIONS:
        if (json.dumps(t, **kw) + tail).encode() == raw:
            return name, kw, tail
    raise SystemExit("no known serialization reproduces the current bytes; refusing to write")


def _id(ref):
    return ref.split("/")[-1]


def complexes_with_role(t, role):
    return [c["id"] for c in t["complexes"] if any(_id(x["templaterole_ref"]) == role for x in c["complexroles"])]


def _cpx(cid, role):
    return {"complexroles": [{"optional_role": 0, "templaterole_ref": f"~/roles/id/{role}", "triggering": 1}],
            "confidence": 0, "id": cid, "name": cid, "reference": "ModelSEED 2.0", "source": "ModelSEED"}


def applied(t):
    roles = {r["id"]: r for r in t["roles"]}
    rx = {r["id"]: r for r in t["reactions"]}
    if NA_ROLE not in roles or roles[NA_ROLE]["name"] != NA_ROLE_NAME or NA_RXN not in rx or SOL_RXN not in rx:
        return False
    r = rx[NA_RXN]
    st = {_id(x["templatecompcompound_ref"]): x["coefficient"] for x in r["templateReactionReagents"]}
    return (st == dict(NA_REAGENTS) and r["direction"] == ">" and r["GapfillDirection"] == ">" and r["type"] == "conditional"
            and [_id(x) for x in r["templatecomplex_refs"]] == [NA_CPX] and complexes_with_role(t, NA_ROLE) == [NA_CPX]
            and complexes_with_role(t, KEGG_ROLE) == [KEGG_CPX]
            and f"~/complexes/id/{KEGG_CPX}" in rx[SOL_RXN]["templatecomplex_refs"])


def edit(t, f):
    roles = {r["id"]: r for r in t["roles"]}
    if NA_ROLE in roles or any(r["name"].strip().lower() == NA_ROLE_NAME for r in t["roles"]):
        raise SystemExit(f"{f}: role {NA_ROLE} / '{NA_ROLE_NAME}' already present")
    if KEGG_ROLE not in roles or roles[KEGG_ROLE]["name"] != KEGG_ROLE_NAME:
        raise SystemExit(f"{f}: role {KEGG_ROLE} missing or renamed")
    if complexes_with_role(t, KEGG_ROLE):
        raise SystemExit(f"{f}: role {KEGG_ROLE} is not orphan ({complexes_with_role(t, KEGG_ROLE)})")
    ids_c = {c["id"] for c in t["complexes"]}
    if NA_CPX in ids_c or KEGG_CPX in ids_c or any(r["id"] == NA_RXN for r in t["reactions"]):
        raise SystemExit(f"{f}: {NA_RXN}, {NA_CPX} or {KEGG_CPX} already present")
    cc = {c["id"] for c in t["compcompounds"]}
    miss = [m for m, _ in NA_REAGENTS if m not in cc]
    if miss:
        raise SystemExit(f"{f}: compcompounds {miss} missing")
    src = [r for r in t["reactions"] if r["id"] == SOL_RXN]
    if len(src) != 1:
        raise SystemExit(f"{f}: {SOL_RXN} not found once")
    src = src[0]
    t["roles"].append({"aliases": [], "features": [], "id": NA_ROLE, "name": NA_ROLE_NAME, "source": "ModelSEED"})
    t["complexes"].append(_cpx(NA_CPX, NA_ROLE))
    t["complexes"].append(_cpx(KEGG_CPX, KEGG_ROLE))
    src["templatecomplex_refs"].append(f"~/complexes/id/{KEGG_CPX}")
    t["reactions"].append({
        "GapfillDirection": ">", "base_cost": src["base_cost"], "direction": ">", "forward_penalty": src["forward_penalty"],
        "id": NA_RXN, "lower_bound": 0, "maxforflux": 1000, "maxrevflux": 0.0,
        "name": "diphosphate phosphohydrolase (Na+-translocating)", "reaction_ref": "kbase/default/reactions/id/rxn54366",
        "reverse_penalty": src["reverse_penalty"],
        "templateReactionReagents": [{"coefficient": c, "templatecompcompound_ref": f"~/compcompounds/id/{m}"} for m, c in NA_REAGENTS],
        "templatecompartment_ref": "~/compartments/id/c", "templatecomplex_refs": [f"~/complexes/id/{NA_CPX}"],
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
            if NA_ROLE in {r["id"] for r in t["roles"]} or any(r["id"] == NA_RXN for r in t["reactions"]):
                raise SystemExit(f"{f} unexpectedly holds {NA_ROLE} or {NA_RXN}")
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
        if not applied(json.loads(new)):
            raise SystemExit(f"{f}: written file does not verify")
        report[f] = {"format": name, "sha256_before": hashlib.sha256(raw).hexdigest(),
                     "sha256_after": hashlib.sha256(new).hexdigest()}
    print(json.dumps(report, indent=1))
    if args.check and not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
