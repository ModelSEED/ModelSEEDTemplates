# Changelog

All notable changes to ModelSEED Templates will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- The role tftr01203 'sodium-translocating pyrophosphatase' (the RAST function of the membrane Na+-translocating
  pyrophosphatase, Na+-PPase, EC 7.2.3.1) and its reaction rxn54366_c (H2O + PPi + Na+[c] -> 2 Pi + H+ + Na+[e]), with one
  new single-role complex tcpx01432, in the Archaea, GramNeg and GramPos templates of v5.0, v6.0 and v7.0. No template carried
  the role, so a genome whose only pyrophosphatase is the Na+ pump got no PPi hydrolysis. Direction '>' (hydrolysis; the
  database lists '='), type 'conditional', base cost and penalties as rxn00001_c.
- A complex tcpx01433 for the orphan role ftr33579 'inorganic diphosphatase (EC 3.6.1.1)' on rxn00001_c (soluble
  pyrophosphatase), in the same nine files. Both changes are applied by `validation/apply_sodium_pyrophosphatase.py`, which
  keeps each file's serialization. The Core templates are not touched.

## [6.0.0] - 2025-06-18

### Added
- New versioned repository structure for better release management
- Enhanced Archaea template (V6) with improved metabolic coverage
- Updated Core metabolism template (V5.2) with refined reaction set
- Updated Gram-negative template (V6) with enhanced pathway representation
- Updated Gram-positive template (V6) with improved organism-specific reactions
- Organized biomass formulations by template version
- Comprehensive documentation for repository structure

### Changed
- Repository restructured with version-specific directories (`v6.0/`, `v5.0/`, `legacy/`)
- Legacy templates moved to dedicated `legacy/` directory
- Biomass formulations organized by version for better compatibility tracking
- Updated README with new repository structure and v6.0 release information

### Fixed
- Improved template organization for easier version management
- Better separation of current vs legacy content

### Notes
- This release coincides with ModelSEED v2 manuscript submission for publication
- All v6.0 templates maintain backward compatibility with v5.0 where applicable

## [5.0.0] - 2023-09-01

### Added
- Templates used in "ModelSEED v2: High-throughput genome-scale metabolic model reconstruction with enhanced energy biosynthesis pathway prediction" pre-print
- Introduction of Archaea template (V5)
- Updated core metabolism model template
- Updated gram-negative template
- Updated gram-positive template
- Biomass objective function updated to represent DNA, RNA, and Protein compounds instead of individual metabolites
- Corresponding DNA, RNA, and Protein synthesis reactions added to templates
- Reaction drains now represented in templates

### Changed
- Enhanced biomass formulations with compound-level representations
- Improved reaction coverage across all template types

### Reference
- Pre-print: https://www.biorxiv.org/content/10.1101/2023.10.04.556561v1.abstract

## [4.0.0] - 2021-02-01

### Added
- Introduction of core metabolism template
- Updated RAST functional role mappings to reactions to match RAST's latest release

### Deprecated
- Legacy templates retired (moved to legacy directory in v6.0.0)

### Changed
- Significant updates to reaction mappings and functional roles
- Enhanced template accuracy and coverage

---

## Version Compatibility Guide

- **v6.0**: Latest release with enhanced templates and improved organization
- **v5.0**: Stable release used in ModelSEED v2 publication
- **Legacy**: Historical templates (pre-v5.0) maintained for archival purposes

For detailed version-specific changes, see individual changelog files in the `ChangeLogs/` directory.