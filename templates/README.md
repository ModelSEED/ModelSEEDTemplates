# ModelSEED Templates

This directory contains ModelSEED templates organized by version for better release management and backward compatibility.

## Directory Structure

### Current Release
- **`v6.0/`** - Latest templates (June 2025)
  - ArchaeaTemplateV6.json - Archaea organisms
  - Core-V5.2.json - Enhanced core metabolism for bacteria  
  - GramNegModelTemplateV6.json - Gram-negative bacteria
  - GramPosModelTemplateV6.json - Gram-positive bacteria
  - biomass_formulations/ - Organism-specific biomass compositions

### Previous Release
- **`v5.0/`** - Previous stable release (September 2023)
  - ArchaeaModelTemplateV5.json - Archaea organisms
  - CoreModelTemplateV5.json - Core metabolism for bacteria
  - GramNegModelTemplateV5.json - Gram-negative bacteria
  - GramPosModelTemplateV5.json - Gram-positive bacteria
  - biomass_formulations/ - Corresponding biomass formulations

### Archive
- **`legacy/`** - Legacy templates (pre-v5.0)
  - Contains historical templates in TSV format
  - Maintained for archival and compatibility purposes

## Usage

### For New Projects
Use templates from `v6.0/` directory for the latest features and improvements.

### For Existing Projects
- Continue using `v5.0/` templates for consistency with existing workflows
- Migrate to `v6.0/` when ready to adopt latest improvements

### For Historical Analysis
Legacy templates in `legacy/` directory provide access to older template versions.

## Release Information

### v6.0 (June 2025)
- Coincides with ModelSEED v2 manuscript submission for publication
- Enhanced templates with improved metabolic coverage
- Better organism-specific representations
- Improved repository organization

### v5.0 (September 2023) 
- Used in ModelSEED v2 publication: https://www.biorxiv.org/content/10.1101/2023.10.04.556561v1.abstract
- Introduction of Archaea template
- Enhanced biomass formulations with DNA/RNA/Protein compounds
- Addition of reaction drains

For detailed changes, see the main repository CHANGELOG.md.
