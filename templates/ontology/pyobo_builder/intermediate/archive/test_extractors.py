#!/usr/bin/env python3
"""
Test script for SEED unified ontology extractors.

This script tests each extractor individually to ensure they can
properly parse the source files.
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from extractors import TemplateExtractor, ModelSEEDExtractor, SEEDRolesExtractor


def test_template_extractor():
    """Test the template extractor."""
    print("=== Testing Template Extractor ===")
    
    template_path = Path(__file__).parent.parent / "enhanced_templates" / "GramNegModelTemplateV6_with_ontology.json"
    
    if not template_path.exists():
        print(f"ERROR: Template file not found: {template_path}")
        return False
    
    try:
        extractor = TemplateExtractor(str(template_path))
        data = extractor.extract_all_data()
        
        print(f"✓ Complexes: {len(data['complexes'])}")
        print(f"✓ Reactions: {len(data['reactions'])}")
        print(f"✓ Roles: {len(data['roles'])}")
        print(f"✓ Complex-role relationships: {len(data['complex_role_relationships'])}")
        print(f"✓ Reaction-complex relationships: {len(data['reaction_complex_relationships'])}")
        
        # Show sample complex
        if data['complexes']:
            sample_id = list(data['complexes'].keys())[0]
            sample = data['complexes'][sample_id]
            print(f"✓ Sample complex: {sample_id} - {sample['name']} ({len(sample['roles'])} roles)")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Template extractor failed: {e}")
        return False


def test_modelseed_extractor():
    """Test the ModelSEED extractor."""
    print("\n=== Testing ModelSEED Extractor ===")
    
    modelseed_path = Path(__file__).parent.parent / "json" / "modelseed.json.gz"
    
    if not modelseed_path.exists():
        print(f"ERROR: ModelSEED file not found: {modelseed_path}")
        return False
    
    try:
        extractor = ModelSEEDExtractor(str(modelseed_path))
        data = extractor.extract_all_data()
        
        print(f"✓ Compounds: {len(data['compounds'])}")
        print(f"✓ Reactions: {len(data['reactions'])}")
        print(f"✓ Relationships: {len(data['relationships'])}")
        print(f"✓ Compound xrefs: {data['compound_xrefs_summary']}")
        print(f"✓ Reaction xrefs: {data['reaction_xrefs_summary']}")
        
        # Show sample compound
        if data['compounds']:
            sample_id = list(data['compounds'].keys())[0]
            sample = data['compounds'][sample_id]
            print(f"✓ Sample compound: {sample_id} - {sample['name']} (xrefs: {list(sample['xrefs'].keys())})")
        
        return True
        
    except Exception as e:
        print(f"ERROR: ModelSEED extractor failed: {e}")
        return False


def test_seed_roles_extractor():
    """Test the SEED roles extractor."""
    print("\n=== Testing SEED Roles Extractor ===")
    
    seed_path = Path(__file__).parent.parent / "json" / "seed.json"
    
    if not seed_path.exists():
        print(f"ERROR: SEED file not found: {seed_path}")
        return False
    
    try:
        extractor = SEEDRolesExtractor(str(seed_path))
        data = extractor.extract_all_data()
        
        print(f"✓ Roles: {len(data['roles'])}")
        print(f"✓ Role hierarchies: {len(data['role_hierarchies'])}")
        print(f"✓ Role-reaction mappings: {len(data['role_reaction_mappings'])}")
        print(f"✓ Roles with reactions: {len(data['roles_with_reactions'])}")
        print(f"✓ Name index entries: {len(data['name_to_id_index'])}")
        print(f"✓ Subsystem info: {data['subsystem_info'].get('title', 'N/A')}")
        
        # Show sample role
        if data['roles']:
            sample_id = list(data['roles'].keys())[0]
            sample = data['roles'][sample_id]
            print(f"✓ Sample role: {sample_id} - {sample['name']}")
            print(f"  Normalized: {sample['normalized_name']}")
            print(f"  Reactions: {len(sample['xrefs'].get('seed_reactions', []))}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: SEED roles extractor failed: {e}")
        return False


def main():
    """Run all extractor tests."""
    print("Testing SEED unified ontology extractors...")
    
    results = []
    results.append(test_template_extractor())
    results.append(test_modelseed_extractor())
    results.append(test_seed_roles_extractor())
    
    print(f"\n=== TEST RESULTS ===")
    print(f"Template extractor: {'PASS' if results[0] else 'FAIL'}")
    print(f"ModelSEED extractor: {'PASS' if results[1] else 'FAIL'}")
    print(f"SEED roles extractor: {'PASS' if results[2] else 'FAIL'}")
    
    if all(results):
        print("\n✓ All extractors working correctly!")
        print("Ready to run: python build_seed_unified.py --validate")
        return True
    else:
        print("\n✗ Some extractors failed. Check file paths and dependencies.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)