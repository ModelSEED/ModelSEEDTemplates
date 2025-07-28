# ModelSEED Templates with Ontology Annotations

This directory contains ModelSEED templates that have been enhanced with ontology identifiers and annotations from the ModelSEED ontology project.

## Overview

The ModelSEED ontology provides a formal representation of the biochemical entities and relationships used in ModelSEED templates. By incorporating ontology IDs and annotations into our templates, we enable:

- Better interoperability with other biological databases and ontologies
- Formal semantic relationships between reactions, compounds, and subsystems
- Enhanced querying and reasoning capabilities
- Improved data integration with other systems that use ontology-based representations

## Files

### OWL Ontology Files (`owl/`)
- **modelseed.owl.gz** - The compressed ModelSEED ontology containing formal definitions of ModelSEED entities
- **seed.owl** - The SEED subsystem ontology with role and subsystem definitions

### JSON Format (`json/`)
- **modelseed.json.gz** - Compressed JSON-LD representation of the ModelSEED ontology (converted from OWL using ROBOT)
- **seed.json** - JSON-LD representation of the SEED subsystem ontology

## Ontology Structure

The ModelSEED ontology includes:
- Compound definitions with chemical properties and cross-references
- Reaction definitions with stoichiometry and enzyme classifications
- Role definitions linking to EC numbers and functional annotations
- Subsystem hierarchies and metabolic pathway relationships

## Integration with Templates

The ontology annotations are being integrated into the ModelSEED templates to provide:
- Stable ontology URIs for each compound, reaction, and role
- Semantic relationships between entities
- Cross-references to external databases
- Formal definitions that can be used for automated reasoning

## Usage

These ontology-enhanced templates can be used in the same way as standard ModelSEED templates, with the additional benefit of having formal semantic annotations that enable advanced querying and integration capabilities.

## Version Information

These ontology files correspond to the ModelSEED v2 release and are compatible with the v6.0 templates.

## File Generation Process

The OWL ontology files in this repository were generated using PyOBO scripts available at:
https://github.com/kbase/cdm-data-loader-utils/tree/biochem/biochemistry_loader_scripts/obo

The JSON files were created by converting the OWL files using ROBOT with the following command:
```bash
robot convert --input <file>.owl --output <file>.json
```

Note: The large modelseed.json file has been compressed using gzip to comply with GitHub file size limits.