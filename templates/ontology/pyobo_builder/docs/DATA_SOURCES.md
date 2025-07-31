# Data Sources Documentation

This document provides comprehensive information about the three data sources integrated by the SEED Unified Ontology Builder and how they are processed.

## Overview

The ontology builder integrates three complementary biological data sources to create a unified semantic representation of metabolic systems:

1. **Template Data**: Protein complexes and their functional roles
2. **ModelSEED Data**: Compounds, reactions, and cross-references  
3. **SEED Roles Data**: Functional role hierarchies and definitions

## Data Source Details

### 1. Template Data: GramNegModelTemplateV6_with_ontology.json

**Location**: `../enhanced_templates/GramNegModelTemplateV6_with_ontology.json`

#### Purpose
Contains curated protein complexes and their associated functional roles from the ModelSEED template system. This represents the "metabolic machinery" - the protein complexes that catalyze biochemical reactions.

#### Structure
```json
{
  "complexes": [
    {
      "id": "cpx00001",
      "name": "Acetyl-CoA carboxylase",
      "roles": ["role1", "role2"],
      "reactions": ["rxn00001"],
      "ontology_terms": ["GO:0003989"],
      "confidence": 0.95
    }
  ],
  "roles": {
    "role1": {
      "name": "Acetyl-CoA carboxylase",
      "definition": "Catalyzes the carboxylation of acetyl-CoA",
      "ec_numbers": ["6.4.1.2"],
      "subsystem": "Fatty acid biosynthesis"
    }
  }
}
```

#### Key Information Extracted
- **Complexes**: Protein complex identifiers, names, and metadata
- **Complex-Role Relationships**: Which functional roles are performed by each complex
- **Complex-Reaction Relationships**: Which reactions are catalyzed by each complex
- **Role Definitions**: Detailed descriptions of functional roles
- **EC Numbers**: Enzyme Commission identifiers for standardization
- **Subsystem Classifications**: Metabolic pathway groupings
- **Quality Scores**: Confidence levels for complex assignments

#### Processing Details
The template extractor (`extractors/template_extractor.py`) performs:

1. **Data Validation**: Ensures required fields are present
2. **ID Normalization**: Standardizes identifiers for consistency
3. **Relationship Mapping**: Creates bidirectional complex-role mappings
4. **Quality Filtering**: Removes low-confidence assignments
5. **Cross-Reference Generation**: Links to external databases

**Statistics** (typical values):
- ~2,000-3,000 protein complexes
- ~8,000-12,000 functional roles
- ~15,000-25,000 complex-role relationships
- ~95% coverage of core metabolic functions

### 2. ModelSEED Data: modelseed.json.gz

**Location**: `../json/modelseed.json.gz`

#### Purpose
Comprehensive database of biochemical compounds and reactions with extensive cross-references to external databases. This represents the "metabolic chemistry" - the molecules and transformations in metabolism.

#### Structure
```json
{
  "compounds": [
    {
      "id": "cpd00001",
      "name": "H2O",
      "formula": "H2O",
      "charge": 0,
      "mass": 18.015,
      "xrefs": {
        "KEGG": ["C00001"],
        "ChEBI": ["CHEBI:15377"],
        "MetaCyc": ["WATER"]
      },
      "smiles": "O",
      "inchi": "InChI=1S/H2O/h1H2"
    }
  ],
  "reactions": [
    {
      "id": "rxn00001",
      "name": "Hexokinase",
      "equation": "cpd00001 + cpd00002 -> cpd00003 + cpd00004",
      "stoichiometry": {
        "cpd00001": -1,
        "cpd00002": -1,
        "cpd00003": 1,
        "cpd00004": 1
      },
      "reversibility": false,
      "xrefs": {
        "KEGG": ["R00299"],
        "MetaCyc": ["HEXOKINASE-RXN"]
      }
    }
  ]
}
```

#### Key Information Extracted

**Compounds**:
- Chemical identifiers and names
- Molecular formulas and masses
- Structural information (SMILES, InChI)
- Cross-references to KEGG, ChEBI, MetaCyc, PubChem
- Charge states and stereochemistry

**Reactions**:
- Reaction identifiers and names
- Balanced chemical equations
- Stoichiometric coefficients
- Reversibility information
- Cross-references to pathway databases
- EC number associations

#### Processing Details
The ModelSEED extractor (`extractors/modelseed_extractor.py`) performs:

1. **Compression Handling**: Decompresses gzipped JSON data
2. **Data Validation**: Validates chemical formulas and equations
3. **Cross-Reference Standardization**: Normalizes external database IDs
4. **Relationship Extraction**: Maps compounds to reactions via stoichiometry
5. **Quality Control**: Flags invalid or incomplete entries

**Statistics** (typical values):
- ~30,000-40,000 compounds
- ~15,000-20,000 reactions
- ~200,000+ cross-references
- Coverage of major metabolic pathways

### 3. SEED Roles Data: seed.json

**Location**: `../json/seed.json`

#### Purpose
Hierarchical classification of functional roles organized by biological subsystems. This represents the "functional organization" - how biological functions are grouped and classified.

#### Structure
```json
{
  "subsystems": {
    "Glycolysis": {
      "roles": [
        {
          "id": "role_1",
          "name": "Hexokinase (EC 2.7.1.1)",
          "definition": "Phosphorylates glucose to glucose-6-phosphate",
          "ec_numbers": ["2.7.1.1"],
          "functional_class": "enzyme"
        }
      ],
      "hierarchy": ["Central metabolism", "Carbohydrate metabolism", "Glycolysis"],
      "description": "Glucose breakdown pathway"
    }
  },
  "role_mappings": {
    "role_1": {
      "reactions": ["rxn00001"],
      "complexes": ["cpx00001"],
      "genes": ["fig|83333.1.peg.1234"]
    }
  }
}
```

#### Key Information Extracted

**Subsystems**:
- Hierarchical pathway classifications
- Functional role groupings
- Biological process descriptions
- Cross-pathway relationships

**Roles**:
- Detailed functional descriptions
- EC number mappings
- Gene-protein-reaction associations
- Quality annotations

#### Processing Details
The SEED roles extractor (`extractors/seed_roles_extractor.py`) performs:

1. **Hierarchy Processing**: Builds subsystem classification trees
2. **Role Standardization**: Normalizes role names and descriptions
3. **EC Number Parsing**: Extracts and validates enzyme classifications
4. **Cross-Reference Integration**: Links roles to genes and reactions
5. **Definition Enhancement**: Enriches role descriptions with context

**Statistics** (typical values):
- ~200-300 subsystems
- ~8,000-12,000 functional roles
- ~4-6 hierarchy levels
- ~90% coverage of characterized metabolic functions

## Data Integration Process

### 1. Extraction Phase

Each data source is processed independently:

```python
# Template data extraction
template_extractor = TemplateExtractor(template_file)
template_data = template_extractor.extract_all_data()

# ModelSEED data extraction  
modelseed_extractor = ModelSEEDExtractor(modelseed_file)
modelseed_data = modelseed_extractor.extract_all_data()

# SEED roles extraction
seed_extractor = SEEDRolesExtractor(seed_file)
seed_data = seed_extractor.extract_all_data()
```

### 2. Validation Phase

Data quality checks are performed:

- **Completeness**: Required fields are present
- **Consistency**: Cross-references are valid
- **Format Compliance**: Data follows expected schemas
- **Relationship Integrity**: Referenced entities exist

### 3. Integration Phase

Data sources are merged using common identifiers:

- **Role IDs**: Link template complexes to SEED role definitions
- **Reaction IDs**: Connect template reactions to ModelSEED reactions
- **Cross-References**: Use external IDs for additional mappings

### 4. Ontology Generation

Integrated data is converted to semantic ontology format:

- **Terms**: Each entity becomes an ontology class
- **Relationships**: Data relationships become semantic properties
- **Annotations**: Metadata becomes term annotations
- **Cross-References**: External IDs become xref annotations

## Data Quality and Coverage

### Quality Metrics

The system tracks several quality indicators:

```json
{
  "extraction_summary": {
    "template_coverage": 0.95,
    "modelseed_coverage": 0.87,
    "seed_coverage": 0.92,
    "integration_success": 0.91
  },
  "validation_results": {
    "missing_definitions": 245,
    "broken_references": 12,
    "duplicate_mappings": 8
  }
}
```

### Coverage Analysis

Cross-source coverage is analyzed:

- **Template-SEED Role Overlap**: ~85% of template roles have SEED definitions
- **Template-ModelSEED Reaction Overlap**: ~78% of template reactions are in ModelSEED
- **SEED-ModelSEED Functional Overlap**: ~82% of SEED roles map to reactions

### Unmapped Entities

Entities that don't integrate across sources are tracked:

```json
{
  "unmapped_template_roles": {
    "count": 156,
    "examples": ["role_x", "role_y"],
    "reasons": ["deprecated", "organism-specific", "low-confidence"]
  },
  "unmapped_modelseed_compounds": {
    "count": 2341,
    "examples": ["cpd99999"],
    "reasons": ["experimental", "theoretical", "pathway-specific"]
  }
}
```

## Data Source Maintenance

### Update Procedures

1. **Template Updates**: New ModelSEED template versions
2. **ModelSEED Updates**: Quarterly database releases
3. **SEED Updates**: Periodic subsystem annotations

### Version Tracking

```json
{
  "data_versions": {
    "template_version": "v6.0",
    "modelseed_version": "2024-Q1",
    "seed_version": "2024-03-15",
    "integration_date": "2024-03-20"
  }
}
```

### Compatibility

The system handles version differences through:

- **Backward Compatibility**: Supports older data formats
- **Migration Scripts**: Converts between format versions
- **Deprecation Warnings**: Alerts for outdated data
- **Validation Updates**: Adjusts quality checks for new formats

## Performance Considerations

### File Sizes
- Template JSON: ~50-100MB
- ModelSEED compressed: ~200-500MB (uncompressed: ~2-3GB)
- SEED JSON: ~10-20MB

### Processing Time
- Template extraction: ~30-60 seconds
- ModelSEED extraction: ~2-5 minutes
- SEED extraction: ~10-30 seconds
- Integration: ~1-3 minutes

### Memory Usage
- Peak memory: ~2-4GB during ModelSEED processing
- Steady state: ~500MB-1GB
- Recommendation: 8GB RAM for comfortable operation

## Extending Data Sources

### Adding New Sources

To integrate additional data sources:

1. **Create New Extractor**: Implement `BaseExtractor` interface
2. **Define Data Schema**: Specify expected data structure
3. **Add Integration Logic**: Map to existing entity types
4. **Update Validation**: Add quality checks
5. **Test Coverage**: Ensure comprehensive testing

### Custom Data Formats

The system can be extended to support:

- **BioPAX**: Pathway data from BioPAX sources
- **SBML**: Systems Biology Markup Language models
- **Custom JSON**: Organization-specific data formats
- **Database Connections**: Direct database integration

This comprehensive data source documentation ensures users understand how their biological data is processed and integrated into the unified ontology.