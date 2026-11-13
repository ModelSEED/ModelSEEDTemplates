#!/usr/bin/env python
"""Per-row comparison of a gapfilled pass on this branch's templates (stage b) with the
reference, amendment A-C13 (prFBA data/phenotype_gf_c13/: the same ModelSEEDpy c2e31a0,
--integrate-reversals, templates 21a8084). Rows are matched on (genome, arm, pipeline);
only genomes present in --after are compared, so this also checks a smoke run.

For each matched row: status, the C12 sanity gate (gapfilled.sanity_gate_ok), growth
(gapfilled.growth, > 1e-6 counts as growing), the number of gapfilled reactions
(gapfilled.n_new_rxn), the reversals applied (gapfilled.reversed_applied), whether any of
the seven reactions this branch restricts appears among the gapfilled or reversed
reactions, and whether the core ATP vector changed (the ATP readout uses Core-V6, which
this branch does not change). Ladder rows carry no gapfilled model (their `gapfilled`
fields are None), so the gate, growth and burden counts cover the gapfilled rows only.

    python validation/compare_gf_to_c13.py --after validation/gf_pass/per_genome.jsonl \
        --out validation/gf_pass/compare_vs_c13.json
"""
import argparse
import json
import math
import statistics as st
from collections import Counter

C13 = ("/home/freiburger/Documents/prFBA/region_validation/shared_reference/data/"
       "phenotype_gf_c13/per_genome.jsonl")
SEVEN = {"rxn00014", "rxn23850", "rxn05746", "rxn08933", "rxn08934", "rxn08935", "rxn08936"}
GROW = 1e-6


def load(path):
    out = {}
    with open(path) as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                out[(r["src_genome_id"], r["arm"], r["pipeline"])] = r
    return out


def gf(r):
    return r.get("gapfilled") or {}


def seven_in(r):
    ids = list(gf(r).get("new_rxn") or []) + [str(x) for x in gf(r).get("reversed_applied") or []]
    return sorted({x for x in ids if x.split("_")[0] in SEVEN})


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--after", required=True, help="per_genome.jsonl of the new pass")
    ap.add_argument("--before", default=C13, help="reference per_genome.jsonl (A-C13)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    a, b = load(args.after), load(args.before)
    genomes = {k[0] for k in a}
    keys = sorted(k for k in a if k in b)
    missing = sorted("|".join(k) for k in b if k[0] in genomes and k not in a)
    rows, c = [], Counter()
    ratios, deltas = [], []
    for k in keys:
        x, y = a[k], b[k]
        gx, gy = gf(x), gf(y)
        rec = {"key": "|".join(k), "status": [y.get("status"), x.get("status")],
               "gate_ok": [gy.get("sanity_gate_ok"), gx.get("sanity_gate_ok")],
               "growth": [gy.get("growth"), gx.get("growth")],
               "n_new_rxn": [gy.get("n_new_rxn"), gx.get("n_new_rxn")],
               "reversed_applied": [gy.get("reversed_applied") or [],
                                    gx.get("reversed_applied") or []],
               "seven_in_solution": seven_in(x),
               "atp_vector_equal": (x.get("atp") or {}).get("vector")
               == (y.get("atp") or {}).get("vector"),
               "draft_n_rxn": [(y.get("draft") or {}).get("n_rxn"),
                               (x.get("draft") or {}).get("n_rxn")]}
        rows.append(rec)
        c["rows"] += 1
        c["status_ok_after"] += x.get("status") == "ok"
        c["atp_vector_changed"] += not rec["atp_vector_equal"]
        if gy.get("sanity_gate_ok") is None and gx.get("sanity_gate_ok") is None:
            c["rows_not_gapfilled"] += 1          # ladder rows: nothing gapfills them
            continue
        c["rows_gapfilled"] += 1
        c["gated_before"] += gy.get("sanity_gate_ok") is False
        c["gated_after"] += gx.get("sanity_gate_ok") is False
        c["new_gate_failures"] += (gy.get("sanity_gate_ok") is not False
                                   and gx.get("sanity_gate_ok") is False)
        gb = (gy.get("growth") or 0) > GROW
        ga = (gx.get("growth") or 0) > GROW
        c["growing_before"] += gb
        c["growing_after"] += ga
        c["stopped_growing"] += gb and not ga
        c["reversal_applied_before"] += bool(gy.get("reversed_applied"))
        c["reversal_applied_after"] += bool(gx.get("reversed_applied"))
        c["seven_in_solution_after"] += bool(rec["seven_in_solution"])
        c["n_new_rxn_changed"] += gy.get("n_new_rxn") != gx.get("n_new_rxn")
        deltas.append((gx.get("n_new_rxn") or 0) - (gy.get("n_new_rxn") or 0))
        if gb and ga:
            ratios.append(gx["growth"] / gy["growth"])
    out = {"before": args.before, "after": args.after, "genomes": len(genomes),
           "rows_after": len(a), "matched": len(keys), "missing_from_after": missing,
           "counts": dict(c),
           "growth_ratio_after_over_before": (
               {"n": len(ratios), "median": st.median(ratios), "min": min(ratios),
                "max": max(ratios),
                "n_moved_gt_10pct": sum(abs(r - 1) > 0.10 for r in ratios),
                "median_abs_log": st.median(abs(math.log(r)) for r in ratios)}
               if ratios else None),
           "n_new_rxn_delta_mean_gapfilled_rows": st.mean(deltas) if deltas else None,
           "rows": rows}
    if args.out:
        with open(args.out, "w") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
            fh.write("\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
