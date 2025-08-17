#!/usr/bin/env python3
"""
Extract Parquet Files from SemSQL Database with Predicate Simplification

Extracts statements and term associations from the SemSQL database to parquet format.
Performs post-processing to convert full URI predicates to simplified names.

Converts:
- <https://modelseed.org/ontology/enables_reaction> → enables_reaction
- <https://modelseed.org/ontology/has_role> → has_role
- <https://modelseed.org/ontology/has_complex> → has_complex
- <https://modelseed.org/ontology/reaction_type> → reaction_type
- <http://www.w3.org/2002/07/owl#sameAs> → owl:sameAs

Usage:
    python extract_parquet.py
    
Output:
    - ontology/statements.parquet (with simplified predicates)
    - ontology/term_associations.parquet (unchanged)
"""

import sqlite3
import pandas as pd
import sys
from pathlib import Path

def extract_statements(db_path):
    """
    Extract all statements from database and simplify predicates.
    
    Args:
        db_path: Path to SemSQL database
        
    Returns:
        DataFrame with simplified predicates
    """
    print("📂 Extracting statements from database...")
    
    conn = sqlite3.connect(db_path)
    
    # Load all statements
    df_statements = pd.read_sql_query(
        "SELECT stanza, subject, predicate, object, value, datatype, language FROM statements", 
        conn
    )
    
    print(f"   Loaded {len(df_statements):,} total statements")
    
    # Show original predicate counts
    original_counts = df_statements['predicate'].value_counts()
    key_full_predicates = [
        '<https://modelseed.org/ontology/enables_reaction>',
        '<https://modelseed.org/ontology/has_role>',
        '<https://modelseed.org/ontology/has_complex>',
        '<https://modelseed.org/ontology/reaction_type>',
        '<http://www.w3.org/2002/07/owl#sameAs>'
    ]
    
    print(f"\n📊 Original predicate counts (full URIs):")
    for pred in key_full_predicates:
        if pred in original_counts:
            print(f"   {pred}: {original_counts[pred]:,}")
    
    # Post-process: Convert full URIs to simplified names
    print(f"\n🔄 Post-processing: Converting to simplified predicates...")
    predicate_mapping = {
        '<https://modelseed.org/ontology/enables_reaction>': 'enables_reaction',
        '<https://modelseed.org/ontology/has_role>': 'has_role',
        '<https://modelseed.org/ontology/has_complex>': 'has_complex',
        '<https://modelseed.org/ontology/reaction_type>': 'reaction_type',
        '<http://www.w3.org/2002/07/owl#sameAs>': 'owl:sameAs'
    }
    
    # Apply mapping
    df_statements['predicate'] = df_statements['predicate'].replace(predicate_mapping)
    
    # Show simplified predicate counts
    simplified_counts = df_statements['predicate'].value_counts()
    key_simplified_predicates = [
        'enables_reaction',
        'has_role',
        'has_complex',
        'reaction_type',
        'owl:sameAs'
    ]
    
    print(f"\n📊 Simplified predicate counts (post-processed):")
    for pred in key_simplified_predicates:
        if pred in simplified_counts:
            print(f"   {pred}: {simplified_counts[pred]:,}")
        else:
            print(f"   {pred}: 0")
    
    conn.close()
    return df_statements

def extract_term_associations():
    """
    Extract gene-role term associations from backup.
    
    Returns:
        DataFrame with term associations
    """
    print(f"\n📂 Loading term associations...")
    
    # Load from backup zip (term associations are pre-computed)
    try:
        df_terms = pd.read_parquet('backup_before_rebuild.zip')
        # Try to find the term associations in the zip
        import zipfile
        with zipfile.ZipFile('backup_before_rebuild.zip', 'r') as zip_ref:
            # Extract term associations temporarily
            zip_ref.extract('backup_before_rebuild/term_associations.parquet', '.')
            df_terms = pd.read_parquet('backup_before_rebuild/term_associations.parquet')
            # Clean up temporary file
            import os
            os.remove('backup_before_rebuild/term_associations.parquet')
            os.rmdir('backup_before_rebuild')
    except:
        # Fallback: try to load from examples folder
        df_terms = pd.read_parquet('examples/term_associations.parquet')
    
    print(f"   Loaded {len(df_terms):,} gene-role mappings")
    print(f"   Unique genes: {df_terms['gene_id'].nunique():,}")
    print(f"   Unique roles: {df_terms['seed_role_id'].nunique():,}")
    
    return df_terms

def main():
    """Extract parquet files with predicate post-processing."""
    
    print("SEED Ontology Parquet Extraction with Predicate Simplification")
    print("=" * 65)
    print("🔄 POST-PROCESSING APPROACH")
    print("   Database stores full URIs, converted to simplified names during extraction")
    print()
    
    db_path = "ontology/seed_unified.db"
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        print("   Run the ontology builder first.")
        sys.exit(1)
    
    try:
        # Extract statements (with post-processing)
        df_statements = extract_statements(db_path)
        
        # Extract term associations
        df_terms = extract_term_associations()
        
        # Save parquet files directly to examples folder
        print(f"\n💾 Saving parquet files to examples folder...")
        
        statements_path = "examples/statements.parquet"
        df_statements.to_parquet(statements_path, index=False)
        print(f"   ✅ {statements_path} ({len(df_statements):,} statements)")
        
        terms_path = "examples/term_associations.parquet"
        df_terms.to_parquet(terms_path, index=False)
        print(f"   ✅ {terms_path} ({len(df_terms):,} associations)")
        
        print(f"\n🎉 Extraction complete!")
        print(f"   Post-processed to simplified predicates:")
        print(f"   - enables_reaction")
        print(f"   - has_role")
        print(f"   - has_complex")
        print(f"   - reaction_type")
        print(f"   - owl:sameAs")
        print(f"\n🚀 Ready for production notebooks!")
        
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()