# Restrict seven reversible reactions that let draft models make ATP from nothing to forward

Branch `fix-draft-atp-loops` (commits `7fd1ab1` and `1f84188`), on top of
`fix-irreversible-reaction-directions` (`21a8084`, the five-reaction fix). From a fork it
targets `main`, so it shows the five-reaction commit too until that PR merges.

## Summary

**The change.** Seven template reactions are reversible (`=`) in the three genome-scale
v7.0 templates (GramNeg v7, GramPos v7, Archaea v6). Run backwards, each is one step of an
energy-generating cycle. With such a cycle, a draft model, before gapfilling, makes ATP with
every uptake closed and only water and protons free. This PR restricts all seven to their
forward direction.

**How each is edited.** Each reaction is edited the way `21a8084` edits a `=` reaction:
- `direction` and `GapfillDirection` are set to `>`;
- `lower_bound` is set to 0 and `maxrevflux` to 0.0;
- penalties, costs, upper bounds and maximum forward fluxes are unchanged.

**What else changes: nothing.** Core-V6 holds none of the seven, and no other reaction or
field changes; this was checked by parsing every file before and after. v5.0 and v6.0 carry
the same seven `=` entries and are not changed.

| Reaction | Name | Before | After | Database | Why forward |
|---|---|---|---|---|---|
| rxn23850 | GAPN, non-phosphorylating glyceraldehyde-3-phosphate dehydrogenase | `=` | `>` | `>` | ΔG'° −9.75 kcal/mol forward (GOLD). Reversed, with GAPDH (rxn00781) and phosphoglycerate kinase (rxn01100), it makes ATP from ADP and phosphate |
| rxn05746 | maltodextrin glucosidase (maltotriose) | `=` | `>` | `?` | hydrolysis of a glycosidic bond is irreversible |
| rxn08933 | maltodextrin glucosidase (maltotetraose) | `=` | `>` | `>` | the same |
| rxn08934 | maltodextrin glucosidase (maltopentaose) | `=` | `>` | `>` | the same |
| rxn08935 | maltodextrin glucosidase (maltohexaose) | `=` | `>` | `>` | the same |
| rxn08936 | maltodextrin glucosidase (maltoheptaose) | `=` | `>` | `?` | the same |
| rxn00014 | cytochrome c peroxidase | `=` | `>` | `?` (no direction or free energy) | reversed, it makes H2O2 from water and ferricytochrome c, uphill by about 212 kJ/mol (2F × 1.10 V: E'° of H2O2/H2O is +1.35 V, of cytochrome c +0.25 V) |

- **The glucosidase loop.** The glucosidases run backwards together with maltodextrin
  phosphorylase, phosphoglucomutase and glucokinase, also run backwards. The database gives
  `>` for three of the five glucosidases. It gives no direction for rxn05746 and rxn08936,
  which are the same reaction on the neighbouring chain lengths.
- **The rxn00014 loop.** Catalase (rxn00006, forward since the five-reaction fix) turns the
  H2O2 into O2, and cbb3 oxidase (rxn14426, rxn60859) uses the O2 to pump protons for ATP
  synthase. This is the one draft-level loop that the five-reaction fix exposes: on the
  original templates, catalase ran only backwards and blocked the route.

**Reading the diff.** The Gram templates are single-line JSON, so the diff is easiest to
read with `git diff --word-diff 21a8084 7fd1ab1`. `validation/apply_draft_loop_fix.py` makes
the change and keeps each file's existing serialization, so the diff touches only these
reactions; `--check` verifies it.

## Validation

We ran the change through a benchmark that builds ModelSEED models from predicted EC sets
(freiburgermsu/prFBA, `region_validation/shared_reference/`). It ran on 200 genomes with six
EC sets each: the genome's own annotation and five predicted or baseline sets. The pipeline
is MSATPCorrection, then MSGapfill on complete medium, applying the gapfiller's reversals.

The reference is the same run on the five-reaction fix (`21a8084`): the same ModelSEEDpy
commit (`c2e31a0`), inputs and harness code. Only the templates differ.

1. **Draft level, nothing gapfilled.** Every draft (1,181) was tested on a medium of water
   and protons: does it make ATP or biomass?
2. **Gapfilled.** The full pass: 8,614 rows, of which 2,362 are gapfilled models, compared
   row by row with the reference.

## Results

**Draft level: the drafts that make ATP from nothing fall from 865 to 95 of 1,181**
(73.2% to 8.0%).
- 770 drafts stop leaking, and none starts.
- Leaking drafts built from genome annotations fall from 138 to 21 of 200. Leaks at the
  1,000 ATPM bound fall from 833 to 53.
- By template: Archaea 98/142 → 3/142, GramNeg 387/515 → 72/515, GramPos 380/524 → 20/524.
- **The 95 that still leak hold a long tail of a different kind.** The same conversion is
  catalysed with two electron carriers, both reversible. Run forward with one carrier and
  backward with the other, it interconverts them, and a proton-pumping step makes ATP.

**Gapfilled models: no measurable cost.**
- **No leaks.** No model makes ATP or biomass from water and protons: 0 of 8,614 rows,
  against 0 on the five-reaction fix.
- **Growth.** Every one of the 2,362 gapfilled models still grows.
  - The median growth ratio against the reference is 1.000; 1,875 models are within 1%.
  - 204 move by more than 10%, 99 up and 105 down.
  - 164 of the 204 are one baseline, which uses one EC set for all the genomes of a fold.
    Its 164 movers collapse to 19 distinct before/after growth pairs, 82 up and 82 down.
    Several are swaps between two alternative gapfill solutions.
  - For comparison, a ModelSEEDpy update with no template change moved 87 models by more
    than 10%.
  - Two models lose a large growth excess: 16.6 → 2.2 and 11.3 → 1.5. In both, the
    maltotriose glucosidase rxn05746 was essential before and is not after.
- **Gapfill burden.** The number of gapfilled reactions changes by a mean of +0.013
  reactions (median 0; within ±1 in 2,036 models). The gapfill solution changes in 2,271
  models, against 2,263 under that ModelSEEDpy update, by a median of 6 reactions in both.
- **The seven reactions** appear in no gapfill solution and in no reversal.
- **Reversals.** 111 models apply a gapfiller reversal, against 114.
- **ATP and determinism.** The core-model ATP vectors are identical in every row; Core-V6
  is unchanged. Two builds from one EC set still give identical reaction sets, ATP vectors
  and gapfill solutions.
- **The benchmark's readouts move little.** Against the genome's own annotation, the
  per-method medians of reaction-essentiality disagreement and growth move by at most
  0.004, and gapfill burden by at most one reaction. None of the benchmark's comparisons
  changes.

**Caveats.**
- We validated one pipeline: ATP correction, then gapfilling on complete medium. Without
  ATP correction the draft-level loops matter more, and these changes remove most of them,
  but we did not run that pipeline.
- Minimal-medium gapfilling is untested.

## Files

**Templates** (`7fd1ab1`): `templates/v7.0/GramNegModelTemplateV7.json`,
`GramPosModelTemplateV7.json` and `ArchaeaTemplateV6.json`. The seven reactions change in
each, in four fields each. Core-V6 is unchanged.

**`validation/`** (`7fd1ab1`, `1f84188`):
- `apply_draft_loop_fix.py` makes the change, and `--check` verifies it.
- `compare_probe_templates.py` and `probe_comparison.json` check the diff against
  `21a8084` and against the templates of the draft-level probe.
- `chain_tmpl7.sh`, `launch_tmpl7.sh` and `harness.sha256` run the two stages through the
  benchmark's harness.
- `scan_summary.py` and `compare_gf_to_c13.py` summarize them.
- `README.md` and `PROVENANCE.md` give the plan, the commits and the file hashes.
- If you would rather take the template change alone, `7fd1ab1` stands without `1f84188`.

**Data and full results:**
- in this branch's `validation/` (`REPORT.md`, `PROVENANCE.md`);
- in freiburgermsu/prFBA, `region_validation/shared_reference/C12_SCOPE.md` sections 2,
  2b and 3: the draft-level scan and the loop families;
- issue #10, the direction audit, lists rxn23850 and the glucosidases among the
  reversible-in-template reactions. It cannot list rxn00014, which has no database
  direction.
