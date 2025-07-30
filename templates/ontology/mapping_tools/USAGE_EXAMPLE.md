# Usage Example: Adding Ontology Mappings to Templates

## Quick Start

1. **Process the default template** (GramNegModelTemplateV6):
```bash
python add_ontology_mappings.py
```

2. **Process a custom template**:
```bash
python add_ontology_mappings.py /path/to/your/template.json /output/directory/
```

## Example Output

### Enhanced Role Entry
```json
{
  "id": "ftr01407",
  "name": "Lactate 2-monooxygenase (EC 1.13.12.4)",
  "source": "ModelSEED",
  "seed_id": "seed.role:0000000004380",
  "seed_url": "https://pubseed.theseed.org/RoleEditor.cgi?page=ShowRole&Role=0000000004380"
}
```

### Enhanced Compound Entry
```json
{
  "id": "cpd00001",
  "name": "H2O",
  "seed_id": "seed.compound:cpd00001",
  "seed_url": "https://modelseed.org/biochem/compounds/cpd00001",
  "kegg_ids": ["C00001"],
  "chebi_ids": ["CHEBI:15377"]
}
```

### Enhanced Reaction Entry
```json
{
  "id": "rxn00001_c0",
  "name": "Phosphate:phosphate phosphotransferase...",
  "seed_id": "seed.reaction:rxn00001",
  "seed_url": "https://modelseed.org/biochem/reactions/rxn00001",
  "ec_numbers": ["2.7.4.1"]
}
```

### Enhanced Complex Entry
```json
{
  "id": "cpx01798",
  "name": "Lactate 2-monooxygenase",
  "seed_id": "seed.complex:cpx01798",
  "seed_url": "https://modelseed.org/biochem/complexes/cpx01798",
  "role_seeds": ["seed.role:0000000004380"]
}
```

## Mapping Statistics

Example output from GramNegModelTemplateV6:
```
=== MAPPING SUMMARY ===
Roles: 9,981/16,138 ModelSEED roles mapped
Compounds: 6,569/6,573 mapped
Reactions: 8,576/8,584 mapped
Complexes: 3,296/3,296 mapped
```

## Unmapped Entities Report

The CSV report includes entities that couldn't be mapped:
```csv
Entity Type,ID,Name/Details,Additional Info
role,ftr00123,Hypothetical protein,ModelSEED
compound,cpd99999,Unknown compound,C1H2O3
reaction,rxn99999,Unknown reaction,base: rxn99999
```