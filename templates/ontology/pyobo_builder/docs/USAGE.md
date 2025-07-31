# Usage Guide

This guide provides comprehensive examples and advanced usage patterns for the SEED Unified Ontology Builder.

## Basic Usage

### Command Line Interface

```bash
# Basic build with default settings
python build_seed_unified.py

# Build with validation (recommended)
python build_seed_unified.py --validate

# Custom output directory
python build_seed_unified.py --output-dir /path/to/custom/output

# Verbose logging for debugging
python build_seed_unified.py --validate --verbose

# Specify custom source directory
python build_seed_unified.py --source-dir /path/to/sources --validate
```

### Programmatic Interface

```python
from build_seed_unified import SEEDUnifiedBuilder
from pathlib import Path

# Basic usage
builder = SEEDUnifiedBuilder(
    source_dir=Path("../"),
    output_dir=Path("./output")
)

results = builder.build_full_pipeline(validate=True)
print(f"Generated {results['ontology_terms']} terms")
```

## Advanced Usage

### Custom Data Processing

```python
from extractors import TemplateExtractor, ModelSEEDExtractor, SEEDRolesExtractor

# Use extractors individually
template_extractor = TemplateExtractor("../enhanced_templates/GramNegModelTemplateV6_with_ontology.json")
template_data = template_extractor.extract_all_data()

print(f"Extracted {len(template_data['complexes'])} complexes")
print(f"Extracted {len(template_data['roles'])} roles")

# Access specific data
for complex_id, complex_data in list(template_data['complexes'].items())[:5]:
    print(f"Complex {complex_id}: {complex_data['name']}")
    print(f"  Roles: {len(complex_data.get('roles', []))}")
```

### Working with Generated Ontology

#### Loading and Basic Queries

```python
import owlready2 as owl
import json

# Load the OWL ontology
onto = owl.get_ontology("output/seed_unified.owl").load()

# Load the JSON metadata for easier access
with open("output/seed_unified.json", 'r') as f:
    onto_json = json.load(f)

# Basic statistics
print(f"Total classes: {len(list(onto.classes()))}")
print(f"Total properties: {len(list(onto.properties()))}")
print(f"Total individuals: {len(list(onto.individuals()))}")
```

#### Querying Specific Term Types

```python
# Find all role terms
roles = [cls for cls in onto.classes() if 'role' in cls.name.lower()]
print(f"Found {len(roles)} role classes")

# Find all reaction terms  
reactions = [cls for cls in onto.classes() if 'reaction' in cls.name.lower()]
print(f"Found {len(reactions)} reaction classes")

# Find all compound terms
compounds = [cls for cls in onto.classes() if 'compound' in cls.name.lower()]
print(f"Found {len(compounds)} compound classes")

# Find all complex terms
complexes = [cls for cls in onto.classes() if 'complex' in cls.name.lower()]
print(f"Found {len(complexes)} complex classes")
```

#### Exploring Relationships

```python
# Find role-enables-reaction relationships
role_enables = onto.role_enables_reaction if hasattr(onto, 'role_enables_reaction') else None
if role_enables:
    print(f"Role-enables-reaction property found: {role_enables}")
    
    # Find all instances of this relationship
    for role in roles[:10]:  # Check first 10 roles
        if hasattr(role, 'role_enables_reaction'):
            reactions_enabled = getattr(role, 'role_enables_reaction', [])
            if reactions_enabled:
                print(f"{role.name} enables {len(reactions_enabled)} reactions")

# Find complex-has-role relationships
complex_has_role = onto.complex_has_role if hasattr(onto, 'complex_has_role') else None
if complex_has_role:
    for complex_term in complexes[:5]:  # Check first 5 complexes
        if hasattr(complex_term, 'complex_has_role'):
            roles_in_complex = getattr(complex_term, 'complex_has_role', [])
            if roles_in_complex:
                print(f"{complex_term.name} has {len(roles_in_complex)} roles")
```

#### Cross-Reference Analysis

```python
# Analyze cross-references from JSON metadata
xref_stats = {}

for term in onto_json.get('graphs', [{}])[0].get('nodes', []):
    if 'xrefs' in term:
        for xref in term['xrefs']:
            prefix = xref.split(':')[0] if ':' in xref else 'unknown'
            xref_stats[prefix] = xref_stats.get(prefix, 0) + 1

print("Cross-reference statistics:")
for prefix, count in sorted(xref_stats.items(), key=lambda x: x[1], reverse=True):
    print(f"  {prefix}: {count} references")
```

## Working with Analysis Results

### Understanding Unmapped Entities

```python
import json

# Load unmapped entities analysis
with open("analysis/unmapped_entities.json", 'r') as f:
    unmapped = json.load(f)

print("Unmapped entity summary:")
for category, data in unmapped.items():
    if isinstance(data, dict) and 'count' in data:
        print(f"  {category}: {data['count']} unmapped")
        if 'examples' in data:
            print(f"    Examples: {data['examples'][:3]}")
```

### Coverage Analysis

```python
# Load mapping coverage report
with open("analysis/mapping_coverage_report.json", 'r') as f:
    coverage = json.load(f)

print("Mapping coverage:")
print(f"  Template complexes: {coverage.get('template_complex_coverage', 'N/A')}%")
print(f"  ModelSEED compounds: {coverage.get('modelseed_compound_coverage', 'N/A')}%")
print(f"  SEED roles: {coverage.get('seed_role_coverage', 'N/A')}%")
```

## Performance Optimization

### Memory Management

```python
# For large ontologies, optimize memory usage
import gc

# Build in chunks if needed
builder = SEEDUnifiedBuilder(
    source_dir=Path("../"),
    output_dir=Path("./output")
)

# Enable garbage collection between major steps
results = builder.extract_data()
gc.collect()

# Continue with processing
ontology = builder.build_ontology(results)
gc.collect()

# Export formats
builder.export_ontology(ontology)
```

### Parallel Processing

```python
from concurrent.futures import ThreadPoolExecutor
import json

# Process multiple extractions in parallel
def extract_template_data():
    extractor = TemplateExtractor("../enhanced_templates/GramNegModelTemplateV6_with_ontology.json")
    return extractor.extract_all_data()

def extract_modelseed_data():
    extractor = ModelSEEDExtractor("../json/modelseed.json.gz")
    return extractor.extract_all_data()

def extract_seed_data():
    extractor = SEEDRolesExtractor("../json/seed.json")
    return extractor.extract_all_data()

# Run extractions in parallel
with ThreadPoolExecutor(max_workers=3) as executor:
    template_future = executor.submit(extract_template_data)
    modelseed_future = executor.submit(extract_modelseed_data)
    seed_future = executor.submit(extract_seed_data)
    
    template_data = template_future.result()
    modelseed_data = modelseed_future.result()
    seed_data = seed_future.result()

print("Parallel extraction completed")
```

## Integration Examples

### Using with SPARQL Queries

```python
import rdflib

# Load the Turtle file for SPARQL queries
g = rdflib.Graph()
g.parse("output/seed_unified.ttl", format="turtle")

# Example SPARQL query
query = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX seed: <http://purl.obolibrary.org/obo/SEED_>

SELECT ?role ?roleName ?reaction ?reactionName
WHERE {
    ?role seed:role_enables_reaction ?reaction .
    ?role rdfs:label ?roleName .
    ?reaction rdfs:label ?reactionName .
}
LIMIT 10
"""

results = g.query(query)
for row in results:
    print(f"Role: {row.roleName} -> Reaction: {row.reactionName}")
```

### Integration with Other Tools

```python
# Export to different formats for tool compatibility

# For Protégé
print("Use seed_unified.owl in Protégé for ontology editing")

# For semantic-sql
print("Convert to semantic-sql database:")
print("semsql create -i output/seed_unified.owl -o seed_unified.db")

# For ROBOT toolkit
print("Use ROBOT for ontology operations:")
print("robot query -i output/seed_unified.owl --query my_query.sparql")
```

## Validation and Quality Control

### Custom Validation

```python
# Add custom validation logic
def validate_ontology_completeness(onto_json):
    """Custom validation for ontology completeness."""
    
    issues = []
    nodes = onto_json.get('graphs', [{}])[0].get('nodes', [])
    
    # Check for terms without definitions
    undefined_terms = [node for node in nodes if not node.get('definition')]
    if undefined_terms:
        issues.append(f"{len(undefined_terms)} terms lack definitions")
    
    # Check for orphan terms (no relationships)
    edges = onto_json.get('graphs', [{}])[0].get('edges', [])
    connected_terms = set()
    for edge in edges:
        connected_terms.add(edge.get('subject'))
        connected_terms.add(edge.get('object'))
    
    all_terms = {node.get('id') for node in nodes}
    orphan_terms = all_terms - connected_terms
    if orphan_terms:
        issues.append(f"{len(orphan_terms)} orphan terms found")
    
    return issues

# Run custom validation
with open("output/seed_unified.json", 'r') as f:
    onto_data = json.load(f)

validation_issues = validate_ontology_completeness(onto_data)
if validation_issues:
    print("Validation issues found:")
    for issue in validation_issues:
        print(f"  - {issue}")
else:
    print("Custom validation passed!")
```

## Troubleshooting Common Issues

### Debug Information

```python
# Enable detailed logging
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Run with detailed logging
builder = SEEDUnifiedBuilder(
    source_dir=Path("../"),
    output_dir=Path("./output")
)

try:
    results = builder.build_full_pipeline(validate=True)
    logger.info(f"Build completed successfully: {results}")
except Exception as e:
    logger.error(f"Build failed: {e}", exc_info=True)
```

### Data Source Verification

```python
# Verify source files before building
from pathlib import Path
import gzip

def verify_source_files():
    """Verify all required source files exist and are readable."""
    
    required_files = [
        "../enhanced_templates/GramNegModelTemplateV6_with_ontology.json",
        "../json/modelseed.json.gz",
        "../json/seed.json"
    ]
    
    for file_path in required_files:
        path = Path(file_path)
        if not path.exists():
            print(f"ERROR: Missing required file: {file_path}")
            return False
        
        # Test readability
        try:
            if file_path.endswith('.gz'):
                with gzip.open(path, 'rt') as f:
                    f.read(100)  # Read first 100 chars
            else:
                with open(path, 'r') as f:
                    f.read(100)
            print(f"OK: {file_path}")
        except Exception as e:
            print(f"ERROR: Cannot read {file_path}: {e}")
            return False
    
    return True

# Run verification before building
if verify_source_files():
    print("All source files verified - proceeding with build")
else:
    print("Source file verification failed - fix issues before building")
```

This usage guide provides comprehensive examples for both basic and advanced use cases. For more specific questions, refer to the main README.md or the development guide.