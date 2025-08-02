#!/usr/bin/env python3
"""
Generate OBO format from SEED Unified Ontology

Creates a simplified OBO format version of the ontology for compatibility
with tools that prefer OBO over OWL.

Usage:
    python generate_obo.py
"""

import json
import os


def generate_obo():
    """Generate OBO format from the JSON summary"""
    print("📄 Generating OBO format...")
    
    # Load the JSON summary
    json_file = "output/seed_unified.json"
    if not os.path.exists(json_file):
        print(f"❌ JSON summary not found: {json_file}")
        return
    
    with open(json_file, 'r') as f:
        summary = json.load(f)
    
    obo_lines = []
    
    # OBO header
    metadata = summary['metadata']
    stats = summary['statistics']
    
    obo_lines.extend([
        "format-version: 1.2",
        f"ontology: seed",
        f"name: {metadata['name']}",
        f"description: {metadata['description']}",
        f"version: {metadata['version']}",
        f"date: {metadata['generated'][:10]}",  # Just the date part
        "",
        "! This OBO file was generated from the complete SEED Unified Ontology",
        f"! Statistics: {stats['compounds']:,} compounds, {stats['reactions']:,} reactions,",
        f"!            {stats['roles']:,} roles, {stats['subsystems']:,} subsystems, {stats['complexes']:,} complexes",
        f"! Total relationships: {sum(stats['relationships'].values()):,}",
        "",
        "! Standard relationship types used:",
        "! RO:0002327 enables",
        "! RO:0001019 contains", 
        "! RO:0002215 capable_of",
        "! RO:0000058 is_realized_by",
        "",
        "! Custom data properties:",
        "! seed:hasNormalizedForm - normalized role names for performance",
        "! seed:reactionType - reaction classification (spontaneous/universal/conditional)",
        ""
    ])
    
    # Note about full relationships
    obo_lines.extend([
        "! NOTE: This OBO file contains only basic term definitions.",
        "! For complete relationships and semantic properties, use the OWL version:",
        "! seed_unified.owl contains all " + f"{sum(stats['relationships'].values()):,}" + " relationships",
        "",
        "! ===================================================================", 
        "! TERMS",
        "! ===================================================================",
        ""
    ])
    
    # Simple term count summary
    obo_lines.extend([
        "[Term]",
        "id: SEED:summary",
        "name: SEED Unified Ontology Summary",
        f"def: \"Complete SEED ontology with {stats['compounds']:,} compounds, {stats['reactions']:,} reactions, {stats['roles']:,} roles, {stats['subsystems']:,} subsystems, and {stats['complexes']:,} complexes. Generated from ModelSEED templates with semantic relationships using standard RO properties.\" []",
        f"comment: For complete ontology with all {sum(stats['relationships'].values()):,} relationships, use seed_unified.owl",
        "",
        "! End of basic OBO format",
        "! For full ontology functionality, use the OWL version which includes:",
        f"! - All {sum(stats['relationships'].values()):,} semantic relationships",
        "! - Performance-optimized normalized forms",
        "! - Standard RO property mappings", 
        "! - Direct compatibility with reasoning tools",
        ""
    ])
    
    # Write OBO file
    obo_file = "output/seed_unified.obo"
    with open(obo_file, 'w') as f:
        f.write('\n'.join(obo_lines))
    
    print(f"   ✅ Generated {obo_file}")
    
    # File size
    size_kb = os.path.getsize(obo_file) / 1024
    print(f"   📁 Size: {size_kb:.1f} KB")
    
    print(f"\n💡 Note: This OBO file provides basic compatibility.")
    print(f"   For complete ontology functionality with all {sum(stats['relationships'].values()):,} relationships,")
    print(f"   use seed_unified.owl which contains the full semantic model.")


if __name__ == "__main__":
    generate_obo()