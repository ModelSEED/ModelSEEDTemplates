# ModelSEED Template Ontology Mapping

This directory contains tools and results for mapping ModelSEED templates to SEED ontology identifiers.

## Overview

The mapping process adds ontology identifiers to ModelSEED template entities while preserving all original content. This enables:
- Semantic interoperability with other systems using SEED ontologies
- Formal reasoning over metabolic models
- Cross-references to external databases
- Traceability between ModelSEED and ontology identifiers

## Directory Structure

```
templates/ontology/
├── owl/                           # OWL ontology files
│   ├── modelseed.owl.gz          # ModelSEED ontology (compounds, reactions)
│   └── seed.owl                  # SEED role/subsystem ontology
├── json/                         # JSON-LD versions
│   ├── modelseed.json.gz         # Converted from modelseed.owl
│   └── seed.json                 # Converted from seed.owl
├── mapping_tools/                # Scripts for mapping
│   └── add_ontology_mappings.py  # Main mapping script
├── enhanced_templates/           # Output templates with ontology mappings
│   ├── *_with_ontology.json     # Enhanced template files
│   └── *_unmapped.csv           # Reports of unmapped entities
└── README.md                     # General ontology documentation
```

## Mapping Process

### 1. Input Files
- **Template**: Original ModelSEED template (e.g., `GramNegModelTemplateV6.json`)
- **seed.json**: SEED role ontology with `https://pubseed.theseed.org` URLs
- **modelseed.json**: ModelSEED ontology with compound and reaction definitions

### 2. Mapping Rules

#### Roles (seed.role)
- Maps ModelSEED roles (source="ModelSEED") to seed.role IDs
- Uses RASTSeedMapper to match role names to SEED ontology
- Adds:
  - `seed_id`: e.g., "seed.role:0000000004380"
  - `seed_url`: e.g., "https://pubseed.theseed.org/RoleEditor.cgi?page=ShowRole&Role=0000000004380"

#### Compounds (seed.compound)
- Maps compound IDs directly to modelseed ontology
- Adds:
  - `seed_id`: e.g., "seed.compound:cpd00001"
  - `seed_url`: e.g., "https://modelseed.org/biochem/compounds/cpd00001"
  - Cross-references: KEGG, ChEBI IDs when available

#### Reactions (seed.reaction)
- Maps reaction IDs (removing compartment suffixes) to modelseed ontology
- Adds:
  - `seed_id`: e.g., "seed.reaction:rxn00001"
  - `seed_url`: e.g., "https://modelseed.org/biochem/reactions/rxn00001"
  - Cross-references: EC numbers, KEGG, MetaCyc IDs when available

#### Complexes (seed.complex)
- Uses existing complex IDs to create seed.complex identifiers
- Maps complex roles to their corresponding seed.role IDs
- Adds:
  - `seed_id`: e.g., "seed.complex:cpx01798"
  - `seed_url`: e.g., "https://modelseed.org/biochem/complexes/cpx01798"
  - `role_seeds`: List of seed.role IDs for roles in the complex

### 3. Running the Mapping

```bash
cd templates/ontology/mapping_tools
python add_ontology_mappings.py
```

This will:
1. Load the template and ontology files
2. Add ontology mappings to all applicable entities
3. Save enhanced template to `enhanced_templates/`
4. Generate CSV report of unmapped entities

### 4. Output Files

#### Enhanced Template (*_with_ontology.json)
Contains all original data plus ontology mappings. Example entry:
```json
{
  "id": "ftr01407",
  "name": "Lactate 2-monooxygenase (EC 1.13.12.4)",
  "source": "ModelSEED",
  "seed_id": "seed.role:0000000004380",
  "seed_url": "https://pubseed.theseed.org/RoleEditor.cgi?page=ShowRole&Role=0000000004380"
}
```

#### Unmapped Report (*_unmapped.csv)
Lists entities that could not be mapped to ontology identifiers:
- Roles that don't match any SEED role
- Compounds/reactions not in modelseed ontology
- Includes ID, name, and additional context

## Mapping Statistics (GramNegModelTemplateV6)

- **Roles**: 9,981 of 16,138 ModelSEED roles mapped (62%)
- **Compounds**: 6,569 of 6,573 mapped (99.9%)
- **Reactions**: 8,576 of 8,584 mapped (99.9%)
- **Complexes**: 3,296 of 3,296 mapped (100%)

## Future Improvements

1. Improve role mapping coverage by:
   - Handling alternative name formats
   - Using EC numbers for mapping
   - Manual curation of common unmapped roles

2. Add subsystem mappings when available

3. Create bidirectional mappings for data integration

4. Enhance cross-reference support for external databases

## Related Documentation

- [General Ontology README](../README.md) - Overview of ontology files
- [SEED Ontology](https://pubseed.theseed.org/) - SEED role browser
- [ModelSEED](http://modelseed.org/) - ModelSEED project