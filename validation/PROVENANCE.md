# Provenance of the seven-reaction validation

Recorded 2026-10-29, before stage a and stage b ran. Every hash here was read from the
checkouts and files named, on this machine.

## Templates

| What | Where | Commit |
|---|---|---|
| this branch, `fix-draft-atp-loops` | worktree `/home/freiburger/Documents/ModelSEEDTemplates-draftloops` | template change `7fd1ab19a866ce0f85a8a192773cbfb2bc00175f` |
| parent: the five-reaction fix (`fix-irreversible-reaction-directions`) | detached clone `/home/freiburger/Documents/ModelSEEDTemplates-c12run` | `21a808428560c1e3e11e304512d0baab6616ab78` |

`templates/v7.0` file sha256 on this branch (`7fd1ab1`):

| File | sha256 | Same bytes as |
|---|---|---|
| GramNegModelTemplateV7.json | `97d7fa40fa6afd56088c43066ee6f82fa0ff73786284dbe80430e4121762788a` | the probe (`ccp_gapn_mdg`) |
| GramPosModelTemplateV7.json | `3b1b3a42c0f8aa61b10e6b00788a12126f34d327368f672b35a2a506bcf2a5b8` | the probe |
| ArchaeaTemplateV6.json | `cebc7ba396219d8f03ce07e1fd2b6932b983c49827a06e829b72a702ca40f045` | none: indent=4 here, single-line in the probe; reaction-level equal |
| Core-V6.json | `22f82b02be39b40da402f3268f5589f2ea9a7ebb8b689eb684df232fd17d8f7a` | 21a8084 and the probe (unchanged) |

On 21a8084 (`ModelSEEDTemplates-c12run/templates/v7.0`, as A-C13's summary records):
GramNeg `d4c8ec4a…`, GramPos `8c96f43e…`, Archaea `db83de02…`, Core `22f82b02…`.

The probe templates are prFBA's
`region_validation/shared_reference/data/egc_analysis/templates_scope/ccp_gapn_mdg/`,
made by `scripts/egc_template_variants.py` from `ModelSEEDTemplates-c12run` (manifest.json
there). `validation/compare_probe_templates.py` checks this branch against them and
against 21a8084; its output is `validation/probe_comparison.json` (`all_ok: true`).

## Code

| What | Where | Commit / version |
|---|---|---|
| prFBA (the harness) | `/home/freiburger/Documents/prFBA`, branch `hardware-aware-alignment-dispatch` | `9cdefbb32a8079f3915013b07f18a5fb033f80ec` |
| ModelSEEDpy (pin) | detached clone `/home/freiburger/Documents/ModelSEEDpy-c2e31a0`, first on `PYTHONPATH` | `c2e31a0c775eba831a74cc89ed0774f3a3a62fe6`, no tracked file changed |
| cobrakbase | `/home/freiburger/Documents/cobrakbase` (venv editable) | `5e4eedb8363f28471ba81b984f6788308b9138ce`, no tracked file changed |
| ModelSEEDDatabase (`--msd` default) | `/home/freiburger/Documents/ModelSEEDDatabase` | `e8446e3ec2059ba31c38f694dc8cc783028f110a` |
| Python | `/home/freiburger/Documents/py_venv/bin/python` | 3.12.3; cobra 0.29.1, optlang 1.9.1, gurobipy 13.0.1, orjson 3.11.7 |

Both harness runs pass `--expect-modelseedpy c2e31a0`, so they stop unless ModelSEEDpy is
imported from a clean checkout of that commit, and they record `meta.libraries`.

The harness files, all unmodified against prFBA `9cdefbb` when recorded
(`validation/harness.sha256`; `chain_tmpl7.sh` checks them before it runs):

| File | sha256 | Last commit touching it |
|---|---|---|
| `region_validation/shared_reference/scripts/phenotype_fold.py` | `defa403b…` | `f980fd8` |
| `region_validation/shared_reference/scripts/egc_scope_scan.py` | `531f9a32…` | `f980fd8` |
| `region_validation/shared_reference/scripts/c12_compare.py` | `2a1f7b66…` | `41bcfc1` |
| `region_validation/picrust2_comparison/scripts/phenotype_arm.py` | `0d3342ee…` | `b4f9db1` |

`phenotype_fold.py` and `phenotype_arm.py` have the sha256 that A-C13's
`phenotype_summary.json` records in `meta.binding.code`, so stage b runs the same harness
code as the reference.

## Inputs (prFBA `region_validation/shared_reference/data/`, as A-C13 used them)

| File | sha256 |
|---|---|
| `cells.csv.gz` | `ffc9d3a73f4d11638a9ee336fdc0d4bde00fe7c038d0687b7a96b9b71e662ec3` |
| `fold_plan.json` | `fdc8734a7302dac89e97b2d350f5eae384e9a22b78b66b38d852a10362bdb8f3` |
| `panel_eligible.json` | `6eafdc5eb464af2f1c582f35d128c6d72235e49a5c390bb4b979c6a8cb2dc310` |
| `panel_ec_universe.json` | `4e9da0800802cdd7c78f73491203196bade25b2ddffa473adc62e166bee95ca2` |
| `../../picrust2_comparison/data/genome_function_sets.json` (`--functions` default) | `6f4f817ced5582a5fde36adcc9bb29f178a04aebd781f27fc81179603f95a95e` |

`prfba/` and `picrust2/` are read by the harness, which lists every predictions file it
used in the summary's `meta.prfba_runs` and `meta.picrust2_runs`.

## Reference run: amendment A-C13 (gapfilled pass)

- Output: prFBA `data/phenotype_gf_c13/` (`per_genome.jsonl` sha256
  `ccf6bbf34702b1cca57a532e0086f7c7efc093c7d938ea338661bb35badc7a64`, 8,614 rows;
  `phenotype_summary.json` sha256
  `e26c23c1f8a7103b127c13057f2663016e148c5598a41a25a34e46bac8c9a6f8`).
- Same library (c2e31a0), same `--integrate-reversals`, same inputs and harness code;
  templates 21a8084 (`ModelSEEDTemplates-c12run`).
- Run as systemd unit `c13-gf`: 16 workers, `--maxtasksperchild 3`, 10:15:06 to 13:09:53
  on 2026-10-29. The journal records "Consumed 1d 20h 10min 53.342s CPU time, 79.4G
  memory peak".

So stage b differs from the reference in the templates alone, and in the worker count
(10 against 16), which does not change rows (`phenotype_fold.py --maxtasksperchild` help:
"rows do not depend on which worker builds a genome").

Stage a's reference rows are prFBA `data/egc_analysis/scope_scan_200.jsonl` (21a8084,
ModelSEEDpy d884a50) and `scope_scan_variants.jsonl` (the probe `ccp_gapn_mdg`, d884a50).
C12_SCOPE.md section 1 found the leak flags and empty-medium ATP the same on d884a50 and
c2e31a0, for all 2,362 drafts scanned on both.
