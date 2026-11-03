# Provenance of the seven-reaction validation

Recorded 2026-10-29, before stage a and stage b ran. Every hash here was read from the
checkouts and files named, on this machine. The section "What ran" at the end was added on
2026-11-02, after both stages had finished; it records the runs as they happened, which
differ from the plan in README.md (stage b ran in two parts, after an OOM kill).

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

## What ran (added 2026-11-02)

Sources: the user journal (`journalctl --user -u <unit>`), the kernel journal
(`journalctl -k`), the logs in `validation/logs/`, and the session's launch commands. All
times are CDT. The systemd sizes `77G` and `120G` are GiB.

### Units

| Unit | Body | Caps | Start | End | Result |
|---|---|---|---|---|---|
| `tmpl7-smoke` (1st) | stage b command, 2 genomes, 2 workers | `MemoryMax=15G` | 10-29 18:42:50 | 18:44:03 | stopped by hand. The parent needed more than 15 GiB while loading, and the journal records a 1.2G swap peak |
| `tmpl7-smoke` (2nd) | the same | `MemoryMax=28G`, `MemorySwapMax=0` | 10-29 18:46:24 | 19:03:10 | `EXIT=0`, 72 rows (README "Smoke test") |
| `tmpl7-gate` | waits until `gtdbtk-wetland.scope` is inactive (or 01:00–12:00), then runs `launch_tmpl7.sh` | `MemoryMax=1G` | 10-29 20:41:59 | launched at 22:12:00 | done. Its process is gone, and the journal holds no deactivation line |
| `tmpl7-chain` | `chain_tmpl7.sh`, launched by `launch_tmpl7.sh` | `MemoryMax=77G`, `MemorySwapMax=0` | 10-29 22:12:00 | 22:54:18 | **`Failed with result 'oom-kill'`**, after 5h 39min 52.696s CPU time. Stage a finished (exit 0); stage b was killed after 20 genomes |
| `tmpl7-resume` | `chain_tmpl7_resume.sh` (first version) | `MemoryMax=120G`, `MemorySwapMax=0` | 10-30 10:33:48 | 10:36:20 | stopped by hand after 2.5 min, with no genome finished. 5min 39.702s CPU time |
| `tmpl7-resume2` | `chain_tmpl7_resume.sh` (current version) | `MemoryMax=120G`, `MemorySwapMax=0` | 10-30 10:39:10 | 14:34:21 | `EXIT=0` (`logs/tmpl7_chain.log`): stage b exit 0, both post-steps exit 0. 1d 13h 59min 6.939s CPU time, "72.2G memory peak, 0B memory swap peak" |

**Common settings.** All units ran with `--collect`. `tmpl7-chain`, `tmpl7-resume` and
`tmpl7-resume2` also had
`WorkingDirectory=/home/freiburger/Documents/prFBA/region_validation/shared_reference` and
`PYTHONPATH=/home/freiburger/Documents/ModelSEEDpy-c2e31a0`, which `chain_tmpl7*.sh` check.

**The gate's own memory check printed an empty value.** Its journal reads "Referenced but
unset environment variable evaluates to an empty string: a", then "MemAvailable  GB:
launching". `launch_tmpl7.sh` then checked again and logged "MemAvailable 216 GB;
MemoryMax 77 GB; need 89 GB" before it launched. The GTDB-Tk scope it waited on had ended
at 22:08:57.

### Timeline of the two stages

**Stage a:** 10-29, 22:12:01 to 22:21:31 (9.5 min), exit 0 (`logs/tmpl7_chain.oom-2254.log`).
- It covered 1,181 drafts × 2 template directories, 2,362 rows (`scan/scope_scan_tmpl7.jsonl`).
- Both cross-checks against prFBA's scans match on every leak flag and empty-medium ATP
  (`logs/stage_a_summary.log`).

**Stage b, part 1** (`tmpl7-chain`): 10-29, 22:21:31 to the kill at 22:54:16.
- 20 genomes finished: 854 rows, with walls summing to 14,902 s.

**Stage b, part 2** (`tmpl7-resume2`): 10-30, 10:39:11 to 14:34:17 (3 h 55 min).
- The remaining 180 genomes finished, with walls summing to 131,893 s.
- It ended with "[pheno] wrote …/per_genome.jsonl (8614 rows)".

**Post-steps:** `compare_gf_to_c13.py` and prFBA's `c12_compare.py`, both exit 0, done
14:34:21.

**Total:** the per-genome walls sum to 146,796 s, against A-C13's 154,880 s. The median
per-genome ratio is 0.986 (`gf_pass/report_rows.json`, `walls`).

**One log, three segments.** `logs/stage_b_gf_pass.log` was appended to by each launch:

| Lines | Run | Its resume line | Genomes finished |
|---|---|---|---|
| 1–2141 | `tmpl7-chain` | line 5: "200 genomes selected, 0 already done, 200 to build" | 20; no final line (killed) |
| 2142–2158 | `tmpl7-resume` | line 2146: "200 genomes selected, 20 already done, 180 to build" | 0 (stopped) |
| 2159–18755 | `tmpl7-resume2` | line 2163: "200 genomes selected, 20 already done, 180 to build" | 180, then the final "wrote … (8614 rows)" line |

- Each segment logs ModelSEEDpy `c2e31a0` with "tracked files changed: False".
- The first two end with Python's resource-tracker warning about leaked semaphores, which
  their killed or stopped pools left behind (lines 2140–2141 and 2157–2158).

### The OOM kill (10-29 22:54)

**It was the unit's own cap.** The kernel journal at 22:54:15 records a memory-cgroup OOM
(`constraint=CONSTRAINT_MEMCG`) in `tmpl7-chain.service`.
- Usage was 80,740,352 kB against a limit of 80,740,352 kB, which is 77.0 GiB
  (`failcnt 12212`).
- Of that, 82,444,910,592 B was anonymous memory (76.8 GiB) and 28,672 B file cache.

**The kernel killed the stage b parent**, process 165401 (python, anon-rss 14,936,520 kB =
14.2 GiB). The unit then failed with result `oom-kill`.

**Each worker held more than README estimated.** The ten pool workers (165401's children,
pids 173706–173715) held 1,504,210 to 1,770,566 anonymous pages each: 5.7–6.8 GiB, 62.5 GiB
together.
- README "Resources" estimated 4.4 GB per worker and a 59 GB peak, so the 77G cap
  (59 GB + 30%) was too tight. The estimate rested on smoke workers that built one genome
  each.
- Under `--maxtasksperchild 3` a worker builds up to three.
- README is left as the pre-run estimate.

**The resume.** `tmpl7-resume` and `tmpl7-resume2` were launched by hand with the cap
raised to `MemoryMax=120G`.

### The resume script and the stopped attempt

**`chain_tmpl7_resume.sh` is untracked.** It holds `chain_tmpl7.sh` lines 1–49 (the same
pre-checks), without stage a, with stage b appending (`>>`) to `logs/stage_b_gf_pass.log`,
and with the same post-steps. Line 50 changed between the two resume launches:

| Launch | Line 50 |
|---|---|
| `tmpl7-resume` | `rc_a=skipped; fail=${fail:-0}` |
| `tmpl7-resume2` | `rc_a=0  # resume after the OOM kill at 22:54 on 10-29: stage a had already finished (exit 0)` |

The first form would have made the chain's final integer test fail, so the chain would
have exited non-zero even on success.

**Order of events on 10-30:**
1. `logs/tmpl7_chain.log` (the OOM-killed run's log) was copied to
   `logs/tmpl7_chain.oom-2254.log`, and `tmpl7-resume` was launched at 10:33:48.
2. **`tmpl7-resume` was stopped by hand at 10:36:18.** The "0 already done" line it seemed
   to report was the first run's (log line 5); its own line, 2146, already read "20 already
   done, 180 to build" (table above). The resume had been working; the stop was a misreading. No genome
   finished and no row was written: 854 rows before and after.
3. `gf_pass/per_genome.jsonl` was copied to `gf_pass/per_genome.oom-2254.jsonl` (854 rows,
   20 genomes, sha256 `5755edee6dc2b266ad97fdd036e2fb3dd11a046f5fce3d8e4afbf57a81f3d947`).
   `cmp` found the two identical before `tmpl7-resume2` started.
4. `logs/tmpl7_chain.log` was renamed to `logs/tmpl7_chain.resume1-stopped.log`, line 50
   was changed, and `tmpl7-resume2` was launched at 10:39:10.

**The 20 genomes from part 1 were kept, not rebuilt.**
- All 854 of their rows are present byte-identical in the final `per_genome.jsonl`. The
  set is equal, but they are not a prefix, because the harness rewrites the file when it
  finishes (`report_rows.json`, `oom_backup`).
- `identity_control.json` was rewritten by `tmpl7-resume2` at 10:58:43.

**Rows do not depend on the run.** The 72 smoke rows are identical to the full pass's rows
for the same two genomes, apart from wall time (`report_rows.json`, `smoke`).

### Memory of `tmpl7-resume2`

**The journal is the record.** It gives "72.2G memory peak, 0B memory swap peak" (72.2 GiB,
about 77.5 GB), under the 120 GiB cap.

**`logs/mem_trend_resume2.log` holds 10 one-minute samples** from 11:10:50 to 11:19:50.
Each sample has three columns:
- the time;
- `systemctl --user show tmpl7-resume2 -p MemoryCurrent`, in bytes:
  48,636,772,352–77,398,028,288 B (48.6–77.4 GB, 45.3–72.1 GiB);
- the line count of `gf_pass/per_genome.jsonl`: 1,736 → 1,996.

**The 77.6 GB figure is not in any file.** It came from a status message during the run,
not from a file; the journal value above is the one to cite.

### Code and inputs at run time

- **prFBA HEAD.** The commit moved during the runs, but the harness files did not:
  - `9cdefbb` when this file was first written;
  - `f8205be` at the launch of `tmpl7-chain` and of both resumes (the three chain logs);
  - `c91cf19` when the summary was written (`gf_pass/phenotype_summary.json`
    `meta.git_commit`);
  - `b46598b` on 2026-11-02, then `2abcd1a` on 2026-11-03.
- **The harness files are unchanged.**
  - No commit in `9cdefbb..2abcd1a` touches the four harness files (`git log`), and none of
    them has an uncommitted change.
  - On 2026-11-02 and again on 2026-11-03 (at `2abcd1a`), from prFBA
    `region_validation/shared_reference` (where `chain_tmpl7.sh` runs it),
    `sha256sum -c validation/harness.sha256` reports `OK` for all four files and exits 0.
  - The summary's `meta.binding.code` gives `phenotype_fold.py` `defa403b…` and
    `phenotype_arm.py` `0d3342ee…`, as A-C13's does.
- **Templates.**
  - HEAD was `1f84188` at all three launches (chain logs), with `templates/` tree-identical
    to `7fd1ab1`. This was checked by the pre-checks, by `git diff --quiet 7fd1ab1 --
    templates/` on 2026-11-02, and by `apply_draft_loop_fix.py --check` (exit 0;
    `logs/precheck_templates.json` from `tmpl7-resume2`).
  - The summary's `meta.templates` records `git_commit` `1f84188` and the four file sha256
    in "Templates" above.
- **Libraries and inputs.** `meta.libraries` equals A-C13's. The summary's `meta.binding`
  records the input sha256 listed in "Inputs" above.
- **Reference.** A-C13's `per_genome.jsonl` (`ccf6bbf3…`) and `phenotype_summary.json`
  (`e26c23c1…`) are unchanged.

### Output files (sha256, 2026-11-02)

| File | sha256 | Written |
|---|---|---|
| `scan/scope_scan_tmpl7.jsonl` (2,362 rows) | `b9371c0511ea558d1dc907c64d362edb2f0dfe37633d715079b1a3247bee85b0` | 10-29 22:21 |
| `scan/scope_scan_tmpl7.jsonl.meta.json` | `85a71df9fe89c177a16e549e2601807d3bebf30134c3cf5b613ff31eaa9232a0` | 10-29 22:21 |
| `scan/scan_summary.json` | `c1271d5ff8c2dd6b678775c3f22cae8eb3dcc75230589ba7f2ddd66c933f8b14` | 10-29 22:21 |
| `gf_pass/per_genome.jsonl` (8,614 rows) | `dc94ad3af5344327c362ef9b8af0b769c32fcb7ee82a560082ea165ef02f0f79` | 10-30 14:34:08 |
| `gf_pass/phenotype_summary.json` | `c01c52505fd74653dd1760474a5ef90e17bc9f44dd3943665766e872a8d849f6` | 10-30 14:34:11 |
| `gf_pass/identity_control.json` | `bebaf220d7ba08cf2405e716f7da893dc526c1f702650c29599871651babd238` | 10-30 10:58:43 |
| `gf_pass/compare_vs_c13.json` | `df9a719fa06f329b225baf09bac8644d6ead48737d55ff39849bf7a5fba0d127` | 10-30 14:34:19 |
| `gf_pass/c12_compare_vs_c13.json` | `4d7a5016ef596b69659b70efccceddc6acd4bccece888c192a18fadcde79edfa` | 10-30 14:34:21 |
| `gf_pass/per_genome.oom-2254.jsonl` (854 rows) | `5755edee6dc2b266ad97fdd036e2fb3dd11a046f5fce3d8e4afbf57a81f3d947` | copy, 10-30 10:36:20 |

**Added after the runs** (not part of the chain): `report_rows.py`, which writes
`gf_pass/report_rows.json` from the files above and from A-C13's and A-C12's rows.
