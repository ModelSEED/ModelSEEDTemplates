# The seven-reaction direction fix through prFBA's gapfilling harness: results

2026-11-02. Branch `fix-draft-atp-loops`: template change `7fd1ab1`, validation scripts
`1f84188`, both on top of the five-reaction fix `21a8084`. Reference: amendment A-C13 (prFBA
`region_validation/shared_reference/C12_SCOPE.md` section 7), the same 200-genome gapfilled
pass on templates `21a8084` and ModelSEEDpy `c2e31a0`. How the runs went, including the OOM
kill and the resume, is in `PROVENANCE.md`.

## Conclusion

**The seven edits are safe to adopt.** Through ATP correction and gapfilling, on all 200
genomes (8,614 rows), they cost nothing measurable:
- no model fails the C12 gate (0 of 8,614 rows, as in A-C13);
- every gapfilled model still grows (2,362 of 2,362);
- the ATP vectors are identical in every row;
- the C11 identity control passes;
- the gapfill burden changes by a mean of +0.013 reactions;
- no method arm's median moves by more than 0.004 on essentiality or growth, or by more
  than one reaction on burden;
- none of the comparisons the prFBA paper draws changes.

At the draft level the edits stop 770 of 865 leaking drafts from making ATP from nothing,
and they make no draft start.

The growth changes they cause sit at the gapfiller's normal noise level, apart from two
models. Those two lose a large growth excess (section 3.3).

**What this does not cover.**
- The 1,000-genome ATP pass was not rerun on these templates. Its readouts are expected to
  be unchanged: the ATP vector comes from Core-V6, which the edits leave alone, and the
  draft reaction sets do not change. Here both held in all 8,614 rows.
- The validation uses prFBA's pipeline only: MSATPCorrection, then MSGapfill on complete
  medium. A pipeline that skips ATP correction, or that gapfills on minimal media, is
  untested.
- 95 drafts still leak, through a different, long-tail family of loops (C12_SCOPE
  section 2b).
- v5.0 and v6.0 carry the same seven `=` entries; they are not edited (commit message of
  `7fd1ab1`).

## 1. What the seven edits change, and why

Each reaction is `=` in GramNeg v7, GramPos v7 and Archaea v6 (`templates/v7.0`). Each is
now forward-only, edited the way `21a8084` edits a `=` reaction: `direction` and
`GapfillDirection` set to `>`, `lower_bound` to 0 and `maxrevflux` to 0.0. Core-V6 holds
none of them.

Run backwards, each is one step of an energy-generating cycle. With that cycle, a raw draft
makes ATP with every uptake closed and only water and protons free.

| Reaction | Enzyme | Loop it closes when reversed | Database direction |
|---|---|---|---|
| rxn23850 | GAPN, non-phosphorylating G3P dehydrogenase | with GAPDH rxn00781 and PGK rxn01100: ATP from ADP and Pi | `>` (ΔG'° −9.75 kcal/mol, GOLD) |
| rxn05746, rxn08933–rxn08936 | maltodextrin glucosidase (maltotriose to maltoheptaose) | with maltodextrin phosphorylase, phosphoglucomutase and glucokinase run backwards | `>` for rxn08933–rxn08935; `?` for rxn05746 and rxn08936 |
| rxn00014 | cytochrome c peroxidase | H2O2 from water and ferricytochrome c; catalase (forward since `21a8084`) and cbb3 oxidase then pump protons | `?` (no direction or free energy) |

- **GAPN.** The database direction is `>`, GOLD-graded. In C12_SCOPE section 2 GAPN is the
  smallest loop in 130 of the 136 leaking truth drafts.
- **The glucosidases.** Hydrolysis of a glycosidic bond is irreversible. Run backwards, the
  reaction would make that bond from free glucose.
- **rxn00014.** The reverse reaction is uphill by about 212 kJ/mol (2F × 1.10 V; commit
  message of `7fd1ab1`). It is the one loop that `21a8084` opens in drafts (C12_SCOPE
  section 3).

The database directions are from ModelSEEDDatabase `e8446e3e` (README). The thermodynamics
are in the commit message of `7fd1ab1`.

**Checks that the diff is exactly this** (`probe_comparison.json`, `all_ok: true`).
- Against `21a8084`, exactly the seven reactions differ in each genome-scale file, in exactly
  the four fields; Core-V6 differs in nothing.
- Against prFBA's probe templates (`ccp_gapn_mdg`), every reaction is identical.
- `apply_draft_loop_fix.py --check` exits 0 (`logs/precheck_templates.json`).
- `git diff --stat 21a8084 7fd1ab1 -- templates/` gives 30 insertions and 30 deletions:
  1 line each in the single-line GramNeg and GramPos files, and 56 in the indent-4 Archaea
  file.

## 2. Stage a: draft-level leaks, before and after

prFBA's `egc_scope_scan.py` was run on every (genome, arm) draft of the 200-genome pass, with
nothing gapfilled, on this branch and on `21a8084` (source: `scan/scan_summary.json`).

| | `21a8084` | this branch |
|---|---|---|
| leaking drafts (of 1,181) | 865 (73.2%) | **95 (8.0%)** |
| leaking truth drafts (of 200) | 138 | 21 |
| leaks at the 1,000 ATPM bound | 833 | 53 |
| genomes with a leaking draft (of 200) | 200 | 35 |
| drafts making biomass from nothing | 0 | 0 |
| errors | 0 | 0 |

**By template:**
- Archaea: 98/142 → 3/142;
- GramNeg: 387/515 → 72/515;
- GramPos: 380/524 → 20/524.

**By arm:**
- constant baseline: 200/200 → 0/200;
- prFBA: 141/200 → 26/200;
- truth: 138/200 → 21/200;
- nn1: 139/200 → 24/200;
- PICRUSt2: 136/200 → 8/200;
- family donor: 111/181 → 16/181.

**Transitions per draft** (`transitions_21a8084_to_tmpl7`): 770 stop leaking and 0 start
leaking. 95 leak on both templates and 316 on neither.

**Cross-check against prFBA's scans** (`vs_prior`). This branch against the probe rows,
and `21a8084` against `scope_scan_200.jsonl`:
- all 1,181 drafts match in each case, with 0 differences in leak flag or empty-medium ATP;
- `n_rxn` differs in all 1,181. Those scans ran on ModelSEEDpy `d884a50`, whose drafts
  carry different demand reactions (C12_SCOPE section 1).

**A correction to the commit message and README.** Both say the edits cut the leaking
drafts "from 849 to 95". 849 is the probe with rxn00014 alone restricted (C12_SCOPE section
2b). Against the parent `21a8084` the cut is **865 → 95**, which is what the PR text uses.

## 3. Stage b against A-C13

`phenotype_fold.py` ran exactly as A-C13 ran it, with two differences: `--templates` is
this branch, and there are 10 workers instead of 16.

**Sources:**
- `[cmp]` `gf_pass/compare_vs_c13.json` (`compare_gf_to_c13.py`);
- `[c12]` `gf_pass/c12_compare_vs_c13.json` (prFBA `c12_compare.py`);
- `[rows]` `gf_pass/report_rows.json`, written by `report_rows.py` (added with this
  report). It holds every figure the first two do not state.

### 3.1 Rows

**The rows match.** There are 8,614 rows, all `ok`, matched one to one with A-C13's 8,614,
with no row missing on either side `[cmp]`.

**Of these, 2,362 are gapfilled models:** 6 arms × 2 pipelines × 200 genomes, less 19
genomes without a family donor. The other 6,252 are ladder rows, which are not gapfilled
`[cmp]`.

**What does not change** `[rows]`:
- the draft block (reaction, gene and metabolic-reaction counts), in all 8,614 rows;
- the ladder rows, apart from wall time.

The edits change directions, not which reactions a draft holds.

### 3.2 C12 gate and C11 identity control

**C12 gate:** 0 gated rows, against 0 in A-C13, so there is no new gate failure.
- By `gapfilled.sanity_gate_ok`, over the 2,362 gapfilled rows: `gated_after` 0,
  `new_gate_failures` 0 `[cmp]`.
- By row status `gated`, over all 8,614 rows: 0 before and 0 after, in every arm and ladder
  rung. That holds in the 20 genomes that held C12's original 49 gated rows and in the other
  180 `[c12]`.
- `meta.n_gated_out` is empty (`gf_pass/phenotype_summary.json`).

**ATP empty-medium gate:** passes in every row; no row makes ATP on the empty medium
`[rows]`.

**C11:** passes. `gf_pass/identity_control.json` reads `pass: true`, `jaccard: 1.0`,
`atp_identical: true` and `gapfill_identical: true`.

### 3.3 Growth

**No model stops growing.** All 2,362 gapfilled models grow in both runs
(`growing_after` = `growing_before` = 2,362 `[cmp]`; `non_growing_after` 0 `[c12]`). The
lowest growth is 0.0309 in both `[rows]`.

**Growth ratio, this branch over A-C13** (2,362 models; `[cmp]`, quantiles `[rows]`):

| min | p1 | p5 | p25 | median | p75 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|---|
| 0.129 | 0.645 | 0.939 | 0.999 | 1.000 | 1.000 | 1.049 | 2.733 | 2.733 |

- 499 ratios are exactly 1, and 1,875 are within 1%.
- 204 models move by more than 10%: 99 up and 105 down. The median |log ratio| is 0.0006.

**Most of the 204 movers are one arm, toggling between solutions** `[rows]`.
- **The constant baseline holds 164 of the 204**, 82 up and 82 down.
  - It uses one EC set for all the genomes of a fold. In each of its 14 (fold, template)
    groups its drafts have one EC count and one draft size.
  - Its 400 gapfilled rows are only 93 distinct models by (template, pipeline, growth,
    burden) (`base_constant_drafts`).
  - Its 164 movers come from 14 of its 28 (fold, template, pipeline) groups and collapse to
    19 distinct (before, after) growth pairs.
- **Several of those pairs are swaps.** 33 rows go 2.233 → 3.458 while 27 go
  3.457 → 2.233, and 5 go 4.455 → 5.024 while 5 go 5.025 → 4.456. These are alternative
  gapfill solutions, not a drift in one direction.
- **The other five arms hold 40 movers, in 24 genomes.** By arm: truth 10, nn1 9, family
  donor 8, PICRUSt2 7, prFBA 6.
- **In the controlled pipeline the paper reports, the five arms hold 15 movers** (truth 5,
  prFBA 3, family donor 3, PICRUSt2 2, nn1 2), against 51 for the constant baseline.

**The baseline for comparison is A-C13 against A-C12, a ModelSEEDpy update with no template
change.** It moved 87 models by more than 10% and changed the gapfill solution in 2,263 of
2,362 models `[rows]`. The edits changed 2,271 solutions. In both cases the median solution
changes by 6 reactions (section 3.5). So the gapfiller's churn is at its usual level, and
the excess movers are the constant baseline's duplicated models.

**Where the movers are, by draft-level leak transition** (stage a; `[rows]`):

| | movers, all arms | movers, without the constant baseline |
|---|---|---|
| drafts that stopped leaking | 191 of 1,540 models | 27 of 1,140 |
| drafts leaking on both templates | 9 of 190 | 9 of 190 |
| drafts leaking on neither | 4 of 632 | 4 of 632 |

Growth moves most where the edits removed or touched a draft-level loop. It almost never
moves where neither template leaked.

**Two models lose a large growth excess.** Each drops more than twofold, in both pipelines
`[rows]` `changed_more_than_twofold`:

| Model | Growth, A-C13 → this branch | rxn05746 essential | Solution change |
|---|---|---|---|
| 2024824.75 truth | 16.60 → 2.21 (both pipelines) | before, not after | 6 reactions |
| 229919.9 family donor | 10.75 → 1.38 (as shipped); 11.35 → 1.49 (controlled) | before, not after | 6 reactions each |

- **2024824.75.** In A-C13 its truth model was the outlier: the other five arms grew 2.23
  to 4.72 (controlled). Its arms' log10 growth ratio to truth goes from −0.87 to −0.55 to
  between +0.005 and +0.33 `[rows]` `large_drop_genomes_controlled`.
- **229919.9.** The family-donor model's ratio to truth goes from +0.49 to −0.40. The truth
  model (3.69 → 3.72) and the other arms barely move.
- **Mechanism.** The files show only that rxn05746, a maltodextrin glucosidase, was
  essential in both models before and is not after, and that their gapfill solutions
  changed. They hold no fluxes, so they cannot show in which direction rxn05746 carried
  flux before.
- **No arm median moves** because of them (section 4).

The 37 models whose growth more than doubles are 35 constant-baseline rows and 2 PICRUSt2
rows `[rows]`.

### 3.4 Gapfill burden

Burden is the number of gapfilled reactions, `n_new_rxn` (`[cmp]`, `[c12]`, detail
`[rows]`):
- it changes in 1,205 of 2,362 models: 628 up and 577 down;
- the mean change is +0.013 reactions and the median 0;
- it is within ±1 in 2,036 models and within ±2 in 2,268. 31 models move by 5 or more; the
  range is −22 to +36;
- in total, 201,150 reactions before and 201,180 after.
- **Per arm:** the change occurs in 185 to 222 models, with means from −0.110 (truth) to
  +0.113 (prFBA).
- **Against the 20 C12-flagged genomes:** the mean is +0.176 in those genomes and −0.006 in
  the other 180 `[c12]`.
- **Reference:** A-C13 against A-C12 changed the burden in 1,068 models, by a mean of
  +0.016 (C12_SCOPE section 7; `[rows]` `solutions`).

### 3.5 Gapfill solutions and essential sets

| | gapfill solution changed | essential set changed | median solution change |
|---|---|---|---|
| this branch vs A-C13 | 2,271 of 2,362 | 2,252 | 6 reactions (mean 6.82) |
| A-C13 vs A-C12 (reference) | 2,263 of 2,362 | 2,250 | 6 reactions (mean 6.97) |

Source: `[rows]` `solutions`.
- Under either change, nearly every model lands on a different solution of about the same
  size. This is consistent with a gapfill MILP that has many equal-cost alternatives.
- C11 shows that one input gives one solution.
- The edits add no churn beyond the reference.

### 3.6 Reversals

**Rows with a proposed reversal:** 111, against 114 in A-C13 (`reversal_applied_before`
114 and `_after` 111 `[cmp]`; `rows_with_reversals_proposed` = `_applied` = 111 `[c12]`).
- The harness applies every proposed reversal, in both runs `[rows]`.
- 109 rows have a reversal in both runs, 5 only in A-C13 and 2 only on this branch.

**Reversed reactions applied:** 122, against 127 `[rows]`.
- rxn00260: 37 against 42;
- rxn00347: 6 against 5;
- rxn00171: 0 against 1;
- unchanged: rxn05289 54, rxn00117 11, rxn00409 11, rxn02914 2, rxn00237 1.

### 3.7 The seven reactions in the final models

None of the seven appears in any gapfill solution or reversal, in either run
(`seven_in_solution_after` 0 `[cmp]`; 0 before and after `[rows]`).

Some are essential in the gapfilled models `[rows]`. The count falls from 51 models to 37:
- rxn05746: 40 → 30;
- rxn23850: 4 → 0;
- rxn00014: 7 → 7.

### 3.8 ATP vectors

**The core ATP vector is identical in all 8,614 rows** (`atp_vector_changed` 0 `[cmp]`).
The binary vectors are unchanged in every arm and rung `[c12]`.

**The summaries agree on ATP too** `[rows]` `summary_diff`. Every ATP statistic is equal,
in every arm, contrast, ladder and pipeline-effect leaf. This is expected: the readout uses
Core-V6, which this branch does not change.

### 3.9 Run time

The per-genome walls sum to 146,796 s, against A-C13's 154,880 s. The median per-genome
ratio is 0.986 `[rows]` `walls`. The edits do not slow the build.

## 4. Controlled medians per arm: this branch / A-C13

Sources:
- this branch: `gf_pass/phenotype_summary.json`;
- A-C13: prFBA `data/phenotype_gf_c13/phenotype_summary.json`;
- fields `arms.<arm>.controlled.{ess_shared_disagree_frac, growth_log_ratio,
  gapfill_burden}.median`, also in `[rows]` `medians`.

n is 200 per arm, and 181 for the family donor, in both. The format is C12_SCOPE
section 7's. The growth log-ratio is log10 of the model's growth over the truth model's
(`phenotype_fold.py`).

| Arm | Essentiality disagreement | Growth log-ratio to truth | Gapfill burden |
|---|---|---|---|
| truth | 0 / 0 | 0 / 0 | 81.5 / 82.5 |
| prFBA (exact tie) | 0.068 / 0.068 | 0.008 / 0.008 | 80 / 80 |
| PICRUSt2 | 0.065 / 0.065 | −0.003 / −0.006 | 83 / 84 |
| nn1 | 0.069 / 0.069 | 0.009 / 0.008 | 83.5 / 82.5 |
| family donor | 0.065 / 0.066 | 0.004 / 0.006 | 83 / 83 |
| constant | 0.092 / 0.090 | −0.129 / −0.134 | 72 / 72 |

**The method arms barely move:**
- essentiality by at most 0.0005 (nn1, 0.068848 against 0.069362);
- growth by at most 0.0035 (PICRUSt2, −0.002982 against −0.006455);
- burden by at most one reaction (PICRUSt2 −1, nn1 +1).

**The other two arms:**
- truth's burden falls by one reaction;
- the constant baseline moves by +0.0025 on essentiality and +0.0054 on growth.

**As shipped** `[rows]` `medians`: the method arms move by at most 0.0024 on essentiality
(prFBA) and 0.0016 on growth (PICRUSt2). Burden moves by at most 1.5 reactions (PICRUSt2,
84 → 82.5).

**Only these three readouts differ** `[rows]` `summary_diff`.
- The two summaries differ in 247 non-meta leaves, all in `arms` and `pipeline_effect`, all
  for essentiality, growth log-ratio or burden.
- `contrasts`, `ladders`, every ATP leaf and every reaction-Jaccard leaf are identical.
- In `meta`, they differ only in the templates, output paths and hashes, timestamps and
  prFBA commit.
- `meta.libraries` and `meta.binding.code` are equal.

## 5. Would any comparison in the prFBA paper change?

**No.** The paper reports A-C13 (`prFBA_paper/prFBA.tex`, branch `depth100-standard`,
`62fbaf1`, lines 569–573; `prFBA_andrew_voice.tex` has the same sentences). Against this
branch's medians:

| Paper (A-C13) | This branch | Comparison |
|---|---|---|
| PICRUSt2 disagrees on essentiality "marginally less often (median 0.065 against 0.068)" | 0.065 against 0.068 | holds, same figures |
| prFBA vs nn1 essentiality "0.068 against 0.069" | 0.068 against 0.069 | holds, same figures |
| growth log-ratio "0.008 against 0.008 (PICRUSt2 −0.006)" | 0.008 against 0.009 (PICRUSt2 −0.003) | holds ("indistinguishable") |
| "median 80 to 84 added reactions against 82.5" | 80 to 83.5 against 81.5 | holds ("about as much gapfilling as the truth model") |
| reaction Jaccard "0.707 against 0.705" | not touched | from the 1,000-genome ATP pass's drafts; direction edits do not change draft reaction sets, and every Jaccard leaf here is identical |
| pre-registered run "0.066 against 0.068, growth log-ratio 0.002 against 0.004" | not touched | a different run |

- **The ATP findings are not affected.** Every ATP vector and statistic is identical
  (section 3.8).
- **The paper never mentions the seven-reaction probe.**
- **The paper stays on A-C13**, and no sentence would need to change. If prFBA ever adopted
  these templates, only three figures would move, all at the third decimal or by one
  reaction: nn1's growth, PICRUSt2's growth and the burden range.

## 6. Files

| File | What it is | Tracked |
|---|---|---|
| `REPORT.md` | this report | yes (with this report) |
| `report_rows.py`, `gf_pass/report_rows.json` | the row-level figures sections 3 and 4 cite | yes |
| `PR_TEXT.md` | draft PR description for ModelSEEDTemplates | yes |
| `PROVENANCE.md` | commits, hashes, units, caps, timings, the OOM kill and the resume | yes (updated) |
| `chain_tmpl7_resume.sh` | the resume body run by `tmpl7-resume` and `tmpl7-resume2` | yes |
| `scan/` | stage a rows (2,362), meta sidecar and `scan_summary.json` | summary yes; rows gzipped |
| `gf_pass/` | stage b rows (8,614; 30.7 MB), summary, identity control, both comparisons, the 854-row OOM backup | summaries yes; rows gzipped |
| `logs/` | chain, stage and memory-trend logs, including the OOM-killed and stopped runs | yes |
| `smoke_2genomes/` | the 2-genome smoke | yes |

The row-level files (`gf_pass/per_genome.jsonl`, `per_genome.oom-2254.jsonl`,
`scan/scope_scan_tmpl7.jsonl`) are committed gzipped; their uncompressed sha256 values are in
`PROVENANCE.md`.

## 7. Discrepancies found while writing this

1. **"849 to 95".** The commit message of `7fd1ab1` and `README.md` compare with the
   rxn00014-only probe. Against `21a8084` the figure is 865 → 95 (section 2).
2. **rxn00014's free energy.** The commit message gives about 212 kJ/mol (2F × 1.10 V =
   212.3). C12_SCOPE section 2 and its PR note give about 214. This report and the PR text
   use 212.
3. **Stage b's memory.**
   - README "Resources" estimated a 59 GB peak, with 4.4 GB per worker.
   - At the OOM kill the ten workers held 5.7–6.8 GiB of anonymous memory each, and the
     unit reached its 77 GiB cap.
   - The resumed run peaked at 72.2 GiB under a 120 GiB cap (`PROVENANCE.md`).
   - README is left as written, as the pre-run record.
4. **The prFBA commit recorded in PROVENANCE.md (`9cdefbb`) is not the commit the runs
   used.**
   - The runs used `f8205be`, the summary was written at `c91cf19`, and prFBA is at
     `2abcd1a` on 2026-11-03.
   - None of these commits touches the four harness files, whose sha256 still verify
     (`PROVENANCE.md`).
