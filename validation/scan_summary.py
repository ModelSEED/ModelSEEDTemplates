#!/usr/bin/env python
"""Summarize the draft-level scan (stage a): prFBA's egc_scope_scan.py over every
(genome, arm) draft of the 200-genome gapfilled pass, on this branch's templates and on
21a8084, with nothing gapfilled. A draft "leaks" when it makes ATP (ATPM_c0) or biomass
with every uptake closed and only water and protons free (phenotype_arm.sanity_gate).

For each templates directory: drafts, leaking drafts, leaking truth drafts, leaks at the
1,000 ATPM bound (empty_atp >= 999.999), drafts making biomass from nothing, errors,
genomes with a leaking draft, and the split by template and arm. Then the transitions
21a8084 -> this branch per draft, and a row-for-row check against prFBA's own scans:
  - this branch's rows against the probe rows (templates_scope/ccp_gapn_mdg in
    data/egc_analysis/scope_scan_variants.jsonl, ModelSEEDpy d884a50), which used
    reaction-identical templates (validation/probe_comparison.json);
  - the 21a8084 rows against the c12run rows of data/egc_analysis/scope_scan_200.jsonl
    (d884a50).
C12_SCOPE.md section 1 found leak flags and empty-medium ATP independent of the
ModelSEEDpy commit (d884a50 vs c2e31a0); only draft reaction counts differ (demand
reactions), so leak and empty_atp are compared, and n_rxn differences are counted.

    python validation/scan_summary.py --scan validation/scan/scope_scan_tmpl7.jsonl \
        --out validation/scan/scan_summary.json
"""
import argparse
import collections
import json
import os

SR = "/home/freiburger/Documents/prFBA/region_validation/shared_reference"
PRIOR_VARIANTS = os.path.join(SR, "data/egc_analysis/scope_scan_variants.jsonl")
PRIOR_200 = os.path.join(SR, "data/egc_analysis/scope_scan_200.jsonl")
BOUND = 999.999


def load(path):
    with open(path) as fh:
        return [json.loads(l) for l in fh if l.strip()]


def label(d):
    if "ModelSEEDTemplates-draftloops" in d:
        return "tmpl7"
    if "ModelSEEDTemplates-c12run" in d:
        return "21a8084"
    if "main2294299" in d:
        return "2294299"
    return d.rstrip("/").rsplit("/", 1)[-1]


def counts(rows):
    c = {"drafts": len(rows),
         "leaking": sum(bool(r.get("leak")) for r in rows),
         "leaking_truth": sum(bool(r.get("leak")) and r["arm"] == "truth" for r in rows),
         "at_1000_bound": sum(bool(r.get("leak")) and r.get("empty_atp", 0) >= BOUND
                              for r in rows),
         "biomass_from_nothing": sum(r.get("empty_biomass", 0) > 1e-6 for r in rows),
         "errors": sum(r.get("status") != "ok" for r in rows),
         "genomes": len({r["src_genome_id"] for r in rows}),
         "genomes_with_leak": len({r["src_genome_id"] for r in rows if r.get("leak")})}
    for key in ("template", "arm"):
        c["leaking_by_" + key] = {
            k: "%d/%d" % (sum(bool(r.get("leak")) for r in rows if r[key] == k),
                          sum(1 for r in rows if r[key] == k))
            for k in sorted({r[key] for r in rows})}
    return c


def rowwise(a, b):
    """a, b: {(genome, arm): row}; compare leak flags and empty_atp"""
    keys = sorted(set(a) & set(b))
    return {"matched": len(keys), "only_new": len(set(a) - set(b)),
            "only_prior": len(set(b) - set(a)),
            "leak_differs": sorted("%s|%s" % k for k in keys
                                   if bool(a[k].get("leak")) != bool(b[k].get("leak"))),
            "empty_atp_differs": sorted(
                "%s|%s" % k for k in keys
                if abs(a[k].get("empty_atp", 0) - b[k].get("empty_atp", 0)) > 1e-6),
            "n_rxn_differs": sum(a[k].get("n_rxn") != b[k].get("n_rxn") for k in keys)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scan", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = load(args.scan)
    by = collections.defaultdict(list)
    for r in rows:
        by[label(r["templates_dir"])].append(r)
    out = {"scan": os.path.abspath(args.scan),
           "templates_dirs": sorted({r["templates_dir"] for r in rows}),
           "by_templates": {k: counts(v) for k, v in sorted(by.items())}}
    idx = {k: {(r["src_genome_id"], r["arm"]): r for r in v} for k, v in by.items()}
    if "tmpl7" in idx and "21a8084" in idx:
        a, b = idx["21a8084"], idx["tmpl7"]
        keys = sorted(set(a) & set(b))
        out["transitions_21a8084_to_tmpl7"] = {
            "stops_leaking": sum(bool(a[k]["leak"]) and not b[k]["leak"] for k in keys),
            "starts_leaking": sorted("%s|%s" % k for k in keys
                                     if not a[k]["leak"] and b[k]["leak"]),
            "leaks_in_both": sum(bool(a[k]["leak"]) and bool(b[k]["leak"]) for k in keys),
            "leaks_in_neither": sum(not a[k]["leak"] and not b[k]["leak"] for k in keys)}
    prior = {}
    if os.path.exists(PRIOR_VARIANTS):
        prior["tmpl7_vs_probe_ccp_gapn_mdg"] = ("tmpl7", PRIOR_VARIANTS, "ccp_gapn_mdg")
    if os.path.exists(PRIOR_200):
        prior["21a8084_vs_prior_scan_200"] = ("21a8084", PRIOR_200, "ModelSEEDTemplates-c12run")
    out["vs_prior"] = {}
    for name, (lab, path, tag) in prior.items():
        if lab not in idx:
            continue
        p = {(r["src_genome_id"], r["arm"]): r for r in load(path) if tag in r["templates_dir"]}
        rec = rowwise(idx[lab], p)
        rec["prior_file"] = path
        out["vs_prior"][name] = rec
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    for k, v in out["by_templates"].items():
        print("%-8s leaking %d/%d drafts, truth %d, at bound %d, errors %d" % (
            k, v["leaking"], v["drafts"], v["leaking_truth"], v["at_1000_bound"], v["errors"]))
    for k, v in out["vs_prior"].items():
        print("%s: matched %d, leak differs %d, empty_atp differs %d, n_rxn differs %d" % (
            k, v["matched"], len(v["leak_differs"]), len(v["empty_atp_differs"]),
            v["n_rxn_differs"]))


if __name__ == "__main__":
    main()
