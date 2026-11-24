# rxn09388 direction: gapfill check

`gapfill_check.py` gapfills four draft models twice on the same medium: once against the v7.0 templates of `main`
(2294299), once against this branch. The drafts were built by ModelSEEDpy's MSBuilder from RAST-annotated genomes
on the v7.0 templates of `main`. For the patched run, each draft's own rxn09388 is first set to the patched direction,
as a draft built from the patched template would carry it.

Gapfilling: MSGapfill on bio1 (minimum 0.01, prefilter on), with MSATPCorrection's "empty" ATP test on Core-V6.
Medium: `wolfe_h2co2_medium.json`, a Wolfe-type mineral medium with H2/CO2 (the reactor medium of the study that
exposed the defect). Template: GramPos v7.

Tests on each gapfilled model:
- **growth:** bio1 on the medium.
- **sealed ATP:** an ATP hydrolysis test reaction, maximised with every uptake closed (exports open).
- **ATP from H+ and Pi:** the same test with only H+ and phosphate allowed in.

Results (`gapfill_check.json`; ATP in mmol ATP/gDW/h, growth in 1/h):

| Draft | Template | Growth | Sealed ATP | ATP from H+ and Pi | Gapfilled Zn/PPi reactions |
|---|---|---|---|---|---|
| Family_XI.4 | main | 4.382 | 0 | **300** | EX_cpd00012_e0, rxn11268_c0 |
| Family_XI.4 | patched | 2.844 | 0 | 0 | none |
| midas_g_94288.1 | main | 4.257 | 0 | **300** | EX_cpd00012_e0, rxn11268_c0 |
| midas_g_94288.1 | patched | 1.700 | 0 | 0 | none |
| midas_g_98124.1 | main | 4.673 | 0 | 0 | none |
| midas_g_98124.1 | patched | 1.395 | 0 | 0 | none |
| midas_g_110651.1 | main | 1.471 | 0 | 0 | none |
| midas_g_110651.1 | patched | 1.471 | 0 | 0 | none |

How to read it:
- **The leak passes the ATP test.** On `main`, two of the four gapfilled models make 300 mmol ATP/gDW/h from
  phosphate and protons, yet both pass the sealed test and MSATPCorrection's test. Gapfilling adds the
  pyrophosphate exit (the PPi exchange and the PPi:H+ transporter rxn11268) because that route is the cheapest
  "energy source" on the medium.
- **The patched template removes it.** Gapfilling must find a real energy metabolism instead, and growth falls.
- **midas_g_98124.1 grows on the patched template too.** On `main` it makes no ATP from phosphate, but the reversed
  pump, paired with Zn2+:H+ symport, serves as its ATP synthase, driven by the proton gradient. P-type ATPases do not
  run backwards in cells. Patched, gapfilling gives it another route, and growth falls from 4.67 to 1.40.
- **midas_g_110651.1 is the control.** It imports Zn2+ only through rxn09388 in the draft; patched, gapfilling
  supplies another route and growth is unchanged.

Run:

    python validation/zn_atpase/gapfill_check.py --main-root <dir with main's v7.0 templates> \
        --patched-root templates/v7.0 --medium validation/zn_atpase/wolfe_h2co2_medium.json DRAFT.xml ...
