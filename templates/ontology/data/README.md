# Data Sources

This folder contains the source OWL ontology files for building the SEED unified ontology.

## OWL Files

### seed.owl.gz
- **Source**: Built from SEED database using scripts at:
  https://github.com/kbase/cdm-data-loader-utils/tree/biochem/biochemistry_loader_scripts/obo
- **Content**: SEED role definitions (~46,232 roles) and subsystem relationships
- **Size**: 73MB uncompressed, 15MB compressed
- **Format**: OWL/RDF-XML

### modelseed.owl.gz  
- **Source**: Built from ModelSEED biochemistry database using scripts at:
  https://github.com/kbase/cdm-data-loader-utils/tree/biochem/biochemistry_loader_scripts/obo
- **Content**: ModelSEED reactions (~56,009) and compounds (~45,706)
- **Size**: Already compressed (~25MB)
- **Format**: OWL/RDF-XML

## Template Reference

This ontology is designed to work with the ModelSEED template located at:
`/Users/jplfaria/repos/ModelSEEDTemplates/templates/v6.0/GramNegModelTemplateV6.json`

The template contains:
- 8,584 reactions
- 20,548 roles
- 3,296 complexes

## Current Usage

**Note**: The current production builder (`../scripts/build_working_ontology.py`) uses JSON graph data from `../json/` folder instead of these OWL files. These OWL files are kept as reference source data.

### Enhanced Template

**GramNegModelTemplateV6_enhanced.json**: 
- Enhanced version of the v6.0 template with SEED ID mappings
- Used by the working ontology builder  
- Contains 20,548 roles with 74.2% SEED mapping coverage

## Building the Unified Ontology

The current build process:
1. Loads enhanced template and JSON graph data (`../json/seed.json`, `../json/modelseed.json`)
2. Extracts template relationships (reactions, complexes, roles)
3. Creates semantic relationships (enables_reaction, has_role, has_complex, owl:sameAs)
4. Produces unified ontology with 99.81% coverage
5. Post-processes predicates during parquet extraction

See `../scripts/build_working_ontology.py` for the complete build process.