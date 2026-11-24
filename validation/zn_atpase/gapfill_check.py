#!/usr/bin/env python
"""gapfill_check.py -- does the rxn09388 direction decide whether a gapfilled model makes ATP from phosphate?

For each draft model given, gapfill twice on the same medium, once against the v7.0 templates of `main` and once against
the patched templates of this branch (for the patched run the draft's own rxn09388 is set to the patched direction
first, as a draft built from the patched template would carry it). Gapfilling is ModelSEEDpy's MSGapfill on bio1
(minimum 0.01, prefilter on), with the ATP-correction 'empty' test of MSATPCorrection on the Core-V6 template, as in the
pipeline that produced the drafts. Each gapfilled model is then tested:

  growth      bio1 on the medium
  sealed_atp  an ATP hydrolysis test reaction (ATP + H2O -> ADP + Pi + H+) maximised with every uptake closed
              (exports open)
  atp_h_pi    the same with only H+ and phosphate allowed in
  rxn09388    its bounds; rxn05150 (Zn2+ ABC importer), rxn43657 (Zn2+:H+ symport): present?

    python validation/zn_atpase/gapfill_check.py --main-root DIR --patched-root templates/v7.0 \
        --medium validation/zn_atpase/wolfe_h2co2_medium.json --template GramPosModelTemplateV7.json DRAFT.xml ...
    -> validation/zn_atpase/gapfill_check.json
"""
import argparse
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def load_template(path):
    from modelseedpy.core.mstemplate import MSTemplateBuilder
    return MSTemplateBuilder.from_dict(json.load(open(path))).build()


def medium_of(path):
    from modelseedpy import MSMedia
    comp = json.load(open(path))["compounds"]
    m = MSMedia.from_dict(comp)
    m.id = m.name = os.path.basename(path)
    return m, comp


def apply_medium(model, comp):
    for r in model.exchanges:
        r.lower_bound = -comp.get(r.id[3:].split("_")[0], 0.0)


def atp_test(model, open_cpds=()):
    from cobra import Reaction
    with model:
        for r in model.boundary:
            cid = r.id[3:].split("_")[0] if r.id.startswith("EX_") else None
            r.lower_bound = -1000.0 if cid in open_cpds else 0.0
            r.upper_bound = max(r.upper_bound, 0.0)
        for r in model.reactions:                       # release forced fluxes (maintenance floors)
            if not r.boundary and (r.lower_bound > 0 or r.upper_bound < 0):
                r.bounds = (min(r.lower_bound, 0.0), max(r.upper_bound, 0.0))
        g = lambda c: model.metabolites.get_by_id(f"{c}_c0")  # noqa: E731
        t = Reaction("ATPtest", lower_bound=0, upper_bound=1000)
        t.add_metabolites({g("cpd00002"): -1, g("cpd00001"): -1, g("cpd00008"): 1, g("cpd00009"): 1, g("cpd00067"): 1})
        model.add_reactions([t])
        model.objective = t
        v = model.slim_optimize(error_value=float("nan"))
    return None if v != v else round(v, 6)


def run(draft, tpl_path, core_path, medium, comp, patched):
    import cobra
    from cobra.io import read_sbml_model
    from modelseedpy.core.msatpcorrection import MSATPCorrection
    from modelseedpy.core.msgapfill import MSGapfill
    m = read_sbml_model(draft)
    m.id = os.path.basename(draft)[:-4]
    if patched:
        for r in m.reactions:
            if r.id.startswith("rxn09388"):
                r.lower_bound = 0.0
    before = {r.id for r in m.reactions}
    atp = MSATPCorrection(m, load_template(core_path))
    atp.evaluate_growth_media(no_gapfilling=True)
    atp.determine_growth_media()
    atp.expand_model_to_genome_scale()
    tests = [x for x in atp.build_tests() if x["media"].id == "empty"]
    added = atp.atp_hydrolysis.id if atp.atp_hydrolysis.id not in before else None
    t0 = time.time()
    gf = MSGapfill(m, default_gapfill_templates=[load_template(tpl_path)], test_conditions=tests)
    sol = gf.run_gapfilling(media=medium, target="bio1", minimum_obj=0.01, binary_check=False, prefilter=True)
    rec = {"gapfill_seconds": round(time.time() - t0, 1)}
    if not sol:
        rec["status"] = "no gapfill solution"
        return rec
    gf.integrate_gapfill_solution(sol, cumulative_solution=[])
    if added and added in m.reactions:
        m.remove_reactions([added])
    rec["n_gapfilled"] = len(sol.get("new", {})) + len(sol.get("reversed", {}))
    rec["gapfilled_zn_or_ppi"] = sorted(k for k in list(sol.get("new", {})) + list(sol.get("reversed", {}))
                                        if k.split("_")[0] in ("rxn09388", "rxn05150", "rxn43657", "rxn11268", "rxn00001")
                                        or k.startswith("EX_cpd00012"))
    with m:
        apply_medium(m, comp)
        m.objective = "bio1"
        rec["growth"] = round(m.slim_optimize(error_value=0.0), 6)
    rec["sealed_atp"] = atp_test(m)
    rec["atp_h_pi"] = atp_test(m, ("cpd00067", "cpd00009"))
    rec["rxn09388"] = [list(r.bounds) for r in m.reactions if r.id.startswith("rxn09388")]
    rec["has_rxn05150"] = any(r.id.startswith("rxn05150") for r in m.reactions)
    rec["has_rxn43657"] = any(r.id.startswith("rxn43657") for r in m.reactions)
    rec["ppi_exchange"] = [list(r.bounds) for r in m.reactions if r.id.startswith("EX_cpd00012")]
    rec["status"] = "ok"
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--main-root", required=True)
    ap.add_argument("--patched-root", required=True)
    ap.add_argument("--medium", required=True)
    ap.add_argument("--template", default="GramPosModelTemplateV7.json")
    ap.add_argument("--core", default="Core-V6.json")
    ap.add_argument("drafts", nargs="+")
    a = ap.parse_args()
    try:            # optional: a project's shim for a ModelSEEDpy checkout whose MSModelUtil.printlp is shadowed
        import _msp_compat  # noqa: F401
    except ImportError:
        pass
    import cobra
    cobra.Configuration().solver = "gurobi"
    medium, comp = medium_of(a.medium)
    out = {"medium": os.path.basename(a.medium), "template": a.template, "models": {}}
    path = os.path.join(HERE, "gapfill_check.json")
    for d in a.drafts:
        name = os.path.basename(d)[:-4]
        out["models"][name] = {}
        for label, root, patched in (("main", a.main_root, False), ("patched", a.patched_root, True)):
            rec = run(d, os.path.join(root, a.template), os.path.join(root, a.core), medium, comp, patched)
            out["models"][name][label] = rec
            print(name, label, {k: rec.get(k) for k in ("status", "growth", "sealed_atp", "atp_h_pi", "rxn09388",
                                                        "has_rxn05150", "has_rxn43657")}, flush=True)
            json.dump(out, open(path, "w"), indent=1)


if __name__ == "__main__":
    main()
