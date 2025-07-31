#!/usr/bin/env python3
"""
Test data processing and integration without PyOBO dependencies.

This script tests the complete data extraction and processing pipeline
to ensure all components work together correctly.
"""

import sys
import json
from pathlib import Path

# Add extractors to Python path
sys.path.insert(0, str(Path(__file__).parent))

from extractors import TemplateExtractor, ModelSEEDExtractor, SEEDRolesExtractor


def test_data_integration():
    """Test integration of all three data sources."""
    print("=== Testing Data Integration ===")
    
    # Define source paths
    base_dir = Path(__file__).parent.parent
    template_path = base_dir / "enhanced_templates" / "GramNegModelTemplateV6_with_ontology.json"
    modelseed_path = base_dir / "json" / "modelseed.json.gz"
    seed_path = base_dir / "json" / "seed.json"
    
    try:
        # Extract all data
        print("1. Extracting template data...")
        template_extractor = TemplateExtractor(str(template_path))
        template_data = template_extractor.extract_all_data()
        
        print("2. Extracting ModelSEED data...")
        modelseed_extractor = ModelSEEDExtractor(str(modelseed_path))
        modelseed_data = modelseed_extractor.extract_all_data()
        
        print("3. Extracting SEED roles data...")
        seed_extractor = SEEDRolesExtractor(str(seed_path))
        seed_data = seed_extractor.extract_all_data()
        
        # Test data integration scenarios
        print("4. Testing data integration scenarios...")
        
        # Test 1: Role name matching
        template_roles = set(template_data['roles'].keys())
        seed_role_names = seed_data['name_to_id_index']
        
        # Try to match template roles to SEED roles by name
        template_role_names = [template_data['roles'][role_id]['name'] for role_id in template_roles]
        
        # Normalize template role names for matching
        temp_extractor = seed_extractor
        
        matched_roles = 0
        for template_role_name in template_role_names[:100]:  # Test sample
            normalized = temp_extractor._normalize_role_name(template_role_name)
            if normalized in seed_role_names:
                matched_roles += 1
        
        print(f"✓ Role matching test: {matched_roles}/100 template roles matched to SEED")
        
        # Test 2: Reaction coverage
        template_reactions = set(template_data['reactions'].keys())
        modelseed_reactions = set(modelseed_data['reactions'].keys())
        
        common_reactions = template_reactions.intersection(modelseed_reactions)
        reaction_coverage = len(common_reactions) / len(template_reactions) * 100
        
        print(f"✓ Reaction coverage: {len(common_reactions)}/{len(template_reactions)} ({reaction_coverage:.1f}%)")
        
        # Test 3: Complex-role relationships
        complex_role_rels = template_data['complex_role_relationships']
        unique_complexes = set([rel[0] for rel in complex_role_rels])
        unique_roles = set([rel[1] for rel in complex_role_rels])
        
        print(f"✓ Complex-role network: {len(unique_complexes)} complexes connected to {len(unique_roles)} roles")
        
        # Test 4: Cross-reference richness
        compound_xrefs = modelseed_data['compound_xrefs_summary']
        total_compounds = len(modelseed_data['compounds'])
        
        xref_coverage = {}
        for db, count in compound_xrefs.items():
            xref_coverage[db] = f"{count}/{total_compounds} ({count/total_compounds*100:.1f}%)"
        
        print(f"✓ Compound cross-references: {xref_coverage}")
        
        # Test 5: Role-reaction mappings
        role_reaction_mappings = seed_data['role_reaction_mappings']
        roles_with_reactions = len([r for r in role_reaction_mappings.values() if r])
        total_roles = len(seed_data['roles'])
        
        print(f"✓ Role-reaction mappings: {roles_with_reactions}/{total_roles} ({roles_with_reactions/total_roles*100:.1f}%) roles have reactions")
        
        # Generate integration summary
        integration_summary = {
            'data_sources': {
                'template': {
                    'complexes': len(template_data['complexes']),
                    'reactions': len(template_data['reactions']),
                    'roles': len(template_data['roles']),
                    'complex_role_relationships': len(template_data['complex_role_relationships'])
                },
                'modelseed': {
                    'compounds': len(modelseed_data['compounds']),
                    'reactions': len(modelseed_data['reactions']),
                    'compound_xrefs': compound_xrefs
                },
                'seed_roles': {
                    'roles': len(seed_data['roles']),
                    'roles_with_reactions': roles_with_reactions,
                    'role_reaction_mappings': len(role_reaction_mappings)
                }
            },
            'integration_metrics': {
                'reaction_coverage_percent': reaction_coverage,
                'roles_with_reactions_percent': roles_with_reactions/total_roles*100,
                'sample_role_matches': matched_roles
            },
            'expected_ontology_terms': {
                'roles': len(seed_data['roles']),
                'compounds': len(modelseed_data['compounds']),
                'reactions': len(modelseed_data['reactions']),
                'complexes': len(template_data['complexes']),
                'total': len(seed_data['roles']) + len(modelseed_data['compounds']) + len(modelseed_data['reactions']) + len(template_data['complexes'])
            }
        }
        
        # Save integration summary
        output_dir = Path(__file__).parent / "test_output"
        output_dir.mkdir(exist_ok=True)
        
        summary_file = output_dir / "integration_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(integration_summary, f, indent=2)
        
        print(f"✓ Integration summary saved to: {summary_file}")
        print(f"✓ Expected ontology size: ~{integration_summary['expected_ontology_terms']['total']:,} terms")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Data integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_intermediate_file_generation():
    """Test generation of intermediate files for PyOBO builder."""
    print("\n=== Testing Intermediate File Generation ===")
    
    try:
        # Create intermediate directory
        intermediate_dir = Path(__file__).parent / "intermediate"
        intermediate_dir.mkdir(exist_ok=True)
        
        # Define source paths
        base_dir = Path(__file__).parent.parent
        template_path = base_dir / "enhanced_templates" / "GramNegModelTemplateV6_with_ontology.json"
        modelseed_path = base_dir / "json" / "modelseed.json.gz"
        seed_path = base_dir / "json" / "seed.json"
        
        # Extract and save data
        print("1. Generating template intermediate file...")
        template_extractor = TemplateExtractor(str(template_path))
        template_data = template_extractor.extract_all_data()
        
        template_file = intermediate_dir / "template_data.json"
        with open(template_file, 'w') as f:
            json.dump(template_data, f, indent=2)
        print(f"✓ Saved: {template_file}")
        
        print("2. Generating ModelSEED intermediate file...")
        modelseed_extractor = ModelSEEDExtractor(str(modelseed_path))
        modelseed_data = modelseed_extractor.extract_all_data()
        
        modelseed_file = intermediate_dir / "modelseed_data.json"
        with open(modelseed_file, 'w') as f:
            json.dump(modelseed_data, f, indent=2)
        print(f"✓ Saved: {modelseed_file}")
        
        print("3. Generating SEED roles intermediate file...")
        seed_extractor = SEEDRolesExtractor(str(seed_path))
        seed_data = seed_extractor.extract_all_data()
        
        seed_file = intermediate_dir / "seed_roles_data.json"
        with open(seed_file, 'w') as f:
            json.dump(seed_data, f, indent=2)
        print(f"✓ Saved: {seed_file}")
        
        # Generate summary
        extraction_summary = {
            'files_generated': [
                str(template_file),
                str(modelseed_file),
                str(seed_file)
            ],
            'data_summary': {
                'template_complexes': len(template_data['complexes']),
                'modelseed_compounds': len(modelseed_data['compounds']),
                'modelseed_reactions': len(modelseed_data['reactions']),
                'seed_roles': len(seed_data['roles'])
            }
        }
        
        summary_file = intermediate_dir / "extraction_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(extraction_summary, f, indent=2)
        print(f"✓ Saved: {summary_file}")
        
        print(f"✓ All intermediate files ready for PyOBO builder")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Intermediate file generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all data processing tests."""
    print("Testing SEED unified ontology data processing...")
    
    results = []
    results.append(test_data_integration())
    results.append(test_intermediate_file_generation())
    
    print(f"\n=== TEST RESULTS ===")
    print(f"Data integration: {'PASS' if results[0] else 'FAIL'}")
    print(f"Intermediate files: {'PASS' if results[1] else 'FAIL'}")
    
    if all(results):
        print("\n✓ All data processing tests passed!")
        print("✓ System is ready for ontology generation")
        print("\nNext steps:")
        print("  1. Install PyOBO dependencies: pip install -r requirements.txt")
        print("  2. Run full build: python build_seed_unified.py --validate")
    else:
        print("\n✗ Some tests failed. Check error messages above.")
    
    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)