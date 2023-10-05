# ModelSEEDTemplates

Reactions in KEGG and MetaCyc have generic versions without electron donors and acceptors defined, which can render energy biosynthesis obviate, and they often include a mixture of lumped and unlumped reactions, which can cause entire pathways to be bypassed during GEM simulation. Our model templates act as “filters” by including only “modeling-ready” reactions in models. Filtering criteria include (1) no abstract compounds such as “acceptor” and “donor” are allowed; (2) reaction must be mass and charged balanced; (3) all reactants must have defined charge and molecular formula (with few explicit exceptions such as biomass and APS); (4) highly lumped reactions should be avoided when unlumped alternatives exist; (5) reactants should be stereochemically explicit; and (6) all metabolites in the model should be standardized to their primary protonated form at pH 7.5.

## September 2023 Release
### Release highlights
- Templates used to build models in "ModelSEED v2: High-throughput genome-scale metabolic model reconstruction with enhanced energy biosynthesis pathway prediction" pre-print. 
- Introduction of Archaea template.
- Updated core metabolism model template.
- Updated gram-negative template
- Biomass objective function updated to represent DNA, RNA, and Protein compounds instead of individual metabolites. Corresponding DNA, RNA, and Protein synthesis reactions are added to the templates.
- Reaction drains are now represented in the template.

## February 2021 release
### Release highlights
- Retiring legacy templates.
- Introduction of core metabolism template.
- Update of RAST functional role mappings to reactions to match RAST's latest release.
