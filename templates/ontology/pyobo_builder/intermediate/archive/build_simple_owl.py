#!/usr/bin/env python3
"""
Simple OWL builder for SEED unified ontology.

This creates a basic OWL file without PyOBO dependencies,
demonstrating the complete pipeline and providing immediate output.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add extractors to Python path
sys.path.insert(0, str(Path(__file__).parent))

from extractors import TemplateExtractor, ModelSEEDExtractor, SEEDRolesExtractor


class SimpleOWLBuilder:
    """Simple OWL builder without PyOBO dependencies."""
    
    def __init__(self, source_dir: Path, output_dir: Path):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define namespaces
        self.base_uri = "http://purl.obolibrary.org/obo/seed_unified/"
        self.seed_prefix = "seed_unified"
        
    def extract_all_data(self) -> Dict[str, Any]:
        """Extract data from all sources."""
        print("Extracting data from all sources...")
        
        # Define source paths
        template_path = self.source_dir / "enhanced_templates" / "GramNegModelTemplateV6_with_ontology.json"
        modelseed_path = self.source_dir / "json" / "modelseed.json.gz"
        seed_path = self.source_dir / "json" / "seed.json"
        
        # Extract data
        template_extractor = TemplateExtractor(str(template_path))
        template_data = template_extractor.extract_all_data()
        
        modelseed_extractor = ModelSEEDExtractor(str(modelseed_path))
        modelseed_data = modelseed_extractor.extract_all_data()
        
        seed_extractor = SEEDRolesExtractor(str(seed_path))
        seed_data = seed_extractor.extract_all_data()
        
        return {
            'template': template_data,
            'modelseed': modelseed_data,
            'seed_roles': seed_data
        }
    
    def escape_xml(self, text: str) -> str:
        """Escape XML special characters."""
        if not text:
            return ""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&apos;'))
    
    def generate_owl_header(self) -> str:
        """Generate OWL file header."""
        timestamp = datetime.now().isoformat()
        
        return f'''<?xml version="1.0"?>
<rdf:RDF xmlns="http://purl.obolibrary.org/obo/seed_unified.owl#"
     xml:base="http://purl.obolibrary.org/obo/seed_unified.owl"
     xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:obo="http://purl.obolibrary.org/obo/"
     xmlns:owl="http://www.w3.org/2002/07/owl#"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:xml="http://www.w3.org/XML/1998/namespace"
     xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
     xmlns:seed_unified="http://purl.obolibrary.org/obo/seed_unified/">
    <owl:Ontology rdf:about="http://purl.obolibrary.org/obo/seed_unified.owl">
        <dc:title>SEED Unified Ontology</dc:title>
        <dc:description>Unified ontology combining SEED roles, ModelSEED compounds/reactions, and template complexes</dc:description>
        <dc:creator>SEED Unified Ontology Builder</dc:creator>
        <dc:date>{timestamp}</dc:date>
        <owl:versionInfo>2025-01-30</owl:versionInfo>
    </owl:Ontology>

    <!-- Object Properties -->
    <owl:ObjectProperty rdf:about="{self.base_uri}role_enables_reaction">
        <rdfs:label>role enables reaction</rdfs:label>
        <rdfs:comment>A role that enables a biochemical reaction to occur</rdfs:comment>
    </owl:ObjectProperty>

    <owl:ObjectProperty rdf:about="{self.base_uri}complex_has_role">
        <rdfs:label>complex has role</rdfs:label>
        <rdfs:comment>A protein complex that has a specific functional role</rdfs:comment>
    </owl:ObjectProperty>

    <owl:ObjectProperty rdf:about="{self.base_uri}complex_enables_reaction">
        <rdfs:label>complex enables reaction</rdfs:label>
        <rdfs:comment>A protein complex that enables a biochemical reaction</rdfs:comment>
    </owl:ObjectProperty>

    <!-- Data Properties -->
    <owl:DatatypeProperty rdf:about="{self.base_uri}has_normalized_form">
        <rdfs:label>has normalized form</rdfs:label>
        <rdfs:comment>Links an entity to its normalized representation for performance</rdfs:comment>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
    </owl:DatatypeProperty>

    <owl:DatatypeProperty rdf:about="{self.base_uri}confidence">
        <rdfs:label>confidence</rdfs:label>
        <rdfs:comment>Confidence score for the entity or relationship</rdfs:comment>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#float"/>
    </owl:DatatypeProperty>

'''
    
    def generate_owl_footer(self) -> str:
        """Generate OWL file footer."""
        return "\n</rdf:RDF>"
    
    def generate_role_terms(self, data: Dict) -> str:
        """Generate OWL terms for SEED roles."""
        if 'seed_roles' not in data or 'roles' not in data['seed_roles']:
            return ""
        
        owl_content = "\n    <!-- SEED Roles -->\n"
        roles = data['seed_roles']['roles']
        
        for role_id, role_data in list(roles.items())[:1000]:  # Limit for demo
            term_uri = f"{self.base_uri}role_{role_id}"
            name = self.escape_xml(role_data.get('name', ''))
            normalized_name = self.escape_xml(role_data.get('normalized_name', ''))
            
            owl_content += f'''
    <owl:Class rdf:about="{term_uri}">
        <rdfs:label>{name}</rdfs:label>
        <rdfs:comment>SEED functional role: {name}</rdfs:comment>'''
            
            if normalized_name:
                owl_content += f'''
        <seed_unified:has_normalized_form>{normalized_name}</seed_unified:has_normalized_form>'''
            
            # Add reaction relationships
            if 'xrefs' in role_data and 'seed_reactions' in role_data['xrefs']:
                for reaction_id in role_data['xrefs']['seed_reactions']:
                    owl_content += f'''
        <seed_unified:role_enables_reaction rdf:resource="{self.base_uri}reaction_{reaction_id}"/>'''
            
            owl_content += "\n    </owl:Class>"
        
        return owl_content
    
    def generate_compound_terms(self, data: Dict) -> str:
        """Generate OWL terms for ModelSEED compounds."""
        if 'modelseed' not in data or 'compounds' not in data['modelseed']:
            return ""
        
        owl_content = "\n    <!-- ModelSEED Compounds -->\n"
        compounds = data['modelseed']['compounds']
        
        for compound_id, compound_data in list(compounds.items())[:1000]:  # Limit for demo
            term_uri = f"{self.base_uri}compound_{compound_id}"
            name = self.escape_xml(compound_data.get('name', ''))
            
            owl_content += f'''
    <owl:Class rdf:about="{term_uri}">
        <rdfs:label>{name}</rdfs:label>
        <rdfs:comment>ModelSEED compound: {name}</rdfs:comment>'''
            
            # Add cross-references
            if 'xrefs' in compound_data:
                for db, refs in compound_data['xrefs'].items():
                    for ref in refs[:3]:  # Limit cross-refs
                        if db == 'chebi':
                            owl_content += f'''
        <rdfs:seeAlso rdf:resource="http://purl.obolibrary.org/obo/{ref}"/>'''
                        elif db == 'kegg':
                            owl_content += f'''
        <rdfs:seeAlso rdf:resource="https://www.kegg.jp/entry/{ref}"/>'''
            
            owl_content += "\n    </owl:Class>"
        
        return owl_content
    
    def generate_reaction_terms(self, data: Dict) -> str:
        """Generate OWL terms for ModelSEED reactions."""
        if 'modelseed' not in data or 'reactions' not in data['modelseed']:
            return ""
        
        owl_content = "\n    <!-- ModelSEED Reactions -->\n"
        reactions = data['modelseed']['reactions']
        
        for reaction_id, reaction_data in list(reactions.items())[:1000]:  # Limit for demo
            term_uri = f"{self.base_uri}reaction_{reaction_id}"
            name = self.escape_xml(reaction_data.get('name', ''))
            
            owl_content += f'''
    <owl:Class rdf:about="{term_uri}">
        <rdfs:label>{name}</rdfs:label>
        <rdfs:comment>ModelSEED reaction: {name}</rdfs:comment>
    </owl:Class>'''
        
        return owl_content
    
    def generate_complex_terms(self, data: Dict) -> str:
        """Generate OWL terms for template complexes."""
        if 'template' not in data or 'complexes' not in data['template']:
            return ""
        
        owl_content = "\n    <!-- Template Complexes -->\n"
        complexes = data['template']['complexes']
        
        for complex_id, complex_data in list(complexes.items())[:1000]:  # Limit for demo
            term_uri = f"{self.base_uri}complex_{complex_id}"
            name = self.escape_xml(complex_data.get('name', ''))
            confidence = complex_data.get('confidence', 0)
            
            owl_content += f'''
    <owl:Class rdf:about="{term_uri}">
        <rdfs:label>{name}</rdfs:label>
        <rdfs:comment>ModelSEED protein complex: {name}</rdfs:comment>
        <seed_unified:confidence rdf:datatype="http://www.w3.org/2001/XMLSchema#float">{confidence}</seed_unified:confidence>'''
            
            # Add role relationships
            for role_id in complex_data.get('roles', []):
                owl_content += f'''
        <seed_unified:complex_has_role rdf:resource="{self.base_uri}role_{role_id}"/>'''
            
            owl_content += "\n    </owl:Class>"
        
        return owl_content
    
    def build_owl_file(self, data: Dict) -> str:
        """Build complete OWL file."""
        print("Building OWL file...")
        
        owl_content = self.generate_owl_header()
        owl_content += self.generate_role_terms(data)
        owl_content += self.generate_compound_terms(data)
        owl_content += self.generate_reaction_terms(data)
        owl_content += self.generate_complex_terms(data)
        owl_content += self.generate_owl_footer()
        
        return owl_content
    
    def build_json_summary(self, data: Dict) -> Dict:
        """Build JSON summary of the ontology."""
        print("Building JSON summary...")
        
        summary = {
            'ontology_info': {
                'name': 'SEED Unified Ontology',
                'version': '2025-01-30',
                'description': 'Unified ontology combining SEED roles, ModelSEED compounds/reactions, and template complexes',
                'base_uri': self.base_uri,
                'generated_date': datetime.now().isoformat()
            },
            'statistics': {
                'total_roles': len(data['seed_roles']['roles']) if 'seed_roles' in data else 0,
                'total_compounds': len(data['modelseed']['compounds']) if 'modelseed' in data else 0,
                'total_reactions': len(data['modelseed']['reactions']) if 'modelseed' in data else 0,
                'total_complexes': len(data['template']['complexes']) if 'template' in data else 0,
                'complex_role_relationships': len(data['template']['complex_role_relationships']) if 'template' in data else 0
            },
            'sample_terms': {
                'roles': [],
                'compounds': [],
                'reactions': [],
                'complexes': []
            }
        }
        
        # Add sample terms
        if 'seed_roles' in data:
            for i, (role_id, role_data) in enumerate(data['seed_roles']['roles'].items()):
                if i >= 5:
                    break
                summary['sample_terms']['roles'].append({
                    'id': f"role_{role_id}",
                    'name': role_data.get('name', ''),
                    'uri': f"{self.base_uri}role_{role_id}"
                })
        
        if 'modelseed' in data:
            for i, (compound_id, compound_data) in enumerate(data['modelseed']['compounds'].items()):
                if i >= 5:
                    break
                summary['sample_terms']['compounds'].append({
                    'id': f"compound_{compound_id}",
                    'name': compound_data.get('name', ''),
                    'uri': f"{self.base_uri}compound_{compound_id}"
                })
        
        return summary
    
    def build_complete_ontology(self) -> Dict[str, Any]:
        """Build the complete ontology and save files."""
        print("=== Building SEED Unified Ontology (Simple Version) ===")
        
        # Extract data
        data = self.extract_all_data()
        
        # Build OWL file
        owl_content = self.build_owl_file(data)
        
        # Save OWL file
        owl_file = self.output_dir / "seed_unified_demo.owl"
        with open(owl_file, 'w', encoding='utf-8') as f:
            f.write(owl_content)
        print(f"✓ Saved OWL file: {owl_file}")
        
        # Build and save JSON summary
        summary = self.build_json_summary(data)
        summary_file = self.output_dir / "seed_unified_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"✓ Saved JSON summary: {summary_file}")
        
        print(f"✓ Generated ontology with ~{summary['statistics']['total_roles'] + summary['statistics']['total_compounds'] + summary['statistics']['total_reactions'] + summary['statistics']['total_complexes']:,} total terms")
        print(f"  - {summary['statistics']['total_roles']:,} SEED roles")
        print(f"  - {summary['statistics']['total_compounds']:,} ModelSEED compounds")
        print(f"  - {summary['statistics']['total_reactions']:,} ModelSEED reactions")
        print(f"  - {summary['statistics']['total_complexes']:,} template complexes")
        
        return {
            'success': True,
            'owl_file': str(owl_file),
            'summary_file': str(summary_file),
            'statistics': summary['statistics']
        }


def main():
    """Main entry point."""
    print("SEED Unified Ontology Builder (Simple Version)")
    print("=" * 50)
    
    # Setup paths
    source_dir = Path(__file__).parent.parent
    output_dir = Path(__file__).parent / "output"
    
    # Build ontology
    builder = SimpleOWLBuilder(source_dir, output_dir)
    results = builder.build_complete_ontology()
    
    if results['success']:
        print("\n" + "=" * 50)
        print("BUILD COMPLETED SUCCESSFULLY!")
        print(f"OWL file: {results['owl_file']}")
        print(f"Summary: {results['summary_file']}")
        print("\nThis demonstrates the complete SEED unified ontology system.")
        print("For full PyOBO version, install dependencies and run build_seed_unified.py")
    else:
        print("Build failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())