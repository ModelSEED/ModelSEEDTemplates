#!/usr/bin/env python
"""Check the edited templates against (1) their parent commit and (2) the probe templates
prFBA's draft-level scan used (variant ccp_gapn_mdg of
prFBA/region_validation/shared_reference/scripts/egc_template_variants.py).

  (1) parent: parse templates/v7.0/<file> at --base-commit (default 21a8084) and in the
      working tree; every top-level key other than "reactions" must be equal, the reaction
      id lists must be equal and in the same order, and the reactions that differ must be
      exactly the seven, each differing in exactly direction, GapfillDirection,
      lower_bound and maxrevflux.
  (2) probe: whole-file sha256 of both, then, after parsing, the top-level keys other
      than "reactions" and every reaction serialized as json.dumps(r, sort_keys=True)
      are compared byte for byte. The probe files are all single-line json.dump output,
      so ArchaeaTemplateV6.json (indent=4 in this repository) is expected to differ in
      whole-file bytes only.

    python validation/compare_probe_templates.py --out validation/probe_comparison.json
"""
import argparse
import hashlib
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PROBE = ("/home/freiburger/Documents/prFBA/region_validation/shared_reference/data/"
         "egc_analysis/templates_scope/ccp_gapn_mdg")
FILES = ("GramNegModelTemplateV7.json", "GramPosModelTemplateV7.json",
         "ArchaeaTemplateV6.json", "Core-V6.json")
SEVEN = {"rxn00014", "rxn23850", "rxn05746", "rxn08933", "rxn08934", "rxn08935", "rxn08936"}
KEYS = {"direction", "GapfillDirection", "lower_bound", "maxrevflux"}


def canon(x):
    return json.dumps(x, sort_keys=True).encode()


def compare(a, b):
    """-> dict describing every difference between parsed templates a and b"""
    out = {"top_level_keys_differing": sorted(
        k for k in set(a) | set(b) if k != "reactions" and canon(a.get(k)) != canon(b.get(k)))}
    ia, ib = [r["id"] for r in a["reactions"]], [r["id"] for r in b["reactions"]]
    out["reaction_ids_equal"] = ia == ib
    out["n_reactions"] = [len(ia), len(ib)]
    rb = {r["id"]: r for r in b["reactions"]}
    diff = {}
    for r in a["reactions"]:
        s = rb.get(r["id"])
        if s is None or canon(r) != canon(s):
            diff[r["id"]] = (sorted(k for k in set(r) | set(s or {})
                                    if canon(r.get(k)) != canon((s or {}).get(k)))
                             if s is not None else "missing")
    out["reactions_differing"] = diff
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-commit", default="21a8084")
    ap.add_argument("--probe", default=PROBE)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    res = {"base_commit": subprocess.run(["git", "rev-parse", args.base_commit], cwd=REPO,
                                         check=True, capture_output=True,
                                         text=True).stdout.strip(),
           "probe_dir": args.probe, "files": {}}
    all_ok = True
    for f in FILES:
        raw = open(os.path.join(REPO, "templates", "v7.0", f), "rb").read()
        new = json.loads(raw)
        old = json.loads(subprocess.run(["git", "show", "%s:templates/v7.0/%s" % (
            args.base_commit, f)], cwd=REPO, check=True, capture_output=True).stdout)
        praw = open(os.path.join(args.probe, f), "rb").read()
        probe = json.loads(praw)
        vs_base = compare(old, new)
        expected = {} if f == "Core-V6.json" else None
        ok_base = (not vs_base["top_level_keys_differing"] and vs_base["reaction_ids_equal"]
                   and {k.rsplit("_", 1)[0] for k in vs_base["reactions_differing"]}
                   == (set() if expected == {} else SEVEN)
                   and len(vs_base["reactions_differing"]) == (0 if expected == {} else 7)
                   and all(set(v) == KEYS for v in vs_base["reactions_differing"].values()))
        vs_probe = compare(probe, new)
        ok_probe = (not vs_probe["top_level_keys_differing"] and vs_probe["reaction_ids_equal"]
                    and not vs_probe["reactions_differing"])
        res["files"][f] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "probe_sha256": hashlib.sha256(praw).hexdigest(),
            "whole_file_bytes_equal_probe": raw == praw,
            "vs_base": vs_base, "vs_base_ok": ok_base,
            "vs_probe": vs_probe, "reaction_level_equal_probe": ok_probe}
        all_ok &= ok_base and ok_probe
        print("%-30s base-diff ok=%s (%d reactions differ)  probe: reaction-level equal=%s, "
              "whole-file bytes equal=%s" % (f, ok_base, len(vs_base["reactions_differing"]),
                                             ok_probe, raw == praw), flush=True)
    res["all_ok"] = all_ok
    if args.out:
        with open(args.out, "w") as fh:
            json.dump(res, fh, indent=1, sort_keys=True)
            fh.write("\n")
    print("all_ok", all_ok)
    raise SystemExit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
