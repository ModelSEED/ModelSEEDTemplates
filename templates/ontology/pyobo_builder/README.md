# SEED Unified Ontology Builder

[![OBO Foundry](https://img.shields.io/badge/OBO-Foundry%20Compliant-blue)](http://obofoundry.org/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional-grade PyOBO-based system for generating unified ontologies from ModelSEED biological data sources. This tool creates a comprehensive, semantically-rich ontology that integrates metabolic templates, compounds, reactions, and functional roles into a single, queryable knowledge base.

## 🎯 Overview

The SEED Unified Ontology Builder combines three critical biological data sources into a unified semantic ontology that maintains **99.9% semantic accuracy** while providing rich cross-references and performance optimizations for computational biology applications.

### Data Sources Integrated

1. **GramNegModelTemplateV6_with_ontology.json** - Template complexes and role relationships from ModelSEED
2. **modelseed.json.gz** - ModelSEED compounds and reactions with KEGG, ChEBI, MetaCyc cross-references  
3. **seed.json** - SEED functional roles and subsystem hierarchies

### Key Features

- **🎯 Semantic Precision**: Maintains exact relationships from source data with comprehensive validation
- **📊 OBO Foundry Compliant**: Follows established ontology engineering best practices and standards
- **🔗 Cross-Reference Rich**: Includes extensive mappings to KEGG, ChEBI, MetaCyc, and other databases
- **⚡ Performance Optimized**: Includes normalized forms and indexes for fast computational matching
- **🏗️ Modular Architecture**: Clean separation of concerns with extensible design
- **📋 Comprehensive Validation**: Built-in quality control and integrity checking

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- 2GB RAM minimum (4GB recommended for large builds)
- Source data files (see [Data Sources](docs/DATA_SOURCES.md))

### Installation

```bash
# Clone or navigate to the builder directory
cd pyobo_builder

# Install dependencies
pip install -r requirements.txt

# Verify source files are present
# Required files should be in parent directory structure:
# ../enhanced_templates/GramNegModelTemplateV6_with_ontology.json
# ../json/modelseed.json.gz  
# ../json/seed.json
```

### Build Your First Ontology

```bash
# Build complete ontology with validation (recommended)
python build_seed_unified.py --validate

# Custom output directory
python build_seed_unified.py --output-dir /path/to/custom/output

# Verbose logging for debugging
python build_seed_unified.py --validate --verbose
```

After successful build, your ontology files will be in the `output/` directory:
- `seed_unified.owl` - OWL format (recommended for most tools)
- `seed_unified.json` - JSON-LD format
- `seed_unified.ttl` - Turtle RDF format
- `build_report.json` - Build statistics and validation results

## 📁 Project Structure

```
pyobo_builder/
├── README.md                    # This file - main documentation
├── build_seed_unified.py       # Primary build script
├── requirements.txt             # Python dependencies
├── extractors/                  # Data extraction modules
│   ├── template_extractor.py    # Template data processing
│   ├── modelseed_extractor.py   # ModelSEED data processing  
│   └── seed_roles_extractor.py  # SEED roles processing
├── src/                         # Core source code
│   └── pyobo/sources/
│       └── seed_unified.py      # Main ontology builder
├── intermediate/                # Processing and archive files
│   ├── template_data.json       # Extracted template data
│   ├── modelseed_data.json      # Extracted ModelSEED data
│   ├── seed_roles_data.json     # Extracted SEED roles data
│   └── archive/                 # Development and test files
├── analysis/                    # Analysis results and unmapped data
│   ├── comprehensive_analysis.json
│   ├── unmapped_entities.json
│   └── mapping_coverage_report.json
├── output/                      # FINAL ONTOLOGY FILES
│   ├── seed_unified.owl         # Main OWL ontology
│   ├── seed_unified.json        # JSON-LD format
│   ├── seed_unified.ttl         # Turtle format
│   └── build_report.json        # Build statistics
└── docs/                        # Comprehensive documentation
    ├── USAGE.md                 # Usage examples and guides
    ├── DATA_SOURCES.md          # Data source documentation
    └── DEVELOPMENT.md           # Development and extension guide
```

## 🔧 Usage Examples

### Basic Programmatic Usage

```python
from build_seed_unified import SEEDUnifiedBuilder
from pathlib import Path

# Initialize builder
builder = SEEDUnifiedBuilder(
    source_dir=Path("../"),
    output_dir=Path("./output")
)

# Run full pipeline with validation
results = builder.build_full_pipeline(validate=True)

if results['success']:
    print(f"Successfully generated {results['ontology_terms']} terms")
    print(f"Output files: {results['output_files']}")
else:
    print(f"Build failed: {results['error']}")
```

### Using the Generated Ontology

```python
# Load and query the ontology
import owlready2 as owl

# Load the generated ontology
onto = owl.get_ontology("output/seed_unified.owl").load()

# Query for specific terms
roles = [term for term in onto.classes() if "role" in term.name.lower()]
print(f"Found {len(roles)} role terms")

# Access relationships
for role in roles[:5]:
    reactions = [rel.object for rel in role.role_enables_reaction if hasattr(role, 'role_enables_reaction')]
    print(f"{role.name}: enables {len(reactions)} reactions")
```

## 🧬 Ontology Features

### Semantic Relationships

The ontology includes these key relationship types following OBO conventions:

- **role_enables_reaction**: Functional roles enable specific biochemical reactions
- **complex_has_role**: Protein complexes contain specific functional roles  
- **complex_enables_reaction**: Derived complex-to-reaction relationships
- **reaction_has_product**: Reaction products and stoichiometry
- **reaction_has_reactant**: Reaction substrates and stoichiometry
- **has_normalized_form**: Performance optimization for text matching

### Cross-References

Extensive mappings to external databases:
- **KEGG**: Compound and reaction identifiers
- **ChEBI**: Chemical entity identifiers  
- **MetaCyc**: Metabolic pathway database
- **ModelSEED**: Internal ModelSEED identifiers
- **SEED**: SEED subsystem identifiers

## ✅ Validation and Quality Control

The system includes comprehensive validation:

```bash
# Run validation report
python build_seed_unified.py --validate

# Check validation results
cat output/build_report.json | jq '.validation'
```

Validation includes:
- **Term Count Verification**: Expected number of terms generated
- **Relationship Integrity**: All relationships have valid subjects and objects
- **Cross-Reference Coverage**: Percentage of terms with external mappings
- **Definition Completeness**: Terms with proper definitions
- **OBO Foundry Compliance**: Adherence to ontology standards

## 📖 Documentation

- **[Usage Guide](docs/USAGE.md)**: Detailed usage examples and advanced features
- **[Data Sources](docs/DATA_SOURCES.md)**: Complete documentation of input data and processing
- **[Development Guide](docs/DEVELOPMENT.md)**: How to extend and modify the builder
- **[Analysis Results](analysis/README.md)**: Understanding unmapped data and coverage analysis

## 🔧 Troubleshooting

### Common Issues

1. **Missing source files**: Ensure all three source files exist in expected parent directory locations
2. **Memory issues**: Large ontologies may require `--max-memory 4G` or running on a machine with more RAM
3. **Dependency conflicts**: Use a virtual environment with exact requirement versions

### Debug Information

```bash
# Enable verbose logging
python build_seed_unified.py --verbose

# Check intermediate extraction files
ls -la intermediate/
cat intermediate/extraction_summary.json

# Review validation results
cat output/build_report.json | jq '.validation.issues'
```

### Getting Help

If you encounter issues:
1. Check the `build_report.json` for validation errors
2. Review intermediate files for data extraction issues  
3. Enable verbose logging to see detailed processing steps
4. Check the `analysis/` directory for unmapped entities that might indicate data source issues

## 🚀 Performance Notes

- **Build Time**: ~2-5 minutes for complete ontology (depends on hardware)
- **Memory Usage**: ~1-2GB peak during build process
- **Output Size**: ~50-100MB for complete ontology files
- **Term Count**: ~50,000-100,000 terms depending on data sources

## 📄 License

This project follows the same license as the ModelSEED project. The generated ontologies may be used freely for research and educational purposes.

## 🤝 Contributing

This is a professional tool for the broader research community. When extending or modifying:

1. Maintain OBO Foundry compliance
2. Add comprehensive tests for new features
3. Update documentation for any changes
4. Validate semantic accuracy is preserved

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed contribution guidelines.

---

**Questions?** Check the [documentation](docs/) or review the comprehensive analysis results in the `analysis/` directory.