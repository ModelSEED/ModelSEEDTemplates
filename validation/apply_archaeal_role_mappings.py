#!/usr/bin/env python
"""Map three methanogen roles to their reactions, where the templates either leave the role without a reaction or lack
the role or reaction entirely. Applied to templates/v5.0, v6.0 and v7.0; templates/legacy is not touched.

  FBA  The bifunctional archaeal fructose-1,6-bisphosphate aldolase/phosphatase (FBPA/P; role 'Fructose-bisphosphate
       aldolase/bisphosphatase ancestral bifunctional (EC 4.1.2.13) (EC 3.1.3.11)') reaches only the phosphatase,
       rxn00549_c, through its single-role complex. That complex is added to the aldolase rxn00786_c as well.
         Archaea, GramNeg, GramPos: complex tcpx00462 (role tftr00666); Core: tcpx00463 (role tftr00121).
  ADK  'Adenylate kinase, archaeal type (EC 2.7.4.3)' is not a template role, so drafts of genomes whose only
       adenylate kinase is the archaeal type get no adenylate kinase at all. New role tftr01203 with a single-role
       complex tcpx01432 on rxn00097_c (Archaea).
  TFR  The thiol:fumarate reductase of methanogens (TfrAB; fumarate + CoM + CoB -> succinate + CoM-S-S-CoB) is in no
       template. New roles tftr01204 (TfrA) and tftr01205 (TfrB), one complex tcpx01433 with both as triggering
       subunits, and a new reaction rxn40405_c (Archaea):
         fumarate[c] + CoM[c] + HTP[c] -> succinate[c] + CoM-S-S-HTP[c] + H+[c]
       The H+ balances the equation on the template's own compounds (HTP is stored with charge -2, the database
       entry has no H+). Direction '>': E0' is +33 mV for fumarate/succinate and about -143 mV for CoM-S-S-CoB, so
       dG0' is about -34 kJ/mol; the database gives '='. base_cost and penalties as rxn03127_c (methyl-CoM reductase),
       type 'conditional'.

New ids are above the largest in every v5.0/v6.0/v7.0 file on main, and above tcpx01431, which the pending H+-PPase
change uses. The script stops if an id is taken, an expected role/complex does not match, or a compound is missing,
and writes each file in the serialization it already has (checked against the current bytes first).

    python validation/apply_archaeal_role_mappings.py            # edit in place
    python validation/apply_archaeal_role_mappings.py --check    # verify only; exit 1 if not applied
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TROOT = os.path.join(os.path.dirname(HERE), "templates")
FILES = {
    "v5.0/ArchaeaModelTemplateV5.json": "archaea",
    "v6.0/ArchaeaTemplateV6.json": "archaea",
    "v7.0/ArchaeaTemplateV6.json": "archaea",
    "v5.0/GramNegModelTemplateV5.json": "gram",
    "v5.0/GramPosModelTemplateV5.json": "gram",
    "v6.0/GramNegModelTemplateV6.json": "gram",
    "v6.0/GramPosModelTemplateV6.json": "gram",
    "v7.0/GramNegModelTemplateV7.json": "gram",
    "v7.0/GramPosModelTemplateV7.json": "gram",
    "v5.0/CoreModelTemplateV5.json": "core",
    "v6.0/Core-V5.2.json": "core",
    "v7.0/Core-V6.json": "core",
}
SERIALIZATIONS = (("default", {}, ""), ("indent4", {"indent": 4}, ""), ("indent2", {"indent": 2}, ""),
                  ("default+nl", {}, "\n"), ("indent4+nl", {"indent": 4}, "\n"), ("indent2+nl", {"indent": 2}, "\n"))
ROLE_ADK = ("tftr01203", "Adenylate kinase, archaeal type (EC 2.7.4.3)")
ROLE_TFRA = ("tftr01204", "Fumarate reductase (CoM/CoB), subunit TfrA (EC 1.3.4.1)")
ROLE_TFRB = ("tftr01205", "Fumarate reductase (CoM/CoB), subunit TfrB (EC 1.3.4.1)")
CPX_ADK, CPX_TFR, RXN_TFR = "tcpx01432", "tcpx01433", "rxn40405_c"
TFR_REAGENTS = (("cpd00106_c", -1), ("cpd02246_c", -1), ("cpd02817_c", -1),
                ("cpd00036_c", 1), ("cpd02935_c", 1), ("cpd00067_c", 1))


def detect_format(raw, t):
    for name, kw, tail in SERIALIZATIONS:
        if (json.dumps(t, **kw) + tail).encode() == raw:
            return name, kw, tail
    raise SystemExit("no known serialization reproduces the current bytes; refusing to write")


def role(rid, name):
    return {"aliases": [], "features": [], "id": rid, "name": name, "source": "ModelSEED"}


def cpx(cid, role_ids):
    return {"complexroles": [{"optional_role": 0, "templaterole_ref": f"~/roles/id/{r}", "triggering": 1}
                             for r in role_ids],
            "confidence": 0, "id": cid, "name": cid, "reference": "ModelSEED 2.0", "source": "ModelSEED"}


def fba_ids(kind):
    return ("tcpx00463", "tftr00121") if kind == "core" else ("tcpx00462", "tftr00666")


def state(t, kind):
    """{"FBA": bool, "ADK": bool, "TFR": bool} -- which edits are present (ADK/TFR only for archaea)."""
    rx = {r["id"]: r for r in t["reactions"]}
    out = {"FBA": f"~/complexes/id/{fba_ids(kind)[0]}" in rx["rxn00786_c"].get("templatecomplex_refs", [])}
    if kind == "archaea":
        out["ADK"] = f"~/complexes/id/{CPX_ADK}" in rx["rxn00097_c"].get("templatecomplex_refs", [])
        out["TFR"] = RXN_TFR in rx
    return out


def apply(t, kind):
    roles = {r["id"]: r for r in t["roles"]}
    cpxs = {c["id"]: c for c in t["complexes"]}
    rxns = {r["id"]: r for r in t["reactions"]}
    ccs = {c["id"] for c in t["compcompounds"]}
    log = []

    def absent(ids):
        for i in ids:
            if i in roles or i in cpxs or i in rxns:
                raise SystemExit(f"{i} already exists")

    def add_ref(rid, cid):
        refs = rxns[rid].setdefault("templatecomplex_refs", [])
        refs.append(f"~/complexes/id/{cid}")
        log.append(f"{rid} += {cid}")

    fcpx, frole = fba_ids(kind)
    if [x["templaterole_ref"] for x in cpxs[fcpx]["complexroles"]] != [f"~/roles/id/{frole}"]:
        raise SystemExit(f"{fcpx} is not the single-role complex of {frole}")
    if not roles[frole]["name"].startswith("Fructose-bisphosphate aldolase/bisphosphatase ancestral bifunctional"):
        raise SystemExit(f"{frole} is not the bifunctional FBPA/P role")
    add_ref("rxn00786_c", fcpx)
    if kind == "archaea":
        absent([ROLE_ADK[0], CPX_ADK, ROLE_TFRA[0], ROLE_TFRB[0], CPX_TFR, RXN_TFR])
        t["roles"].append(role(*ROLE_ADK))
        t["complexes"].append(cpx(CPX_ADK, [ROLE_ADK[0]]))
        add_ref("rxn00097_c", CPX_ADK)
        for c, _ in TFR_REAGENTS:
            if c not in ccs:
                raise SystemExit(f"missing compcompound {c}")
        t["roles"] += [role(*ROLE_TFRA), role(*ROLE_TFRB)]
        t["complexes"].append(cpx(CPX_TFR, [ROLE_TFRA[0], ROLE_TFRB[0]]))
        mcr = rxns["rxn03127_c"]
        t["reactions"].append({
            "GapfillDirection": ">", "base_cost": mcr["base_cost"], "direction": ">",
            "forward_penalty": mcr["forward_penalty"], "id": RXN_TFR, "lower_bound": 0, "maxforflux": 1000,
            "maxrevflux": 0.0, "name": "fumarate CoM:CoB oxidoreductase (succinate forming)",
            "reaction_ref": "kbase/default/reactions/id/rxn40405", "reverse_penalty": mcr["reverse_penalty"],
            "templateReactionReagents": [{"coefficient": k, "templatecompcompound_ref": f"~/compcompounds/id/{c}"}
                                         for c, k in TFR_REAGENTS],
            "templatecompartment_ref": "~/compartments/id/c",
            "templatecomplex_refs": [f"~/complexes/id/{CPX_TFR}"], "type": "conditional", "upper_bound": 1000})
        log.append(f"roles {ROLE_ADK[0]}, {ROLE_TFRA[0]}, {ROLE_TFRB[0]}; complexes {CPX_ADK}, {CPX_TFR}; {RXN_TFR}")
    return log


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    bad = 0
    for rel, kind in FILES.items():
        path = os.path.join(TROOT, rel)
        raw = open(path, "rb").read()
        t = json.loads(raw)
        st = state(t, kind)
        if a.check:
            print(f"{rel}: {st}")
            bad += not all(st.values())
            continue
        if all(st.values()):
            print(f"{rel}: already applied")
            continue
        if any(st.values()):
            raise SystemExit(f"{rel}: partly applied {st}; refusing")
        name, kw, tail = detect_format(raw, t)
        log = apply(t, kind)
        open(path, "wb").write((json.dumps(t, **kw) + tail).encode())
        print(f"{rel} ({name}): {'; '.join(log)}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
