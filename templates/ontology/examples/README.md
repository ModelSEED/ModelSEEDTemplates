# Examples and Demonstrations

This folder contains example notebooks and data demonstrating the SEED ontology achieving **99.81% coverage**.

## Files

### Notebooks

#### Example_Genome_To_Model_OWL_Rebuilt.ipynb
- **Purpose**: Main demonstration of genome-to-model pipeline
- **Achievement**: Shows 99.81% coverage (1617/1620 reactions)
- **Data Source**: Uses parquet files in this folder
- **Key Features**:
  - Loads statements.parquet for ontology relationships
  - Uses term_associations.parquet for gene mappings
  - Demonstrates owl:sameAs expansion (critical for coverage)
  - Identifies the 3 missing PTS transport reactions

### Data Files (All in this folder for easy deployment)

#### statements.parquet (6.3MB)
- Complete ontology relationships from database
- 519,521 statements with simplified predicates
- Key relationships: enables_reaction, owl:sameAs, reaction_type

#### term_associations.parquet (60KB)
- Pre-computed gene to role mappings
- 4,378 associations for E. coli genome
- Maps genes to SEED role IDs

#### example_ecoli_genome.json (841KB)
- Example E. coli genome with 4,642 annotated features
- Used to demonstrate coverage calculation
- Real genome data from RAST annotation

#### example_ecoli_modelseed_model.json (981KB)
- Target ModelSEED model with 1,620 reactions
- Used as comparison baseline
- Shows what reactions should be covered

## Quick Start

1. Open the notebook:
```bash
jupyter notebook Example_Genome_To_Model_OWL_Rebuilt.ipynb
```

2. Run all cells to see:
   - Data loading from parquet files
   - Equivalence map building (owl:sameAs)
   - Gene to reaction mapping
   - 99.81% coverage calculation
   - The 3 missing reactions explained

## Expected Results

```
📊 COVERAGE RESULTS:
   Target reactions: 1,620
   Covered reactions: 1,617
   Missing reactions: 3
   Coverage: 99.81%

❌ Missing reactions: ['rxn05485', 'rxn05569', 'rxn05655']
```

All 3 missing reactions are PTS transport reactions that lack substrate-specific components.

## Key Insights

1. **Parquet files enable fast processing** - No database needed
2. **owl:sameAs is critical** - Without it, coverage drops to 93.9%
3. **Conservative approach** - We require triggering roles, not just optional ones
4. **Production ready** - All files in one folder for easy deployment

## Comparison with ModelSEEDpy

- **ModelSEEDpy**: 99.9% (includes reactions with only optional roles)
- **SEED Ontology**: 99.81% (requires triggering roles)
- **Difference**: 0.09% (3 PTS transport reactions)

Both approaches are valid - ours is more conservative and semantically precise.