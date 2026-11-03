#!/usr/bin/env python
"""Row-level figures for validation/REPORT.md that the stage outputs do not state directly.

Compares stage b (gf_pass/per_genome.jsonl, this branch) with amendment A-C13 (prFBA
data/phenotype_gf_c13/, templates 21a8084) row by row, and, as a reference for how much any
small change moves gapfill solutions, A-C13 with A-C12 (prFBA data/phenotype_gf_c12fix/, the
same templates on ModelSEEDpy d884a50). Rows are matched on (genome, arm, pipeline); the six
main arms are the gapfilled rows, the ladder rows are not gapfilled.

Writes one JSON with:
  rows        matched rows; draft blocks, ladder rows (ignoring wall_seconds), ATP vectors
  gate        sanity_gate_ok False and status "gated", before and after
  growth      growth ratio after/before: quantiles, >10% movers by arm, pipeline and template;
              the constant baseline's share; movers by draft-level leak transition (stage a);
              every model whose growth changed more than twofold, with the seven reactions in
              its essential set before and after
  burden      gapfill burden (n_new_rxn) change: counts, histogram, per arm
  solutions   gapfill solution and essential-set changes; the same for A-C13 vs A-C12
  reversals   proposed and applied reversals, before and after
  seven       the seven reactions in solutions, reversals and essential sets
  medians     per arm and pipeline: essentiality disagreement, growth log-ratio to truth and
              gapfill burden, from the two phenotype_summary.json files
  summary_diff  which leaves of the two phenotype_summary.json files differ
  walls       per-genome wall times from the two pass logs
  smoke, oom_backup  the smoke rows and the 20 genomes kept from the OOM-killed run

    python validation/report_rows.py --out validation/gf_pass/report_rows.json
"""
import argparse
import collections
import json
import math
import os
import re
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SR = "/home/freiburger/Documents/prFBA/region_validation/shared_reference"
NEW = os.path.join(HERE, "gf_pass", "per_genome.jsonl")
C13 = os.path.join(SR, "data", "phenotype_gf_c13", "per_genome.jsonl")
C12 = os.path.join(SR, "data", "phenotype_gf_c12fix", "per_genome.jsonl")
NEW_SUM = os.path.join(HERE, "gf_pass", "phenotype_summary.json")
C13_SUM = os.path.join(SR, "data", "phenotype_gf_c13", "phenotype_summary.json")
SCAN = os.path.join(HERE, "scan", "scope_scan_tmpl7.jsonl")
NEW_LOG = os.path.join(HERE, "logs", "stage_b_gf_pass.log")
C13_LOG = os.path.join(SR, "logs", "pheno_c13_gf.log")
SMOKE = os.path.join(HERE, "smoke_2genomes", "per_genome.jsonl")
OOM = os.path.join(HERE, "gf_pass", "per_genome.oom-2254.jsonl")
MAIN = ("truth", "prfba_exact_tie", "picrust2", "base_nn1", "base_family_donor",
        "base_constant")
SEVEN = {"rxn00014", "rxn23850", "rxn05746", "rxn08933", "rxn08934", "rxn08935", "rxn08936"}
MOVED = 0.10


def load(path, drop_wall=False):
    out = {}
    with open(path) as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                if drop_wall:
                    r.pop("wall_seconds", None)
                out[(r["src_genome_id"], r["arm"], r["pipeline"])] = r
    return out


def gf(r):
    return r.get("gapfilled") or {}


def base(x):
    return str(x).split("_")[0]


def quantile(xs, p):
    i = (len(xs) - 1) * p
    lo, hi = math.floor(i), math.ceil(i)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def moved(r):
    return abs(r - 1) > MOVED


def solution_churn(X, Y, keys):
    sd = [len(set(gf(X[k]).get("new_rxn") or []) ^ set(gf(Y[k]).get("new_rxn") or []))
          for k in keys]
    rat = [gf(X[k])["growth"] / gf(Y[k])["growth"] for k in keys]
    return {"rows": len(keys),
            "solution_set_changed": sum(x > 0 for x in sd),
            "solution_symmetric_difference_median": st.median(sd),
            "solution_symmetric_difference_mean": round(st.mean(sd), 3),
            "essential_set_changed": sum(set(gf(X[k]).get("essential") or [])
                                         != set(gf(Y[k]).get("essential") or [])
                                         for k in keys),
            "burden_changed": sum(gf(X[k]).get("n_new_rxn") != gf(Y[k]).get("n_new_rxn")
                                  for k in keys),
            "growth_moved_gt10pct": sum(moved(r) for r in rat)}


def walls(path):
    d = {}
    with open(path) as fh:
        for line in fh:
            m = re.match(r"\[pheno\] (\S+) done in ([0-9.]+)s", line)
            if m:
                d[m.group(1)] = float(m.group(2))
    return d


def log_segments(path):
    """stage_b_gf_pass.log is appended to by each launch; a segment starts at each
    '[pheno] modelseedpy' line. Per segment: first line, the 'already done' line, genomes
    finished and the sum of their walls, and whether it ends with the final 'wrote' line."""
    segs = []
    with open(path) as fh:
        for i, line in enumerate(fh, 1):
            if line.startswith("[pheno] modelseedpy "):
                segs.append({"first_line": i, "selected": None, "genomes_done": 0,
                             "walls_sum_s": 0.0, "wrote_final": False})
            if not segs:
                continue
            s = segs[-1]
            if "already done" in line:
                s["selected"] = line.strip()
            m = re.match(r"\[pheno\] (\S+) done in ([0-9.]+)s", line)
            if m:
                s["genomes_done"] += 1
                s["walls_sum_s"] += float(m.group(2))
            if line.startswith("[pheno] wrote "):
                s["wrote_final"] = True
    for s in segs:
        s["walls_sum_s"] = round(s["walls_sum_s"])
    return segs


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(HERE, "gf_pass", "report_rows.json"))
    args = ap.parse_args()
    A, B, C = load(NEW), load(C13), load(C12)
    keys = sorted(set(A) & set(B))
    gk = [k for k in keys if k[1] in MAIN]
    lad = [k for k in keys if k[1] not in MAIN]
    out = {"inputs": {"after": NEW, "before": C13, "reference_pair_older": C12,
                      "scan": SCAN}}

    def nowall(r):
        r = dict(r)
        r.pop("wall_seconds", None)
        return r
    out["rows"] = {
        "after": len(A), "before": len(B), "matched": len(keys), "gapfilled_rows": len(gk),
        "ladder_rows": len(lad),
        "status_ok_after": sum(A[k].get("status") == "ok" for k in keys),
        "draft_block_differs": sum(A[k].get("draft") != B[k].get("draft") for k in keys),
        "ladder_rows_differ_ignoring_wall": sum(nowall(A[k]) != nowall(B[k]) for k in lad),
        "atp_vector_changed": sum((A[k].get("atp") or {}).get("vector")
                                  != (B[k].get("atp") or {}).get("vector") for k in keys),
        "atp_gate_failed_after": sum((A[k].get("atp") or {}).get("gate_ok") is False
                                     for k in keys),
        "empty_medium_atp_positive_after": sum(
            ((A[k].get("atp") or {}).get("empty_medium_atp") or 0) > 1e-6 for k in keys)}
    out["gate"] = {
        "sanity_gate_false_before": sum(gf(B[k]).get("sanity_gate_ok") is False for k in gk),
        "sanity_gate_false_after": sum(gf(A[k]).get("sanity_gate_ok") is False for k in gk),
        "status_gated_before": sum(B[k].get("status") == "gated" for k in keys),
        "status_gated_after": sum(A[k].get("status") == "gated" for k in keys)}

    # ---- growth ----
    ratio = {k: gf(A[k])["growth"] / gf(B[k])["growth"] for k in gk}
    rs = sorted(ratio.values())
    g = {"n": len(rs),
         "min_growth_before": min(gf(B[k])["growth"] for k in gk),
         "min_growth_after": min(gf(A[k])["growth"] for k in gk),
         "non_growing_after_le_1e-6": sum(gf(A[k])["growth"] <= 1e-6 for k in gk),
         "ratio_quantiles": {q: round(quantile(rs, p), 4) for q, p in (
             ("min", 0), ("p01", .01), ("p05", .05), ("p25", .25), ("p50", .5),
             ("p75", .75), ("p95", .95), ("p99", .99), ("max", 1))},
         "ratio_exactly_1": sum(abs(r - 1) < 1e-9 for r in rs),
         "ratio_within_1pct": sum(abs(r - 1) <= 0.01 for r in rs),
         "moved_gt10pct": sum(moved(r) for r in rs),
         "moved_up": sum(r > 1 + MOVED for r in rs),
         "moved_down": sum(r < 1 - MOVED for r in rs),
         "ratio_gt2": sum(r > 2 for r in rs), "ratio_lt0.5": sum(r < 0.5 for r in rs)}
    for dim, idx in (("by_arm", 1), ("by_pipeline", 2)):
        d = collections.defaultdict(list)
        for k, r in ratio.items():
            d[k[idx]].append(r)
        g[dim] = {a: {"n": len(v), "moved_gt10pct": sum(moved(r) for r in v),
                      "up": sum(r > 1 + MOVED for r in v),
                      "down": sum(r < 1 - MOVED for r in v)} for a, v in sorted(d.items())}
    d = collections.defaultdict(list)
    for k, r in ratio.items():
        if k[2] == "controlled":
            d[k[1]].append(r)
    g["controlled_by_arm"] = {a: {"n": len(v), "moved_gt10pct": sum(moved(r) for r in v)}
                              for a, v in sorted(d.items())}
    d = collections.defaultdict(list)
    for k, r in ratio.items():
        d[A[k]["template"]].append(r)
    g["by_template"] = {t: {"n": len(v), "moved_gt10pct": sum(moved(r) for r in v)}
                        for t, v in sorted(d.items())}
    bc = [k for k in gk if k[1] == "base_constant" and moved(ratio[k])]
    groups = collections.defaultdict(list)
    for k in gk:
        if k[1] == "base_constant":
            groups[(A[k]["fold"], A[k]["template"], k[2])].append(k)
    pairs = collections.Counter((round(gf(B[k])["growth"], 4), round(gf(A[k])["growth"], 4))
                                for k in bc)
    g["base_constant_movers"] = {
        "rows": len(bc), "up": sum(ratio[k] > 1 for k in bc),
        "down": sum(ratio[k] < 1 for k in bc),
        "distinct_before_after_growth_pairs": len(pairs),
        "fold_template_pipeline_groups_holding_movers": len(
            {(A[k]["fold"], A[k]["template"], k[2]) for k in bc}),
        "fold_template_pipeline_groups_total": len(groups),
        "top_pairs": [[list(p), n] for p, n in pairs.most_common(6)]}
    # the constant baseline uses one EC set per fold (C12_SCOPE section 1): its drafts are
    # one size per (fold, template), and many of its gapfilled models coincide
    ft = collections.defaultdict(set)
    for k in gk:
        if k[1] == "base_constant":
            ft[(A[k]["fold"], A[k]["template"])].add((A[k]["n_ec_input"],
                                                     A[k]["draft"]["n_rxn"]))
    g["base_constant_drafts"] = {
        "fold_template_groups": len(ft),
        "groups_with_one_ec_count_and_draft_size": sum(len(v) == 1 for v in ft.values()),
        "rows": sum(1 for k in gk if k[1] == "base_constant"),
        "distinct_gapfilled_models_template_pipeline_growth_burden": len(
            {(A[k]["template"], k[2], round(gf(A[k])["growth"], 4), gf(A[k])["n_new_rxn"])
             for k in gk if k[1] == "base_constant"})}
    other = [k for k in gk if k[1] != "base_constant" and moved(ratio[k])]
    g["other_arm_movers"] = {"rows": len(other), "genomes": len({k[0] for k in other})}
    # by draft-level leak transition (stage a: 21a8084 -> this branch)
    leak = {}
    with open(SCAN) as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                lab = "new" if "ModelSEEDTemplates-draftloops" in r["templates_dir"] else "old"
                leak[(r["src_genome_id"], r["arm"], lab)] = bool(r.get("leak"))

    def trans(k):
        o, n = leak[(k[0], k[1], "old")], leak[(k[0], k[1], "new")]
        return ("stops_leaking" if o and not n else "leaks_in_both" if o and n
                else "starts_leaking" if n else "leaks_in_neither")
    for name, sel in (("by_draft_leak_transition", gk),
                      ("by_draft_leak_transition_excluding_constant",
                       [k for k in gk if k[1] != "base_constant"])):
        d = collections.defaultdict(lambda: [0, 0, 0])
        for k in sel:
            t = trans(k)
            d[t][0] += 1
            d[t][1] += moved(ratio[k])
            d[t][2] += gf(A[k]).get("n_new_rxn") != gf(B[k]).get("n_new_rxn")
        g[name] = {t: {"gapfilled_rows": v[0], "moved_gt10pct": v[1], "burden_changed": v[2]}
                   for t, v in sorted(d.items())}
    big = []
    for k in gk:
        if ratio[k] > 2 or ratio[k] < 0.5:
            big.append({"key": "|".join(k), "ratio": round(ratio[k], 4),
                        "growth": [gf(B[k])["growth"], gf(A[k])["growth"]],
                        "n_new_rxn": [gf(B[k]).get("n_new_rxn"), gf(A[k]).get("n_new_rxn")],
                        "solution_symmetric_difference": len(
                            set(gf(A[k]).get("new_rxn") or [])
                            ^ set(gf(B[k]).get("new_rxn") or [])),
                        "seven_essential_before": sorted(
                            x for x in gf(B[k]).get("essential") or [] if base(x) in SEVEN),
                        "seven_essential_after": sorted(
                            x for x in gf(A[k]).get("essential") or [] if base(x) in SEVEN)})
    g["changed_more_than_twofold"] = sorted(big, key=lambda x: x["ratio"])
    # the genomes of the two large drops: every arm's growth and log-ratio to truth
    drops = sorted({x["key"].split("|")[0] for x in big if x["ratio"] < 0.5})
    g["large_drop_genomes_controlled"] = {
        gid: {arm: {"growth": [gf(B[(gid, arm, "controlled")])["growth"],
                               gf(A[(gid, arm, "controlled")])["growth"]],
                    "growth_log_ratio_to_truth": [
                        (B[(gid, arm, "controlled")].get("vs_truth") or {}).get(
                            "growth_log_ratio"),
                        (A[(gid, arm, "controlled")].get("vs_truth") or {}).get(
                            "growth_log_ratio")]}
              for arm in MAIN if (gid, arm, "controlled") in A}
        for gid in drops}
    out["growth"] = g

    # ---- burden ----
    dl = {k: gf(A[k]).get("n_new_rxn") - gf(B[k]).get("n_new_rxn") for k in gk}
    dv = list(dl.values())
    out["burden"] = {
        "changed": sum(x != 0 for x in dv), "up": sum(x > 0 for x in dv),
        "down": sum(x < 0 for x in dv), "mean": round(st.mean(dv), 4),
        "median": st.median(dv), "min": min(dv), "max": max(dv),
        "abs_le_1": sum(abs(x) <= 1 for x in dv), "abs_le_2": sum(abs(x) <= 2 for x in dv),
        "abs_ge_5": sum(abs(x) >= 5 for x in dv),
        "histogram": {str(a): b for a, b in sorted(collections.Counter(dv).items())},
        "total_before": sum(gf(B[k]).get("n_new_rxn") for k in gk),
        "total_after": sum(gf(A[k]).get("n_new_rxn") for k in gk),
        "by_arm": {a: {"n": sum(1 for k in gk if k[1] == a),
                       "changed": sum(dl[k] != 0 for k in gk if k[1] == a),
                       "mean": round(st.mean(dl[k] for k in gk if k[1] == a), 3)}
                   for a in MAIN}}

    # ---- solutions: this branch vs A-C13, and A-C13 vs A-C12 as the reference ----
    gk12 = [k for k in gk if k in C]
    out["solutions"] = {"edits_vs_A-C13": solution_churn(A, B, gk),
                        "A-C13_vs_A-C12": solution_churn(B, C, gk12)}

    # ---- reversals ----
    rv = {}
    for f in ("reversed_proposed", "reversed_applied"):
        b = {k for k in gk if gf(B[k]).get(f)}
        a = {k for k in gk if gf(A[k]).get(f)}
        rv[f] = {"rows_before": len(b), "rows_after": len(a), "both": len(a & b),
                 "only_before": len(b - a), "only_after": len(a - b)}
    rv["rows_proposed_ne_applied_before"] = sum(
        set(gf(B[k]).get("reversed_proposed") or {}) != set(gf(B[k]).get("reversed_applied")
                                                           or []) for k in gk)
    rv["rows_proposed_ne_applied_after"] = sum(
        set(gf(A[k]).get("reversed_proposed") or {}) != set(gf(A[k]).get("reversed_applied")
                                                           or []) for k in gk)
    for lab, X in (("before", B), ("after", A)):
        c = collections.Counter(base(x) for k in gk for x in gf(X[k]).get("reversed_applied")
                                or [])
        rv["reactions_reversed_" + lab] = dict(c.most_common())
        rv["total_reversed_" + lab] = sum(c.values())
    out["reversals"] = rv

    # ---- the seven reactions ----
    sv = {}
    for lab, X in (("before", B), ("after", A)):
        sv["rows_with_seven_in_solution_or_reversal_" + lab] = sum(
            any(base(x) in SEVEN for x in list(gf(X[k]).get("new_rxn") or [])
                + list(gf(X[k]).get("reversed_applied") or [])) for k in gk)
        c = collections.Counter(base(x) for k in gk for x in gf(X[k]).get("essential") or []
                                if base(x) in SEVEN)
        sv["essential_" + lab] = dict(sorted(c.items()))
        sv["models_with_a_seven_essential_" + lab] = sum(
            any(base(x) in SEVEN for x in gf(X[k]).get("essential") or []) for k in gk)
    out["seven"] = sv

    # ---- medians from the two summaries ----
    sn, so = json.load(open(NEW_SUM)), json.load(open(C13_SUM))
    med = {}
    for pipe in ("controlled", "as_shipped"):
        for arm in MAIN:
            for m in ("ess_shared_disagree_frac", "growth_log_ratio", "gapfill_burden"):
                x, y = sn["arms"][arm][pipe][m], so["arms"][arm][pipe][m]
                med["%s|%s|%s" % (pipe, arm, m)] = {
                    "edits": x["median"], "A-C13": y["median"], "n_edits": x["n"],
                    "n_A-C13": y["n"], "delta": round(x["median"] - y["median"], 6)}
    out["medians"] = med

    # ---- which summary leaves differ ----
    diffs = []

    def walk(a, b, path):
        if isinstance(a, dict) and isinstance(b, dict):
            for k in sorted(set(a) | set(b)):
                if k not in a or k not in b:
                    diffs.append(path + "/" + k)
                else:
                    walk(a[k], b[k], path + "/" + k)
        elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, "%s[%d]" % (path, i))
        elif a != b:
            diffs.append(path)
    for top in sn:
        if top != "meta":
            walk(sn[top], so[top], top)
    metric = re.compile(r"(ess_shared_disagree_frac|ess_shared_disagree|growth_log_ratio|"
                        r"gapfill_burden|atp_\w+|rxn_jaccard_\w+)")
    cnt = collections.Counter()
    for p in diffs:
        m = metric.search(p)
        cnt["%s:%s" % (p.split("/")[0], m.group(1) if m else "other")] += 1
    out["summary_diff"] = {"non_meta_leaves_differing": len(diffs),
                           "by_block_and_metric": dict(sorted(cnt.items())),
                           "blocks_with_any_difference": sorted({p.split("/")[0]
                                                                 for p in diffs}),
                           "atp_leaves_differing": sum("atp" in p for p in diffs)}

    # ---- per-genome walls ----
    wn, wo = walls(NEW_LOG), walls(C13_LOG)
    common = sorted(set(wn) & set(wo))
    out["walls"] = {"genomes_after": len(wn), "genomes_before": len(wo),
                    "sum_after_s": round(sum(wn.values())), "sum_before_s": round(sum(wo.values())),
                    "median_per_genome_ratio_after_over_before": round(
                        st.median(wn[g] / wo[g] for g in common), 3),
                    "stage_b_log_segments": log_segments(NEW_LOG)}

    # ---- smoke rows and the 20 genomes kept from the OOM-killed run ----
    S, An = load(SMOKE, drop_wall=True), load(NEW, drop_wall=True)
    out["smoke"] = {"rows": len(S), "identical_in_full_pass_ignoring_wall": sum(
        S[k] == An.get(k) for k in S)}
    with open(OOM) as fh:
        oom = [l.rstrip("\n") for l in fh if l.strip()]
    with open(NEW) as fh:
        fin = {l.rstrip("\n") for l in fh if l.strip()}
    oom_g = {json.loads(l)["src_genome_id"] for l in oom}
    out["oom_backup"] = {"rows": len(oom), "genomes": len(oom_g),
                         "lines_byte_identical_in_final": sum(l in fin for l in oom),
                         "final_rows_for_those_genomes": sum(
                             1 for k in A if k[0] in oom_g)}
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
