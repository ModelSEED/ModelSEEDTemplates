# Validating the seven-reaction direction fix through gapfilling

Branch `fix-draft-atp-loops` restricts seven template reactions to their forward
direction, on top of `21a8084` (the five-reaction fix, branch
`fix-irreversible-reaction-directions`):

| Reaction | Enzyme | Database direction |
|---|---|---|
| rxn23850 | GAPN, non-phosphorylating G3P dehydrogenase | `>` (dG'0 −9.75 kcal/mol) |
| rxn05746 | maltodextrin glucosidase (maltotriose) | `?` |
| rxn08933 | maltodextrin glucosidase (maltotetraose) | `>` |
| rxn08934 | maltodextrin glucosidase (maltopentaose) | `>` |
| rxn08935 | maltodextrin glucosidase (maltohexaose) | `>` |
| rxn08936 | maltodextrin glucosidase (maltoheptaose) | `?` |
| rxn00014 | cytochrome c peroxidase | `?` |

The database directions are from ModelSEEDDatabase `e8446e3e`
(`Biochemistry/reaction_*.tsv`, column `reversibility`). The commit message of `7fd1ab1`
gives the thermodynamic case for each reaction.

prFBA's draft-level scan (`C12_SCOPE.md` sections 2b, 3 and 7 in
prFBA `region_validation/shared_reference/`) found that these seven changes cut the raw
drafts that make ATP from nothing from 849 to 95 of 1,181. That scan did not gapfill.
This directory checks the change through ATP correction and gapfilling, on prFBA's
200-genome gapfilled pass, against amendment A-C13 (same library, templates 21a8084).

## The plan

1. **The template change** (`apply_draft_loop_fix.py`, commit `7fd1ab1`).
   - For each of the seven reactions in GramNeg v7, GramPos v7 and Archaea v6
     (`templates/v7.0`), it sets direction and GapfillDirection to `>`, lower_bound to 0
     and maxrevflux to 0.0, as 21a8084 does for a `=` reaction. Core-V6 holds none of them.
   - It writes each file in its existing serialization, so the diff touches only these
     reactions: `json.dumps` default on one line for GramNeg, GramPos and Core, indent 4
     for Archaea, no trailing newline. It checks first that this reproduces the current
     bytes.
   - `--check` verifies only.
2. **The check against the probe templates** (`compare_probe_templates.py`, output
   `probe_comparison.json`).
   - Against 21a8084: exactly the seven reactions differ in each genome-scale file, in
     exactly the four fields. Nothing else differs.
   - Against prFBA's probe templates (`ccp_gapn_mdg`): every reaction and every other
     top-level field is byte-identical after parsing, in all four files.
   - GramNeg, GramPos and Core are also byte-identical as whole files. Archaea differs only
     in whitespace, because the probe was written on one line.
3. **Stage a: the draft-level scan** on this branch and on 21a8084 (unit `tmpl7-chain`).
   - prFBA `scripts/egc_scope_scan.py`, as `scripts/egc_scope_chain_pinned.sh` runs it,
     with `--expect-modelseedpy c2e31a0` and 4 workers.
   - It covers every (genome, arm) draft of the 200-genome gapfilled pass (1,181 drafts),
     with nothing gapfilled.
   - Output: `scan/scope_scan_tmpl7.jsonl`, summarized by `scan_summary.py` into
     `scan/scan_summary.json`.
   - The summary cross-checks the rows against prFBA's own scans, which ran on d884a50:
     this branch against the probe rows, and 21a8084 against `scope_scan_200.jsonl`.
4. **Stage b: the 200-genome gapfilled pass** (same unit, after stage a).
   - prFBA `scripts/phenotype_fold.py` exactly as amendment A-C13 ran it, except that
     `--templates` is this worktree's `templates/v7.0` and there are 10 workers, not 16.
   - Output: `gf_pass/per_genome.jsonl`, `gf_pass/phenotype_summary.json` and
     `gf_pass/identity_control.json`.
   - Then `compare_gf_to_c13.py` writes `gf_pass/compare_vs_c13.json`: per row, the gate,
     growth, gapfill burden, reversals, whether any of the seven reactions is in a
     solution, and the core ATP vector.
   - prFBA's own `scripts/c12_compare.py` writes `gf_pass/c12_compare_vs_c13.json`.

What to read off, for the analyst:
- **Draft level:** leaking drafts on this branch against 21a8084. The row-for-row
  agreement with the probe scan should be exact.
- **C12 gate:** A-C13 gated 0 of 8,614 rows. New gate failures here would mean the change
  opens a loop that gapfilling uses.
- **Growth:** every A-C13 model grows. Any model that stops growing is a cost of the
  change.
- **Burden and essentiality:** gapfill burden, essentiality and the vs-truth readouts,
  per arm. The method-arm medians are what the paper reports.
- **ATP readout:** the core ATP vector uses Core-V6, which this branch leaves unchanged,
  so it should match A-C13 row for row.

## Files

| File | What it is | Committed |
|---|---|---|
| `apply_draft_loop_fix.py` | makes the template change; `--check` verifies it | yes, with the templates (`7fd1ab1`) |
| `compare_probe_templates.py`, `probe_comparison.json` | the check against 21a8084 and the probe | yes |
| `chain_tmpl7.sh` | the unit body: pre-checks, stage a, scan summary, stage b, comparisons | yes |
| `launch_tmpl7.sh` | the exact `systemd-run` launch of unit `tmpl7-chain` | yes |
| `harness.sha256` | sha256 of the prFBA harness files; `chain_tmpl7.sh` checks them | yes |
| `scan_summary.py` | stage a summary and the cross-check against prFBA's scans | yes |
| `compare_gf_to_c13.py` | stage b per-row comparison with A-C13 | yes |
| `PROVENANCE.md` | the commits, file hashes and reference run | yes |
| `smoke_2genomes/` | the 2-genome smoke of stage b and its comparison | no (run output) |
| `scan/`, `gf_pass/`, `logs/` | stage a and b outputs and logs | no; the analyst commits them |

## How to reproduce

```bash
WT=/home/freiburger/Documents/ModelSEEDTemplates-draftloops
PY=/home/freiburger/Documents/py_venv/bin/python
# the template change, from 21a8084
git -C /home/freiburger/Documents/ModelSEEDTemplates worktree add $WT -b fix-draft-atp-loops 21a8084
$PY $WT/validation/apply_draft_loop_fix.py
$PY $WT/validation/compare_probe_templates.py --out $WT/validation/probe_comparison.json
# stages a and b, as one systemd user unit (tmpl7-chain)
bash $WT/validation/launch_tmpl7.sh
```

`chain_tmpl7.sh` stops before stage a if any of these fails:
- the templates differ from `7fd1ab1`;
- `ModelSEEDTemplates-c12run` is not a clean 21a8084;
- `PYTHONPATH` is not the c2e31a0 pin;
- the prFBA harness files differ from `harness.sha256`.

To run the pre-checks alone, without either stage: in prFBA's
`region_validation/shared_reference`, run `TMPL7_PRECHECK_ONLY=1
PYTHONPATH=/home/freiburger/Documents/ModelSEEDpy-c2e31a0 $WT/validation/chain_tmpl7.sh`.

A failure in stage a does not skip stage b. If stage b is interrupted, relaunching
resumes it: `phenotype_fold.py` keeps the rows already in `gf_pass/per_genome.jsonl` and
builds only the genomes they do not cover.

The stage b command, for reference (working directory prFBA
`region_validation/shared_reference`, `PYTHONPATH=/home/freiburger/Documents/ModelSEEDpy-c2e31a0`,
`D=$PWD/data`):

```bash
$PY -W ignore::SyntaxWarning scripts/phenotype_fold.py --cells $D/cells.csv.gz \
  --fold-plan $D/fold_plan.json --panel $D/panel_eligible.json --prfba $D/prfba \
  --picrust2 $D/picrust2 --templates $WT/templates/v7.0 --integrate-reversals \
  --expect-modelseedpy c2e31a0 --outdir $WT/validation/gf_pass \
  --summary $WT/validation/gf_pass/phenotype_summary.json --n-genomes 200 \
  --readouts atp,growth,essentiality,structure --workers 10 --maxtasksperchild 3
```

## Resources

One unit, `tmpl7-chain`, runs stage a and then stage b, with `MemoryMax=77G` and
`MemorySwapMax=0`. The cap is set by stage b: its estimated 59 GB peak, plus 30%.
`launch_tmpl7.sh` refuses to start unless MemAvailable is at least 89 GB (77 + 12).

| Stage | Workers | Estimated peak | Estimated duration |
|---|---|---|---|
| a, draft-level scan | 4 | 35 GB | 0.2 h (0.3 h under heavy load) |
| b, gapfilled pass | 10 | 59 GB | 4.7 h; 7.3 h at the smoke's per-genome speed |

**How the stage b numbers were made.**
- **Parent process** (measured in the smoke, by polling `/proc/<pid>/status`): its RSS
  peaks at 16.6 GiB while it loads the inputs, then holds at 15.0 GiB. It parses the
  1.7 GB `genome_function_sets.json` and the prediction blocks, and keeps them.
- **Workers:** each smoke worker built one genome and peaked at 2.3 and 2.9 GiB RSS.
  - A-C13 ran 16 workers that built up to 3 genomes each (`--maxtasksperchild 3`).
  - Its journal records a 79.4G peak; the orchestrator's note gives about 85 GB.
  - From 85 GB, each worker took (85 − 15)/16 = 4.4 GB.
- **Peak at 10 workers:** 15 + 10 × 4.4 = 59 GB. From the smoke alone it would be
  16.6 + 10 × 2.9 = 45 GB, a lower bound.
- **Duration:**
  - A-C13's 200 per-genome walls sum to 154,880 s. Its run took 2.91 h (10:15:06 to
    13:09:53), 1.083 times the ideal 154,880 s / 16 workers.
  - At 10 workers that gives 154,880 / 10 × 1.083 = 4.66 h.
  - In the smoke, the two genomes took 1.55 and 1.61 times their A-C13 walls (616 against
    399 s, 758 against 472 s). The load average was about 60, from other jobs, so the
    template change's own effect on time cannot be told apart. At that speed the pass
    takes 7.3 h.

**Stage a** was not smoke-tested. `egc_scope_scan.py` takes `--only-genomes` but never
applies it, so any run is a full 200-genome scan.
- **Duration:** two earlier scans of the same 1,181 drafts on two template directories,
  with 4 workers, took 11.7 min (`c12-scope-scan`) and 9.6 min (`egc-scope-var`), from
  their journal start and stop times.
- **Memory:** the journal records a 16.3G peak for `egc-scope-pin` (scan plus loop
  enumeration). The orchestrator's note gives about 35 GB. The scan's parent loads the
  same inputs as stage b's (16.6 GiB in the smoke), so 16.3G looks low.
  - The journal's peaks also understate: it recorded "2.1G memory peak" for the smoke,
    whose cgroup `memory.peak` read 24.57 GiB during the run.
  - The table therefore uses 35 GB. That is below stage b's estimate, so it does not set
    the cap.

**If a worker is OOM-killed,** Python's `multiprocessing.Pool` can wait forever for the
lost task instead of failing. Watch `logs/stage_b_gf_pass.log` for progress. Rows already
written are kept, and a relaunch resumes from them.

## Smoke test of stage b

Run on 2026-10-29 as unit `tmpl7-smoke` (18:46:24 to 19:03:10). It used stage b's command
with `--only-genomes 1188229.3,3038979.9`, 2 workers and the output in the session
scratchpad; a copy is in `smoke_2genomes/` (not committed).
- **The genomes.** 1188229.3 is GramNeg: 4 of its drafts still leak on the new templates.
  3038979.9 is GramPos: all its drafts stop leaking (from prFBA's probe scan,
  `scope_scan_variants.jsonl`).
- **Provenance in the summary.** `meta.templates` is this worktree at `7fd1ab1`, with the
  sha256 in `PROVENANCE.md`. `meta.libraries` records ModelSEEDpy `c2e31a0` and
  `integrate_reversals` is true.
- **Rows.** All 72 rows are `ok`. 20 are gapfilled models (5 arms × 2 pipelines × 2
  genomes); the 52 ladder rows are not gapfilled.
- **Sanity gate:** all 20 gapfilled models pass, as in A-C13.
- **Growth:** all 20 grow, as in A-C13.
  - The growth ratio to A-C13 has a median of 1.000, ranging from 0.955 to 1.308.
  - One model moves by more than 10%: 3038979.9 base_constant controlled, 3.430 to 4.486.
- **Gapfill burden:** it changes in 15 of the 20 models, by a mean of +0.2 reactions.
- **Reversals:** none applied, as in A-C13.
- **The seven reactions:** none appears among the gapfilled or reversed reactions.
- **ATP readout:** the core ATP vectors are identical to A-C13 in all 72 rows.
- **C11:** the identity control passes (Jaccard 1.0).

**Memory.**
- A first attempt at `MemoryMax=15G` was stopped at 18:44 after about 70 s. The parent
  alone needed more than 15 GiB while loading, and the unit swapped 1.2 GB.
- The rerun had `MemoryMax=28G` and `MemorySwapMax=0`. It peaked at cgroup
  `memory.peak` 24.57 GiB, of which about 6.8 GB was page cache. Peak anon was 19.22 GiB
  and peak summed RSS 19.55 GiB.
