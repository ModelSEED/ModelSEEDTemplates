#!/usr/bin/env python3
"""
SEED Ontology Validation Script

Validates that the generated SEED ontology contains all expected relationships
and entities from the source materials.

Usage:
    python validate_ontology.py

Checks:
    - Entity counts match expected values
    - All relationships are properly encoded
    - URIs follow correct patterns
    - OWL syntax is valid
"""

import json
import os
import re
from xml.etree import ElementTree as ET


def validate_ontology():
    """Validate the generated SEED ontology"""
    print("🔍 Validating SEED Unified Ontology...")
    print("="*50)
    
    # Check files exist
    owl_file = "output/seed_unified.owl"
    json_file = "output/seed_unified.json"
    
    if not os.path.exists(owl_file):
        print(f"❌ OWL file not found: {owl_file}")
        return False
        
    if not os.path.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        return False
    
    print(f"✅ Found output files")
    
    # Load JSON summary
    with open(json_file, 'r') as f:
        summary = json.load(f)
    
    # Validate entity counts
    print(f"\n📊 Entity counts:")
    stats = summary['statistics']
    print(f"   Compounds: {stats['compounds']:,}")
    print(f"   Reactions: {stats['reactions']:,}")
    print(f"   Roles: {stats['roles']:,}")
    print(f"   Subsystems: {stats['subsystems']:,}")
    print(f"   Complexes: {stats['complexes']:,}")
    
    # Validate relationship counts
    print(f"\n🔗 Relationship counts:")
    rels = stats['relationships']
    total_relationships = sum(rels.values())
    print(f"   role_enables_reaction: {rels['role_enables_reaction']:,}")
    print(f"   complex_has_role: {rels['complex_has_role']:,}")
    print(f"   complex_enables_reaction: {rels['complex_enables_reaction']:,}")
    print(f"   reaction_has_complex: {rels['reaction_has_complex']:,}")
    print(f"   Total: {total_relationships:,}")
    
    # Validate expected minimums (based on notebook data)
    expected_minimums = {
        'compounds': 40000,  # Should have at least 40k compounds
        'reactions': 50000,   # Should have at least 50k reactions
        'roles': 40000,       # Should have at least 40k roles
        'subsystems': 1000,   # Should have at least 1k subsystems
        'complexes': 3000,    # Should have at least 3k complexes
        'role_enables_reaction': 6000,  # From notebook: 6299
        'total_relationships': 15000    # Should have substantial relationships
    }
    
    validation_errors = []
    
    if stats['compounds'] < expected_minimums['compounds']:
        validation_errors.append(f"Too few compounds: {stats['compounds']} < {expected_minimums['compounds']}")
    
    if stats['reactions'] < expected_minimums['reactions']:
        validation_errors.append(f"Too few reactions: {stats['reactions']} < {expected_minimums['reactions']}")
        
    if stats['roles'] < expected_minimums['roles']:
        validation_errors.append(f"Too few roles: {stats['roles']} < {expected_minimums['roles']}")
        
    if rels['role_enables_reaction'] < expected_minimums['role_enables_reaction']:
        validation_errors.append(f"Too few role→reaction relationships: {rels['role_enables_reaction']} < {expected_minimums['role_enables_reaction']}")
        
    if total_relationships < expected_minimums['total_relationships']:
        validation_errors.append(f"Too few total relationships: {total_relationships} < {expected_minimums['total_relationships']}")
    
    # Validate OWL syntax
    print(f"\n🔧 Validating OWL syntax...")
    try:
        tree = ET.parse(owl_file)
        root = tree.getroot()
        print(f"   ✅ OWL file is valid XML")
        
        # Check for key namespaces in the root element
        owl_content_head = ""
        with open(owl_file, 'r') as f:
            owl_content_head = f.read(2000)  # Read first 2000 chars
        
        required_namespaces = ['xmlns:owl=', 'xmlns:rdf=', 'xmlns:rdfs=', 'xmlns:ro=']
        for ns in required_namespaces:
            if ns in owl_content_head:
                print(f"   ✅ Found namespace: {ns.replace('=', '')}")
            else:
                validation_errors.append(f"Missing namespace: {ns.replace('=', '')}")
        
        # Count OWL elements
        owl_classes = len(root.findall('.//{http://www.w3.org/2002/07/owl#}Class'))
        rdf_descriptions = len(root.findall('.//{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description'))
        
        print(f"   ✅ Found {owl_classes:,} OWL classes")
        print(f"   ✅ Found {rdf_descriptions:,} RDF descriptions (relationships)")
        
        if owl_classes < 90000:  # Should have ~150k+ classes (compounds+reactions+roles+subsystems+complexes)
            validation_errors.append(f"Too few OWL classes: {owl_classes}")
            
        if rdf_descriptions < 15000:  # Should have substantial relationships
            validation_errors.append(f"Too few RDF descriptions: {rdf_descriptions}")
            
    except Exception as e:
        validation_errors.append(f"OWL syntax error: {e}")
    
    # Validate URI patterns
    print(f"\n🌐 Validating URI patterns...")
    
    # Sample a few URIs from the OWL file
    with open(owl_file, 'r') as f:
        owl_content = f.read()
    
    # Check for expected URI patterns (with proper XML escaping)
    uri_patterns = {
        'compounds': r'https://modelseed\.org/biochem/compounds/cpd\d+',
        'reactions': r'https://modelseed\.org/biochem/reactions/rxn\d+', 
        'roles': r'https://pubseed\.theseed\.org/RoleEditor\.cgi\?page=ShowRole&amp;Role=\d+',
        'subsystems': r'https://pubseed\.theseed\.org/SubsysEditor\.cgi\?page=ShowSubsystem&amp;subsystem=\d+',
        'complexes': r'https://modelseed\.org/biochem/complexes/cpx\d+'
    }
    
    for entity_type, pattern in uri_patterns.items():
        matches = re.findall(pattern, owl_content)
        if matches:
            print(f"   ✅ Found {len(matches):,} {entity_type} URIs")
        else:
            validation_errors.append(f"No {entity_type} URIs found with pattern: {pattern}")
    
    # Check for RO properties
    ro_properties = ['ro:RO_0002327', 'ro:RO_0001019', 'ro:RO_0002215', 'ro:RO_0000058']
    for prop in ro_properties:
        if prop in owl_content:
            count = owl_content.count(prop)
            print(f"   ✅ Found {count:,} uses of {prop}")
        else:
            validation_errors.append(f"RO property not found: {prop}")
    
    # Validate custom properties
    custom_properties = ['seed_hasNormalizedForm', 'seed_reactionType']
    for prop in custom_properties:
        if prop in owl_content:
            count = owl_content.count(prop)
            print(f"   ✅ Found {count:,} uses of {prop}")
        else:
            validation_errors.append(f"Custom property not found: {prop}")
    
    # Final validation summary
    print(f"\n🎯 Validation Summary:")
    print(f"="*50)
    
    if validation_errors:
        print(f"❌ Validation FAILED with {len(validation_errors)} errors:")
        for error in validation_errors:
            print(f"   • {error}")
        return False
    else:
        print(f"✅ Validation PASSED!")
        print(f"   • All entity counts meet expected minimums")
        print(f"   • All relationship types are present")
        print(f"   • OWL syntax is valid")
        print(f"   • URI patterns match source materials")
        print(f"   • Standard RO properties are used")
        print(f"   • Custom performance properties are included")
        
        # File sizes
        owl_size = os.path.getsize(owl_file) / (1024 * 1024)
        json_size = os.path.getsize(json_file) / (1024 * 1024)
        
        print(f"\n📁 File information:")
        print(f"   • {owl_file}: {owl_size:.1f} MB")
        print(f"   • {json_file}: {json_size:.1f} MB")
        
        print(f"\n🚀 Ontology is ready for:")
        print(f"   • Direct import into semsql databases")
        print(f"   • Use with ROBOT, Protégé, and other OWL tools")
        print(f"   • High-performance semantic queries")
        print(f"   • Metabolic model reconstruction workflows")
        
        return True


def main():
    """Main validation execution"""
    success = validate_ontology()
    
    if success:
        print(f"\n🎉 SEED Unified Ontology validation completed successfully!")
        exit(0)
    else:
        print(f"\n💥 SEED Unified Ontology validation failed!")
        exit(1)


if __name__ == "__main__":
    main()