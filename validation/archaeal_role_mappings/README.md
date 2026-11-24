# Archaeal role mappings: draft-build check

`build_drafts.py` builds drafts of three hydrogenotrophic methanogens (Methanobacterium.1, .3 and .16, RAST-annotated
genomes of a methanogenic bioreactor community) with MSBuilder (`build_base_model`, `annotate_with_rast=False`)
against the v7.0 Archaea template of `main` ("pristine") and of this branch ("patched"). It records which reactions
each probed gene reaches. The paths in the script point at that project, so it documents the run rather than
reproducing it standalone. "whole" uses the RAST strings as the project loads them. "split" splits multi-function
strings (`modelseedpy.core.rast_client.split_annotation`) before matching.

Results (`build_results.json`; reactions per draft, whole strings: pristine -> patched):

| Draft | Reactions | FBPA/P gene | archaeal adenylate kinase gene | TfrA / TfrB genes |
|---|---|---|---|---|
| Methanobacterium.1 | 551 -> 554 | 937: rxn00549 -> rxn00549, **rxn00786** | 602: none -> **rxn00097** | 793 / 799: none -> **rxn40405** |
| Methanobacterium.3 | 511 -> 514 | 1253: rxn00549 -> rxn00549, **rxn00786** | 1930: none -> **rxn00097** | 1024 / 1017: none -> **rxn40405** |
| Methanobacterium.16 | 496 -> 499 | 837: rxn00549 -> rxn00549, **rxn00786** | 414: none -> **rxn00097** | TfrB only, 463: none -> **rxn40405** |

How to read it:
- **Exactly three reactions are added to each draft, each with its gene.** Nothing else changes.
- **Before the change the drafts had no adenylate kinase at all.** Their only adenylate kinase gene is the archaeal
  type, which matched no template role.
- **The "split" builds show the same three additions on top of the split baseline.**
