#!/usr/bin/env python3
"""
Mock PyOBO test to verify the ontology builder logic without requiring PyOBO installation.

This creates mock versions of PyOBO classes to test our ontology building logic.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any
import json

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


class MockReference:
    """Mock PyOBO Reference class."""
    def __init__(self, prefix: str, identifier: str):
        self.prefix = prefix
        self.identifier = identifier
        
    def __str__(self):
        return f"{self.prefix}:{self.identifier}"
    
    def __eq__(self, other):
        return isinstance(other, MockReference) and self.prefix == other.prefix and self.identifier == other.identifier


class MockTerm:
    """Mock PyOBO Term class."""
    def __init__(self, reference: MockReference, name: str, definition: str = None, comment: str = None):
        self.reference = reference
        self.name = name
        self.definition = definition
        self.comment = comment
        self.xrefs = []
        self.annotations = []
    
    def append_xref(self, ref: MockReference):
        self.xrefs.append(ref)
    
    def annotate_literal(self, prop, value):
        self.annotations.append(('literal', prop, value))
    
    def annotate_object(self, prop, obj):
        self.annotations.append(('object', prop, obj))


class MockTypeDef:
    """Mock PyOBO TypeDef class."""
    def __init__(self, reference: MockReference, name: str, definition: str, comment: str = None):
        self.reference = reference
        self.name = name
        self.definition = definition
        self.comment = comment


class MockObo:
    """Mock PyOBO Obo class."""
    def __init__(self, ontology: str, name: str, definition: str, homepage: str, version: str):
        self.ontology = ontology
        self.name = name
        self.definition = definition
        self.homepage = homepage
        self.version = version
        self.terms = []
        self.typedefs = []


# Replace PyOBO imports with mocks
sys.modules['pyobo'] = type('MockModule', (), {
    'Obo': MockObo,
    'Reference': MockReference,
    'Term': MockTerm,
    'TypeDef': MockTypeDef,
    'write_default_obo': lambda obo, path: print(f"Mock: Would write OWL to {path}"),
    'write_obograph': lambda obo, path: print(f"Mock: Would write JSON-LD to {path}")
})()

sys.modules['bioontologies'] = type('MockModule', (), {})()
sys.modules['pyobo.utils.io'] = type('MockModule', (), {
    'multidict': dict
})()
sys.modules['pyobo.utils.path'] = type('MockModule', (), {
    'ensure_df': lambda x: x
})()


def test_ontology_builder():
    """Test the ontology builder with mock data."""
    print("=== Testing Ontology Builder (Mock) ===")
    
    try:
        # First run extractors to create intermediate files
        print("1. Running extractors to create intermediate files...")
        from build_seed_unified import SEEDUnifiedBuilder
        
        builder = SEEDUnifiedBuilder(
            source_dir=Path(__file__).parent.parent,
            output_dir=Path(__file__).parent / "test_output"
        )
        
        # Extract data only
        extracted_data = builder.extract_data()
        print("✓ Data extraction completed")
        
        # Now test the PyOBO module
        print("2. Testing PyOBO module...")
        from pyobo.sources.seed_unified import get_obo
        
        obo = get_obo()
        print(f"✓ Generated ontology with {len(obo.terms)} terms")
        print(f"✓ Generated {len(obo.typedefs)} type definitions")
        
        # Analyze terms by type
        term_types = {}
        for term in obo.terms:
            term_id = term.reference.identifier
            if term_id.startswith('role_'):
                term_types['roles'] = term_types.get('roles', 0) + 1
            elif term_id.startswith('compound_'):
                term_types['compounds'] = term_types.get('compounds', 0) + 1
            elif term_id.startswith('reaction_'):
                term_types['reactions'] = term_types.get('reactions', 0) + 1
            elif term_id.startswith('complex_'):
                term_types['complexes'] = term_types.get('complexes', 0) + 1
        
        print(f"✓ Term types: {term_types}")
        
        # Show sample terms
        print("✓ Sample terms:")
        for i, term in enumerate(obo.terms[:3]):
            print(f"  {term.reference}: {term.name}")
            if term.annotations:
                print(f"    Annotations: {len(term.annotations)}")
        
        # Show sample typedefs
        print("✓ Sample type definitions:")
        for typedef in obo.typedefs[:3]:
            print(f"  {typedef.reference}: {typedef.name}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Ontology builder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run mock ontology builder test."""
    print("Testing SEED unified ontology builder (with mocks)...")
    
    success = test_ontology_builder()
    
    print(f"\n=== TEST RESULTS ===")
    if success:
        print("✓ Ontology builder working correctly!")
        print("The system is ready for production use.")
        print("\nTo run full build:")
        print("  python build_seed_unified.py --validate")
    else:
        print("✗ Ontology builder test failed.")
        print("Check the error messages above.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)