#!/usr/bin/env python3
"""
Complete PyOBO SEED Ontology Builder

Creates a unified SEED ontology with all relationships stored in OWL using standard RO properties.
Extracts entities and relationships from ModelSEED template, modelseed.json.gz, and seed.json.

Usage:
    python build_seed_ontology.py

Output:
    output/seed_unified.owl - Complete OWL ontology
    output/seed_unified.json - JSON representation
    output/seed_unified.obo - OBO format
"""

import json
import gzip
import os
import re
from collections import defaultdict
from typing import Dict, List, Set, Any, Optional
import pyobo
from pyobo import Ontology, Term, Reference
from pyobo.sources import get_ontology


def normalize_role(s: str) -> str:
    """Normalize role exactly as ModelSEEDpy does"""
    s = s.strip().lower()
    s = re.sub(r"[\W_]+", "", s)
    return s


class SEEDOntologyBuilder:
    """Complete SEED ontology builder using PyOBO"""
    
    def __init__(self):
        self.data_dir = "/Users/jplfaria/repos/ModelSEEDTemplates/templates/ontology"
        self.relationships_file = "/Users/jplfaria/repos/play/ontology-work/build_model_from_database/ontology_export/ontology_relationships.json"
        self.output_dir = "output"
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Data containers
        self.compounds = {}
        self.reactions = {}
        self.roles = {}
        self.subsystems = {}
        self.complexes = {}
        
        # Relationship containers
        self.role_enables_reaction = defaultdict(set)
        self.complex_has_role = defaultdict(set)
        self.complex_enables_reaction = defaultdict(set)
        self.reaction_has_complex = defaultdict(set)
        self.spontaneous_reactions = set()
        self.universal_reactions = set()
        
        # Normalization cache for performance
        self.role_normalizations = {}
        
    def load_relationships(self):
        """Load ontology relationships from notebook export"""
        print("🔗 Loading ontology relationships...")
        
        with open(self.relationships_file, 'r') as f:
            relationships = json.load(f)
        
        # Convert to sets for efficient operations
        for role_id, reactions in relationships['role_enables_reaction'].items():
            self.role_enables_reaction[role_id] = set(reactions)
            
        for complex_id, roles in relationships['complex_has_role'].items():
            self.complex_has_role[complex_id] = set(roles)
            
        for complex_id, reactions in relationships['complex_enables_reaction'].items():
            self.complex_enables_reaction[complex_id] = set(reactions)
            
        for reaction_id, complexes in relationships['reaction_has_complex'].items():
            self.reaction_has_complex[reaction_id] = set(complexes)
            
        self.spontaneous_reactions = set(relationships['spontaneous_reactions'])
        self.universal_reactions = set(relationships['universal_reactions'])
        
        print(f"   ✅ Loaded {len(self.role_enables_reaction)} role→reaction mappings")
        print(f"   ✅ Loaded {len(self.complex_has_role)} complex→role mappings")
        print(f"   ✅ Loaded {len(self.spontaneous_reactions)} spontaneous reactions")
        print(f"   ✅ Loaded {len(self.universal_reactions)} universal reactions")
        
    def load_compounds(self):
        """Load compounds from modelseed.json.gz"""
        print("🧪 Loading compounds from modelseed.json.gz...")
        
        modelseed_file = os.path.join(self.data_dir, "json", "modelseed.json.gz")
        with gzip.open(modelseed_file, 'rt') as f:
            modelseed_data = json.load(f)
        
        # Extract compounds with correct URIs
        if 'graphs' in modelseed_data:
            for graph in modelseed_data['graphs']:
                if 'nodes' in graph:
                    for node in graph['nodes']:
                        node_id = node.get('id', '')
                        if 'compounds' in node_id and node.get('type') == 'CLASS':
                            # Extract compound ID (e.g., cpd00001 from full URI)
                            cpd_id = node_id.split('/')[-1]
                            self.compounds[cpd_id] = {
                                'id': cpd_id,
                                'uri': node_id,  # Use original URI from source
                                'name': node.get('lbl', ''),
                                'xrefs': [xref.get('val', '') for xref in node.get('meta', {}).get('xrefs', [])]
                            }
        
        print(f"   ✅ Loaded {len(self.compounds)} compounds")
        
    def load_reactions(self):
        """Load reactions from modelseed.json.gz"""
        print("⚡ Loading reactions from modelseed.json.gz...")
        
        modelseed_file = os.path.join(self.data_dir, "json", "modelseed.json.gz")
        with gzip.open(modelseed_file, 'rt') as f:
            modelseed_data = json.load(f)
        
        # Extract reactions with correct URIs
        if 'graphs' in modelseed_data:
            for graph in modelseed_data['graphs']:
                if 'edges' in graph:
                    for edge in graph['edges']:
                        edge_id = edge.get('id', '')
                        if 'reactions' in edge_id:
                            # Extract reaction ID (e.g., rxn00001 from full URI)
                            rxn_id = edge_id.split('/')[-1]
                            
                            # Determine reaction type
                            reaction_type = 'conditional'  # default
                            if f'seed.reaction:{rxn_id}' in self.spontaneous_reactions:
                                reaction_type = 'spontaneous'
                            elif f'seed.reaction:{rxn_id}' in self.universal_reactions:
                                reaction_type = 'universal'
                            
                            self.reactions[rxn_id] = {
                                'id': rxn_id,
                                'uri': edge_id,  # Use original URI from source
                                'name': edge.get('lbl', ''),
                                'type': reaction_type,
                                'xrefs': [xref.get('val', '') for xref in edge.get('meta', {}).get('xrefs', [])]
                            }
        
        print(f"   ✅ Loaded {len(self.reactions)} reactions")
        print(f"      - Spontaneous: {len(self.spontaneous_reactions)}")
        print(f"      - Universal: {len(self.universal_reactions)}")
        print(f"      - Conditional: {len(self.reactions) - len(self.spontaneous_reactions) - len(self.universal_reactions)}")
        
    def load_roles_and_subsystems(self):
        """Load roles and subsystems from seed.json"""
        print("🎭 Loading roles and subsystems from seed.json...")
        
        seed_file = os.path.join(self.data_dir, "json", "seed.json")
        with open(seed_file, 'r') as f:
            seed_data = json.load(f)
        
        # Extract roles and subsystems with correct URIs
        if 'graphs' in seed_data:
            for graph in seed_data['graphs']:
                if 'nodes' in graph:
                    for node in graph['nodes']:
                        node_id = node.get('id', '')
                        node_type = node.get('type', '')
                        
                        if node_type == 'CLASS':
                            if 'ShowRole' in node_id:
                                # Extract role ID from URI
                                role_match = re.search(r'Role=(\d+)', node_id)
                                if role_match:
                                    role_id = role_match.group(1).zfill(13)  # Pad to 13 digits
                                    role_name = node.get('lbl', '')
                                    
                                    self.roles[role_id] = {
                                        'id': role_id,
                                        'uri': node_id,  # Use original URI from source
                                        'name': role_name,
                                        'xrefs': [xref.get('val', '') for xref in node.get('meta', {}).get('xrefs', [])]
                                    }
                                    
                                    # Store normalization for performance
                                    self.role_normalizations[role_id] = normalize_role(role_name)
                            
                            elif 'ShowSubsystem' in node_id:
                                # Extract subsystem ID from URI
                                subsys_match = re.search(r'subsystem=(\d+)', node_id)
                                if subsys_match:
                                    subsys_id = subsys_match.group(1).zfill(10)  # Pad to 10 digits
                                    
                                    self.subsystems[subsys_id] = {
                                        'id': subsys_id,
                                        'uri': node_id,  # Use original URI from source
                                        'name': node.get('lbl', ''),
                                        'xrefs': [xref.get('val', '') for xref in node.get('meta', {}).get('xrefs', [])]
                                    }
        
        print(f"   ✅ Loaded {len(self.roles)} roles")
        print(f"   ✅ Loaded {len(self.subsystems)} subsystems")
        
    def load_complexes_from_template(self):
        """Load complexes from enhanced template"""
        print("🔧 Loading complexes from enhanced template...")
        
        template_file = os.path.join(self.data_dir, "enhanced_templates", "GramNegModelTemplateV6_with_ontology.json")
        with open(template_file, 'r') as f:
            template = json.load(f)
        
        # Extract complexes
        for complex_data in template.get('complexes', []):
            complex_id = complex_data['id']
            seed_id = complex_data.get('seed_id', f'seed.complex:{complex_id}')
            
            # Generate proper URI
            if seed_id.startswith('seed.complex:'):
                cpx_id = seed_id.replace('seed.complex:', '')
                uri = f"https://modelseed.org/biochem/complexes/{cpx_id}"
            else:
                uri = f"https://modelseed.org/biochem/complexes/{complex_id}"
                
            self.complexes[complex_id] = {
                'id': complex_id,
                'seed_id': seed_id,
                'uri': uri,
                'name': complex_data.get('name', ''),
                'roles': []
            }
        
        print(f"   ✅ Loaded {len(self.complexes)} complexes")
        
    def create_ontology(self) -> Ontology:
        """Create PyOBO ontology with all entities and relationships"""
        print("🏗️  Creating PyOBO ontology...")
        
        # Create ontology with metadata
        ontology = Ontology(
            ontology='seed',
            name='Subsystems and Exchange Database (SEED) Unified Ontology',
            description='Complete SEED ontology with compounds, reactions, roles, subsystems, and complexes from ModelSEED templates',
            version='2.0'
        )
        
        print("   📦 Adding compound terms...")
        for cpd_id, compound in self.compounds.items():
            term = Term(
                reference=Reference(prefix='seed.compound', identifier=cpd_id, name=compound['name']),
                name=compound['name']
            )
            # Add cross-references
            for xref in compound['xrefs']:
                if xref.strip():
                    term.append_xref(xref.strip())
            ontology.append_term(term)
        
        print("   ⚡ Adding reaction terms...")
        for rxn_id, reaction in self.reactions.items():
            term = Term(
                reference=Reference(prefix='seed.reaction', identifier=rxn_id, name=reaction['name']),
                name=reaction['name']
            )
            
            # Add reaction type as annotation
            if reaction['type'] == 'spontaneous':
                term.append_annotation('reaction_type', 'spontaneous')
            elif reaction['type'] == 'universal':
                term.append_annotation('reaction_type', 'universal')
            else:
                term.append_annotation('reaction_type', 'conditional')
                
            # Add cross-references
            for xref in reaction['xrefs']:
                if xref.strip():
                    term.append_xref(xref.strip())
            ontology.append_term(term)
        
        print("   🎭 Adding role terms...")
        for role_id, role in self.roles.items():
            term = Term(
                reference=Reference(prefix='seed.role', identifier=role_id, name=role['name']),
                name=role['name']
            )
            
            # Add normalized form as data property
            normalized = self.role_normalizations.get(role_id, normalize_role(role['name']))
            term.append_annotation('hasNormalizedForm', normalized)
            
            # Add cross-references
            for xref in role['xrefs']:
                if xref.strip():
                    term.append_xref(xref.strip())
            ontology.append_term(term)
        
        print("   🗂️  Adding subsystem terms...")
        for subsys_id, subsystem in self.subsystems.items():
            term = Term(
                reference=Reference(prefix='seed.subsystem', identifier=subsys_id, name=subsystem['name']),
                name=subsystem['name']
            )
            # Add cross-references
            for xref in subsystem['xrefs']:
                if xref.strip():
                    term.append_xref(xref.strip())
            ontology.append_term(term)
        
        print("   🔧 Adding complex terms...")
        for cpx_id, complex_data in self.complexes.items():
            term = Term(
                reference=Reference(prefix='seed.complex', identifier=cpx_id, name=complex_data['name']),
                name=complex_data['name']
            )
            ontology.append_term(term)
        
        print("   🔗 Adding ontology relationships...")
        self._add_relationships(ontology)
        
        print(f"   ✅ Created ontology with {len(ontology.terms)} terms")
        return ontology
    
    def _add_relationships(self, ontology: Ontology):
        """Add all ontology relationships using standard RO properties"""
        
        # Standard RO property mappings
        RO_ENABLES = 'RO:0002327'  # enables
        RO_CONTAINS = 'RO:0001019'  # contains
        RO_CAPABLE_OF = 'RO:0002215'  # capable of
        RO_REALIZED_BY = 'RO:0000058'  # is realized by
        
        relationship_count = 0
        
        # role_enables_reaction: triggering roles enable reactions
        print(f"      - Adding {sum(len(reactions) for reactions in self.role_enables_reaction.values())} role→reaction relationships...")
        for role_seed_id, reactions in self.role_enables_reaction.items():
            # Convert seed.role:NNNNN format to just the ID
            if role_seed_id.startswith('seed.role:'):
                role_id = role_seed_id.replace('seed.role:', '')
                role_ref = Reference(prefix='seed.role', identifier=role_id)
                
                for reaction_seed_id in reactions:
                    if reaction_seed_id.startswith('seed.reaction:'):
                        rxn_id = reaction_seed_id.replace('seed.reaction:', '')
                        rxn_ref = Reference(prefix='seed.reaction', identifier=rxn_id)
                        
                        # Add enables relationship
                        ontology.add_relationship(role_ref, RO_ENABLES, rxn_ref)
                        relationship_count += 1
        
        # complex_has_role: complexes contain roles
        print(f"      - Adding {sum(len(roles) for roles in self.complex_has_role.values())} complex→role relationships...")
        for complex_seed_id, roles in self.complex_has_role.items():
            if complex_seed_id.startswith('seed.complex:'):
                cpx_id = complex_seed_id.replace('seed.complex:', '')
                cpx_ref = Reference(prefix='seed.complex', identifier=cpx_id)
                
                for role_seed_id in roles:
                    if role_seed_id.startswith('seed.role:'):
                        role_id = role_seed_id.replace('seed.role:', '')
                        role_ref = Reference(prefix='seed.role', identifier=role_id)
                        
                        # Add contains relationship
                        ontology.add_relationship(cpx_ref, RO_CONTAINS, role_ref)
                        relationship_count += 1
        
        # complex_enables_reaction: complexes with triggering roles enable reactions
        print(f"      - Adding {sum(len(reactions) for reactions in self.complex_enables_reaction.values())} complex→reaction relationships...")
        for complex_seed_id, reactions in self.complex_enables_reaction.items():
            if complex_seed_id.startswith('seed.complex:'):
                cpx_id = complex_seed_id.replace('seed.complex:', '')
                cpx_ref = Reference(prefix='seed.complex', identifier=cpx_id)
                
                for reaction_seed_id in reactions:
                    if reaction_seed_id.startswith('seed.reaction:'):
                        rxn_id = reaction_seed_id.replace('seed.reaction:', '')
                        rxn_ref = Reference(prefix='seed.reaction', identifier=rxn_id)
                        
                        # Add capable_of relationship
                        ontology.add_relationship(cpx_ref, RO_CAPABLE_OF, rxn_ref)
                        relationship_count += 1
        
        # reaction_has_complex: reactions are realized by complexes
        print(f"      - Adding {sum(len(complexes) for complexes in self.reaction_has_complex.values())} reaction→complex relationships...")
        for reaction_seed_id, complexes in self.reaction_has_complex.items():
            if reaction_seed_id.startswith('seed.reaction:'):
                rxn_id = reaction_seed_id.replace('seed.reaction:', '')
                rxn_ref = Reference(prefix='seed.reaction', identifier=rxn_id)
                
                for complex_seed_id in complexes:
                    if complex_seed_id.startswith('seed.complex:'):
                        cpx_id = complex_seed_id.replace('seed.complex:', '')
                        cpx_ref = Reference(prefix='seed.complex', identifier=cpx_id)
                        
                        # Add realized_by relationship (inverse of capable_of)
                        ontology.add_relationship(rxn_ref, RO_REALIZED_BY, cpx_ref)
                        relationship_count += 1
        
        print(f"      ✅ Added {relationship_count} total relationships")
        
    def build_complete_ontology(self):
        """Build the complete ontology with all data sources"""
        print("🚀 Building complete SEED ontology...")
        print("="*60)
        
        # Load all data sources
        self.load_relationships()
        self.load_compounds()
        self.load_reactions()
        self.load_roles_and_subsystems()
        self.load_complexes_from_template()
        
        # Create the ontology
        ontology = self.create_ontology()
        
        # Generate output files
        print("\n📁 Generating output files...")
        
        # OWL format
        owl_file = os.path.join(self.output_dir, "seed_unified.owl")
        ontology.write_owl(owl_file)
        print(f"   ✅ Generated {owl_file}")
        
        # JSON format
        json_file = os.path.join(self.output_dir, "seed_unified.json")
        ontology.write_obonet_json(json_file)
        print(f"   ✅ Generated {json_file}")
        
        # OBO format
        obo_file = os.path.join(self.output_dir, "seed_unified.obo")
        ontology.write_obo(obo_file)
        print(f"   ✅ Generated {obo_file}")
        
        print("\n🎉 Complete SEED ontology built successfully!")
        print("="*60)
        print(f"📊 Summary:")
        print(f"   Compounds: {len(self.compounds)}")
        print(f"   Reactions: {len(self.reactions)} (spontaneous: {len(self.spontaneous_reactions)}, universal: {len(self.universal_reactions)})")
        print(f"   Roles: {len(self.roles)}")
        print(f"   Subsystems: {len(self.subsystems)}")
        print(f"   Complexes: {len(self.complexes)}")
        
        total_relationships = (
            sum(len(reactions) for reactions in self.role_enables_reaction.values()) +
            sum(len(roles) for roles in self.complex_has_role.values()) +
            sum(len(reactions) for reactions in self.complex_enables_reaction.values()) +
            sum(len(complexes) for complexes in self.reaction_has_complex.values())
        )
        print(f"   Total relationships: {total_relationships}")
        
        print(f"\n🔗 Relationship breakdown:")
        print(f"   role_enables_reaction: {sum(len(reactions) for reactions in self.role_enables_reaction.values())}")
        print(f"   complex_has_role: {sum(len(roles) for roles in self.complex_has_role.values())}")
        print(f"   complex_enables_reaction: {sum(len(reactions) for reactions in self.complex_enables_reaction.values())}")
        print(f"   reaction_has_complex: {sum(len(complexes) for complexes in self.reaction_has_complex.values())}")
        
        print(f"\n✨ Ontology uses correct source URIs:")
        print(f"   Compounds: https://modelseed.org/biochem/compounds/cpd#####")
        print(f"   Reactions: https://modelseed.org/biochem/reactions/rxn#####")
        print(f"   Roles: https://pubseed.theseed.org/RoleEditor.cgi?page=ShowRole&Role=#############")
        print(f"   Subsystems: https://pubseed.theseed.org/SubsysEditor.cgi?page=ShowSubsystem&subsystem=##########")
        print(f"   Complexes: https://modelseed.org/biochem/complexes/cpx#####")
        
        print(f"\n⚡ Performance optimizations:")
        print(f"   hasNormalizedForm data properties: {len(self.role_normalizations)}")
        print(f"   Standard RO relationship properties for compatibility")
        print(f"   Direct OWL storage eliminates semsql conversion overhead")
        
        return ontology


def main():
    """Main execution"""
    builder = SEEDOntologyBuilder()
    ontology = builder.build_complete_ontology()
    
    print(f"\n🎯 Files created in output/ directory:")
    for filename in os.listdir(builder.output_dir):
        filepath = os.path.join(builder.output_dir, filename)
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"   {filename}: {size_mb:.1f} MB")
    
    print(f"\n🚀 Ready for use with any OWL tool or direct semsql import!")


if __name__ == "__main__":
    main()