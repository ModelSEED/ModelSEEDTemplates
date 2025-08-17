# Scripts Directory

Production scripts for building and analyzing the SEED ontology.

## Core Scripts

### build_working_ontology.py
**Purpose**: Build the complete SEED unified ontology with correct entity formats

**Usage**:
```bash
python build_working_ontology.py
```

**Output**:
- `ontology/seed_unified.owl` (OWL/RDF-XML file with full URI predicates)
- Uses Docker: `semsql make ontology/seed_unified.db` (SemSQL database creation)

**Key Features**:
- **Correct entity formats**: Preserves `seed.role:` and `<https://template/roles/>` formats
- Processes template relationships (reactions, complexes, roles)
- Creates enables_reaction only for triggering=1 roles
- Handles duplicate roles with owl:sameAs
- Adds reaction_type for spontaneous/universal reactions
- Uses standard full URI predicates in database

### extract_parquet.py
**Purpose**: Extract parquet files with predicate post-processing (simplified predicates)

**Usage**:
```bash
python extract_parquet.py
```

**Output**:
- `ontology/statements.parquet` (500K+ statements with simplified predicates)
- `ontology/term_associations.parquet` (4.3K gene-role mappings)
- Copies to `examples/` folder for notebook use

**Key Feature**:
- **Post-processing approach**: Converts full URIs to simplified names during extraction
- `<https://modelseed.org/ontology/enables_reaction>` → `enables_reaction`
- Fast parquet file operations
- Ready for production notebooks

### template_enhancer.py
**Purpose**: Enhance template with SEED ID mappings and normalized forms

**Usage**:
```bash
python template_enhancer.py input_template.json output_enhanced.json
```

**Features**:
- Maps template roles to SEED IDs via multiple methods
- Adds normalized forms for fast lookup
- Generates coverage statistics
- Typical enhancement: 74.2% role coverage

## Script Dependencies

All scripts require:
```bash
pip install pandas rdflib sqlite3
```

For template enhancement:
```bash
# Also needs access to RAST-SEED mapper
pip install pyarrow  # For parquet support
```

## Important Implementation Notes

### Triggering Role Logic
```python
# CRITICAL: Only triggering=1 roles enable reactions
if role_ref.get('triggering', 0) == 1:
    add_enables_reaction(role, reaction)
```

### owl:sameAs Expansion
```python
# Build equivalence map from owl:sameAs
for subj, obj in sameas_relations:
    equivalence_map[subj].add(obj)
    equivalence_map[obj].add(subj)

# Expand roles through equivalences
for role in gene_roles:
    equivalent_roles = equivalence_map.get(role, {role})
    # Check ALL equivalent roles for enables_reaction
```

### Post-Processing Approach
Our production solution:
- Database stores full URIs for semantic correctness
- Parquet extraction converts to simplified predicates
- `<https://modelseed.org/ontology/enables_reaction>` → `enables_reaction`
- Clean notebook usage with simplified names

### Complex Satisfaction
Our approach (conservative):
- Requires at least one triggering role present
- All non-optional roles must be in complex

ModelSEEDpy approach (permissive):
- Accepts complexes with only optional roles if any present
- Results in 0.09% coverage difference (3 reactions)

## Workflow

1. **Enhance Template** (if starting fresh):
   ```bash
   python template_enhancer.py raw_template.json enhanced_template.json
   ```

2. **Build Ontology**:
   ```bash
   python build_working_ontology.py
   # Then create database with Docker:
   semsql make -P seed_prefixes.csv ontology/seed_unified.db
   ```

3. **Extract Parquet Files**:
   ```bash
   python extract_parquet.py
   ```

4. **Test Coverage** (via notebook):
   ```bash
   jupyter notebook examples/Example_Genome_To_Model_OWL_Rebuilt.ipynb
   ```

## Performance Notes

- **build_working_ontology.py**: ~2 minutes for ontology creation
- **semsql make**: ~5 minutes for database creation with Docker
- **extract_parquet.py**: ~30 seconds for parquet extraction with post-processing
- **template_enhancer.py**: ~45 seconds for 20K roles
- **Notebook coverage calculation**: ~2 seconds for E. coli genome

## Debugging

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Common issues:
- Missing owl:sameAs expansion → reduced coverage  
- Wrong template version → different coverage results
- Docker timeout → SemSQL creation fails
- Missing entity format preservation → broken CURIE resolution
- Skipping post-processing → notebooks see full URIs instead of simplified predicates