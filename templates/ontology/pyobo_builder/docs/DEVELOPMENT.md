# Development Guide

This guide provides comprehensive information for developers who want to extend, modify, or contribute to the SEED Unified Ontology Builder.

## Architecture Overview

### System Components

```
pyobo_builder/
├── extractors/                  # Data extraction layer
│   ├── template_extractor.py    # Template data processing
│   ├── modelseed_extractor.py   # ModelSEED data processing
│   └── seed_roles_extractor.py  # SEED roles processing
├── src/pyobo/sources/           # Ontology generation layer
│   └── seed_unified.py          # Core ontology builder
└── build_seed_unified.py        # Orchestration layer
```

### Design Principles

1. **Separation of Concerns**: Each component has a single, well-defined responsibility
2. **Extensibility**: New data sources can be added without modifying existing code
3. **Testability**: All components are unit-testable in isolation
4. **Performance**: Optimized for large-scale biological data processing
5. **OBO Compliance**: Follows OBO Foundry principles and best practices

## Core Components

### Data Extractors

#### Base Extractor Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseExtractor(ABC):
    """Base class for all data extractors."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = None
    
    @abstractmethod
    def extract_all_data(self) -> Dict[str, Any]:
        """Extract all data from the source file."""
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate extracted data structure and content."""
        pass
    
    def get_statistics(self) -> Dict[str, int]:
        """Return basic statistics about extracted data."""
        pass
```

#### Implementing New Extractors

```python
class CustomExtractor(BaseExtractor):
    """Example implementation for custom data source."""
    
    def extract_all_data(self) -> Dict[str, Any]:
        """Extract data from custom format."""
        with open(self.file_path, 'r') as f:
            raw_data = json.load(f)
        
        # Process raw data
        processed_data = {
            'entities': self._extract_entities(raw_data),
            'relationships': self._extract_relationships(raw_data),
            'metadata': self._extract_metadata(raw_data)
        }
        
        # Validate before returning
        if not self.validate_data(processed_data):
            raise ValueError("Data validation failed")
        
        return processed_data
    
    def _extract_entities(self, raw_data):
        """Extract entity data."""
        # Implementation specific to your data format
        pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate extracted data."""
        required_keys = ['entities', 'relationships', 'metadata']
        return all(key in data for key in required_keys)
```

### Ontology Builder

#### Core PyOBO Integration

The ontology builder (`src/pyobo/sources/seed_unified.py`) integrates with PyOBO:

```python
import pyobo
from pyobo import Obo, Term, TypeDef, Reference

def get_obo() -> Obo:
    """Generate the SEED unified ontology."""
    
    # Define ontology metadata
    ontology = Obo(
        ontology='seed_unified',
        name='SEED Unified Ontology',
        auto_generated_by='pyobo_builder',
        format_version='1.4',  # OBO format version
        default_namespace='seed_unified'
    )
    
    # Add custom relationship types
    ontology.typedefs.extend([
        TypeDef(
            reference=Reference(prefix='seed_unified', identifier='role_enables_reaction'),
            name='role enables reaction',
            definition='A functional role enables a biochemical reaction'
        ),
        # Add more TypeDefs as needed
    ])
    
    # Generate terms from extracted data
    ontology.terms.extend(_generate_terms())
    
    return ontology
```

#### Adding Custom Relationship Types

```python
def add_custom_relationship(ontology: Obo, rel_id: str, name: str, definition: str):
    """Add a custom relationship type to the ontology."""
    
    typedef = TypeDef(
        reference=Reference(prefix='seed_unified', identifier=rel_id),
        name=name,
        definition=definition,
        # Optional: add additional properties
        comment='Generated automatically from data source',
        is_transitive=False,  # Set as needed
        is_symmetric=False     # Set as needed
    )
    
    ontology.typedefs.append(typedef)
    return typedef
```

#### Term Generation Patterns

```python
def create_ontology_term(entity_id: str, entity_data: Dict[str, Any]) -> Term:
    """Create an ontology term from entity data."""
    
    term = Term(
        reference=Reference(prefix='seed_unified', identifier=entity_id),
        name=entity_data.get('name', ''),
        definition=entity_data.get('definition', ''),
        namespace='seed_unified'
    )
    
    # Add cross-references
    if 'xrefs' in entity_data:
        term.xrefs = [
            Reference.from_curie(xref) 
            for xref in entity_data['xrefs']
        ]
    
    # Add synonyms
    if 'synonyms' in entity_data:
        term.synonyms = entity_data['synonyms']
    
    # Add relationships
    if 'relationships' in entity_data:
        for rel_type, targets in entity_data['relationships'].items():
            if not hasattr(term, rel_type):
                setattr(term, rel_type, [])
            for target in targets:
                getattr(term, rel_type).append(
                    Reference(prefix='seed_unified', identifier=target)
                )
    
    return term
```

## Testing Framework

### Unit Testing Structure

```python
import unittest
from unittest.mock import patch, mock_open
from extractors.template_extractor import TemplateExtractor

class TestTemplateExtractor(unittest.TestCase):
    """Test cases for template data extraction."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data = {
            "complexes": [
                {
                    "id": "cpx00001",
                    "name": "Test Complex",
                    "roles": ["role1", "role2"]
                }
            ]
        }
    
    @patch("builtins.open", new_callable=mock_open, read_data='{"complexes": []}')
    def test_extract_empty_data(self, mock_file):
        """Test extraction of empty data."""
        extractor = TemplateExtractor("test_file.json")
        data = extractor.extract_all_data()
        
        self.assertIn('complexes', data)
        self.assertEqual(len(data['complexes']), 0)
    
    @patch("builtins.open", new_callable=mock_open)
    def test_extract_complex_data(self, mock_file):
        """Test extraction of complex data."""
        mock_file.return_value.read.return_value = json.dumps(self.test_data)
        
        extractor = TemplateExtractor("test_file.json")
        data = extractor.extract_all_data()
        
        self.assertEqual(len(data['complexes']), 1)
        self.assertEqual(data['complexes']['cpx00001']['name'], 'Test Complex')

# Integration testing
class TestFullPipeline(unittest.TestCase):
    """Test the complete build pipeline."""
    
    def test_full_build_pipeline(self):
        """Test complete ontology build process."""
        builder = SEEDUnifiedBuilder(
            source_dir=Path("test_data/"),
            output_dir=Path("test_output/")
        )
        
        results = builder.build_full_pipeline(validate=True)
        
        self.assertTrue(results['success'])
        self.assertGreater(results['ontology_terms'], 0)
        self.assertTrue(Path("test_output/seed_unified.owl").exists())
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest test_extractors.py

# Run with coverage
python -m pytest --cov=extractors --cov=src

# Run integration tests
python -m pytest test_integration.py -v
```

## Performance Optimization

### Memory Management

```python
import gc
from typing import Iterator, Dict, Any

class StreamingExtractor(BaseExtractor):
    """Memory-efficient extractor for large datasets."""
    
    def extract_data_stream(self) -> Iterator[Dict[str, Any]]:
        """Stream data extraction to minimize memory usage."""
        
        with open(self.file_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                yield self._process_record(data)
                
                # Periodic garbage collection
                if self._record_count % 1000 == 0:
                    gc.collect()
    
    def _process_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual record."""
        # Transform record as needed
        return record
```

### Parallel Processing

```python
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import cpu_count

class ParallelBuilder:
    """Builder with parallel processing capabilities."""
    
    def __init__(self, max_workers=None):
        self.max_workers = max_workers or cpu_count()
    
    def extract_data_parallel(self, file_paths: List[str]) -> Dict[str, Any]:
        """Extract data from multiple files in parallel."""
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._extract_single_file, path): path 
                for path in file_paths
            }
            
            results = {}
            for future in futures:
                path = futures[future]
                try:
                    results[path] = future.result()
                except Exception as e:
                    logger.error(f"Failed to process {path}: {e}")
            
            return results
    
    def _extract_single_file(self, file_path: str) -> Dict[str, Any]:
        """Extract data from a single file."""
        # Implementation depends on file type
        pass
```

### Caching Strategies

```python
import pickle
from pathlib import Path
from typing import Optional

class CachedExtractor(BaseExtractor):
    """Extractor with intelligent caching."""
    
    def __init__(self, file_path: str, cache_dir: str = "cache"):
        super().__init__(file_path)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def extract_all_data(self) -> Dict[str, Any]:
        """Extract data with caching."""
        
        cache_file = self._get_cache_file()
        
        # Check if cache is valid
        if self._is_cache_valid(cache_file):
            logger.info(f"Loading from cache: {cache_file}")
            return self._load_from_cache(cache_file)
        
        # Extract fresh data
        data = self._extract_fresh_data()
        
        # Save to cache
        self._save_to_cache(data, cache_file)
        
        return data
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file is newer than source file."""
        if not cache_file.exists():
            return False
        
        source_mtime = Path(self.file_path).stat().st_mtime
        cache_mtime = cache_file.stat().st_mtime
        
        return cache_mtime > source_mtime
    
    def _get_cache_file(self) -> Path:
        """Generate cache file path."""
        source_name = Path(self.file_path).stem
        return self.cache_dir / f"{source_name}_cache.pkl"
    
    def _load_from_cache(self, cache_file: Path) -> Dict[str, Any]:
        """Load data from cache file."""
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    def _save_to_cache(self, data: Dict[str, Any], cache_file: Path):
        """Save data to cache file."""
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
```

## Adding New Features

### Custom Export Formats

```python
from pyobo import Obo

class CustomExporter:
    """Export ontology to custom formats."""
    
    def __init__(self, ontology: Obo):
        self.ontology = ontology
    
    def export_to_csv(self, output_path: str):
        """Export ontology terms to CSV format."""
        import csv
        
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Name', 'Definition', 'Xrefs'])
            
            for term in self.ontology.terms:
                xrefs = ';'.join([str(xref) for xref in term.xrefs])
                writer.writerow([
                    term.reference,
                    term.name,
                    term.definition,
                    xrefs
                ])
    
    def export_to_neo4j(self, neo4j_uri: str, auth: tuple):
        """Export ontology to Neo4j graph database."""
        from neo4j import GraphDatabase
        
        driver = GraphDatabase.driver(neo4j_uri, auth=auth)
        
        with driver.session() as session:
            # Create nodes
            for term in self.ontology.terms:
                session.run(
                    "CREATE (t:Term {id: $id, name: $name, definition: $definition})",
                    id=str(term.reference),
                    name=term.name,
                    definition=term.definition
                )
            
            # Create relationships
            for term in self.ontology.terms:
                for rel_name in dir(term):
                    if rel_name.startswith('_') or rel_name in ['reference', 'name', 'definition']:
                        continue
                    
                    rel_targets = getattr(term, rel_name, [])
                    for target in rel_targets:
                        session.run(
                            f"MATCH (a:Term {{id: $source}}), (b:Term {{id: $target}}) "
                            f"CREATE (a)-[:{rel_name.upper()}]->(b)",
                            source=str(term.reference),
                            target=str(target)
                        )
```

### Custom Validation Rules

```python
class CustomValidator:
    """Implement custom validation rules."""
    
    def __init__(self, ontology: Obo):
        self.ontology = ontology
        self.issues = []
    
    def validate_term_completeness(self) -> List[str]:
        """Validate that all terms have required fields."""
        issues = []
        
        for term in self.ontology.terms:
            if not term.name:
                issues.append(f"Term {term.reference} missing name")
            
            if not term.definition:
                issues.append(f"Term {term.reference} missing definition")
            
            if not term.xrefs:
                issues.append(f"Term {term.reference} has no cross-references")
        
        return issues
    
    def validate_relationship_integrity(self) -> List[str]:
        """Validate that all relationships point to existing terms."""
        issues = []
        term_ids = {str(term.reference) for term in self.ontology.terms}
        
        for term in self.ontology.terms:
            for rel_name in dir(term):
                if rel_name.startswith('_'):
                    continue
                
                rel_targets = getattr(term, rel_name, [])
                if isinstance(rel_targets, list):
                    for target in rel_targets:
                        if str(target) not in term_ids:
                            issues.append(
                                f"Term {term.reference} has {rel_name} "
                                f"pointing to non-existent term {target}"
                            )
        
        return issues
    
    def run_all_validations(self) -> Dict[str, List[str]]:
        """Run all validation checks."""
        return {
            'completeness': self.validate_term_completeness(),
            'integrity': self.validate_relationship_integrity()
        }
```

## Debugging and Troubleshooting

### Logging Configuration

```python
import logging
from pathlib import Path

def setup_logging(log_level: str = 'INFO', log_file: str = None):
    """Set up comprehensive logging."""
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler(log_file or 'build.log')  # File output
        ]
    )
    
    # Configure specific loggers
    pyobo_logger = logging.getLogger('pyobo')
    pyobo_logger.setLevel(logging.WARNING)  # Reduce PyOBO noise
    
    # Create debug logger for development
    debug_logger = logging.getLogger('debug')
    debug_handler = logging.FileHandler('debug.log')
    debug_handler.setLevel(logging.DEBUG)
    debug_logger.addHandler(debug_handler)
    
    return logging.getLogger(__name__)
```

### Debug Utilities

```python
class DebugUtils:
    """Utilities for debugging the build process."""
    
    @staticmethod
    def dump_intermediate_data(data: Dict[str, Any], stage: str):
        """Dump intermediate data for inspection."""
        debug_dir = Path("debug_output")
        debug_dir.mkdir(exist_ok=True)
        
        output_file = debug_dir / f"{stage}_data.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"Debug data saved to: {output_file}")
    
    @staticmethod
    def profile_function(func):
        """Decorator to profile function execution."""
        import time
        import functools
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            print(f"{func.__name__} took {end_time - start_time:.2f} seconds")
            return result
        
        return wrapper
    
    @staticmethod
    def memory_usage():
        """Get current memory usage."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        return f"Memory usage: {memory_mb:.1f} MB"
```

## Contribution Guidelines

### Code Style

- Follow PEP 8 for Python code style
- Use type hints for all function signatures
- Include comprehensive docstrings
- Maintain test coverage above 80%

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Run the full test suite
5. Update documentation as needed
6. Submit a pull request with clear description

### Development Setup

```bash
# Set up development environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run development tests
python -m pytest tests/
```

This development guide provides the foundation for extending and maintaining the SEED Unified Ontology Builder. For specific questions or advanced use cases, refer to the PyOBO documentation and OBO Foundry principles.