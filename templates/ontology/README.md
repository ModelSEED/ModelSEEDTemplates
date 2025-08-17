# SEED Unified Ontology

A production-ready semantic ontology system for metabolic model reconstruction achieving **99.81% coverage**.

## 🎯 Quick Results

- **Coverage**: 99.81% (1617/1620 reactions)
- **Comparison**: ModelSEEDpy achieves 99.9% with more permissive logic
- **Technology**: Formal OWL ontology with semantic relationships
- **Deployment**: Compressed files for GitHub, parquet for production

## 📊 What This Provides

- **Formal Relationships**: `enables_reaction`, `has_role`, `has_complex`, `reaction_type`
- **Complete Traceability**: Gene → Role → Complex → Reaction chains
- **Semantic Precision**: Strict logic requiring triggering roles for reaction enablement
- **Production Quality**: SemSQL database with Parquet files for scalable deployment

## 🚀 Quick Start

```bash
# 1. Decompress data files (if needed)
bash scripts/decompress_data.sh

# 2. Run the example notebook showing 99.81% coverage
jupyter notebook examples/Example_Genome_To_Model_OWL_Rebuilt.ipynb

# 3. Or use directly with Python
import pandas as pd
df = pd.read_parquet('examples/statements.parquet')
enables = df[df['predicate'] == 'enables_reaction']
```

## 📁 Directory Structure

```
ontology/
├── data/                          # Source OWL files
│   ├── seed.owl.gz               # SEED roles ontology (compressed)
│   └── modelseed.owl.gz          # ModelSEED biochemistry (compressed)
│
├── ontology/                      # Production outputs
│   ├── seed_unified.owl.gz       # Unified ontology (compressed)
│   ├── seed_unified.db.gz        # SemSQL database (compressed)
│   ├── statements.parquet        # All relationships (6.3MB)
│   └── term_associations.parquet # Gene mappings (60KB)
│
├── scripts/                       # Build and utility scripts
│   ├── build_ontology.py         # Main ontology builder
│   ├── calculate_coverage.py     # Coverage calculator
│   └── decompress_data.sh        # Decompress .gz files
│
├── examples/                      # Demonstrations
│   ├── Example_Genome_To_Model_OWL_Rebuilt.ipynb # 99.81% demo
│   ├── statements.parquet        # Ontology data for notebook
│   ├── term_associations.parquet # Gene mappings for notebook
│   ├── example_ecoli_genome.json # Test genome
│   └── example_ecoli_modelseed_model.json # Target model
│
└── docs/                          # Documentation
    ├── ONTOLOGY_PROPERTIES.md    # Property definitions
    ├── MISSING_REACTIONS.md      # The 3 missing reactions explained
    └── MODELSEEDPY_COMPARISON.md # Our approach vs ModelSEEDpy
```

## 🔬 Coverage Comparison

| System | Coverage | Philosophy |
|--------|----------|------------|
| **SEED Ontology** | 99.81% (1617/1620) | Conservative - requires triggering roles |
| **ModelSEEDpy** | 99.9% (1620/1621) | Permissive - includes optional roles |

### The 3 Missing Reactions
All are PTS transport reactions lacking substrate-specific components:
- `rxn05485`: N-Acetyl-D-glucosamine transport
- `rxn05569`: D-glucosamine transport  
- `rxn05655`: Sucrose transport

See [docs/MODELSEEDPY_COMPARISON.md](docs/MODELSEEDPY_COMPARISON.md) for detailed comparison.

## 🎯 Key Features

### 1. Semantic Relationships
- **enables_reaction**: Role → Reaction (only for triggering=1 roles)
- **has_role**: Complex → Role (all non-optional roles)
- **has_complex**: Reaction → Complex
- **reaction_type**: Marks spontaneous/universal reactions
- **owl:sameAs**: Links duplicate roles (3,134 equivalences)

### 2. owl:sameAs Equivalences
- 3,134 role equivalence relationships
- Critical for accurate coverage calculation
- Handles duplicate roles in the database

### 3. File Compression
- Large files compressed with .gz for GitHub
- Parquet files for efficient data processing
- Helper script for easy decompression

## 📈 Performance

- **Compressed Sizes**: seed_unified.db.gz (30MB), seed_unified.owl.gz (8MB)
- **Query Speed**: Milliseconds using parquet files
- **Scalability**: Handles genomes with 5000+ genes efficiently
- **Coverage Calculation**: <2 seconds for full genome

## 🔧 Usage Examples

### Run the Demo Notebook
```bash
# Shows 99.81% coverage with E. coli genome
jupyter notebook examples/Example_Genome_To_Model_OWL_Rebuilt.ipynb
```

### Use Parquet Files Directly
```python
import pandas as pd

# Load ontology relationships
df = pd.read_parquet('examples/statements.parquet')

# Filter for enables_reaction
enables = df[df['predicate'] == 'enables_reaction']
print(f"Found {len(enables)} role→reaction mappings")
```

### Decompress Files for Database Access
```bash
# Decompress all .gz files
bash scripts/decompress_data.sh

# Then use SQLite
import sqlite3
conn = sqlite3.connect('ontology/seed_unified.db')
```

## 📚 Documentation

- [ONTOLOGY_PROPERTIES.md](docs/ONTOLOGY_PROPERTIES.md) - Detailed property definitions
- [MISSING_REACTIONS.md](docs/MISSING_REACTIONS.md) - Why 3 reactions cannot be mapped
- [MODELSEEDPY_COMPARISON.md](docs/MODELSEEDPY_COMPARISON.md) - Comparison with ModelSEEDpy

## 🏆 Key Achievements

- **99.81% coverage** with semantic precision
- **GitHub-ready** with compressed files under 100MB
- **Production deployment** with parquet files
- **Complete traceability** through formal ontology relationships

## 📧 Contact & Citation

For questions or improvements, please open an issue in the repository.

If using this ontology, please cite:
```
SEED Unified Ontology v1.0
ModelSEED Templates Repository
Coverage: 99.81% (1588/1591 reactions)
```

---
*Last updated: August 2025 | Coverage verified with E. coli test genome*