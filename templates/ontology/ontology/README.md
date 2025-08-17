# Production Ontology Files

This folder contains the production-ready SEED unified ontology files.

## Files

### seed_unified.owl.gz
- **Description**: Complete SEED unified ontology in OWL/RDF-XML format
- **Size**: 39MB uncompressed, 8MB compressed
- **Content**: ~310,000 RDF statements
- **Relationships**: enables_reaction, has_role, has_complex, reaction_type, owl:sameAs

### seed_unified.db.gz
- **Description**: SemSQL database for efficient querying
- **Size**: 141MB uncompressed, 30MB compressed
- **Tables**: statements table with 519,521 ontology statements
- **Use**: Production queries and relationship traversal

### statements.parquet
- **Description**: Extracted ontology relationships in Parquet format
- **Size**: 6.3MB (no compression needed)
- **Content**: All 519,521 statements from the database
- **Use**: High-performance data analysis with pandas

### term_associations.parquet
- **Description**: Pre-computed gene to role mappings
- **Size**: 60KB (no compression needed)
- **Content**: 4,378 gene-role associations
- **Use**: Genome annotation to SEED role mapping

## Key Statistics

| Metric | Count |
|--------|-------|
| Total statements | 565,869 |
| Ontology relationships | 20,425 |
| Gene mappings | 4,378 |
| Unique roles | 4,057 |
| Unique genes | 4,161 |
| Coverage achieved | 99.81% |

## Relationship Types

### enables_reaction (6,348)
- **Pattern**: `seed.role:XXXXX` → `seed.reaction:rxnXXXXX`
- **Constraint**: Only for triggering=1 roles
- **Purpose**: Core reaction enablement logic

### has_role (6,347)
- **Pattern**: `seed.complex:cpxXXXX` → `seed.role:XXXXX`
- **Constraint**: All non-optional roles
- **Purpose**: Complex composition

### has_complex (4,554)
- **Pattern**: `seed.reaction:rxnXXXXX` → `seed.complex:cpxXXXX`
- **Purpose**: Reaction catalysis

### reaction_type (42)
- **Values**: "spontaneous" or "universal"
- **Purpose**: Non-enzymatic reactions

### owl:sameAs (3,134)
- **Pattern**: Role equivalences
- **Purpose**: Handle duplicate roles
- **Critical**: Required for 99.81% coverage

## Usage

### Decompress for local use:
```bash
gunzip -k seed_unified.owl.gz
gunzip -k seed_unified.db.gz
```

### Query with Python:
```python
# Using parquet (recommended for production)
import pandas as pd
df = pd.read_parquet('statements.parquet')
enables = df[df['predicate'] == 'enables_reaction']

# Using database (after decompressing)
import sqlite3
conn = sqlite3.connect('seed_unified.db')
df = pd.read_sql_query(
    "SELECT * FROM statements WHERE predicate = 'enables_reaction'", 
    conn
)
```

## Coverage Statistics

Using these files with an E. coli genome:
- **Target reactions**: 1,620
- **Covered reactions**: 1,617
- **Coverage**: 99.81%
- **Missing**: 3 PTS transport reactions (by design)

## Important Notes

1. **owl:sameAs expansion is critical** - without it, coverage shows only 93.9%
2. **Files are compressed for GitHub** - decompress before use
3. **Parquet files don't need compression** - already efficient format
4. **The database is read-only** - rebuild from source if changes needed