#!/usr/bin/env python3
"""
Add ontology mappings to ModelSEED template JSON files
Maps to seed.role, seed.reaction, seed.compound, and seed.complex

This script enhances ModelSEED templates by adding ontology identifiers
while preserving all original content for full traceability.

Usage:
    python add_ontology_mappings.py [template_file] [output_dir]
    
    If no arguments provided, processes GramNegModelTemplateV6.json as example

Requirements:
    - seed.json and modelseed.json in ../json/ directory
    - RASTSeedMapper from cdm-data-loader-utils

Output:
    - Enhanced template with ontology mappings (*_with_ontology.json)
    - CSV report of unmapped entities (*_unmapped.csv)

Author: ModelSEED Team
Date: January 2025
"""

import json
import sys
import re
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Add path for RASTSeedMapper
sys.path.insert(0, '/Users/jplfaria/repos/cdm-data-loader-utils/src')
from utils.rast_seed_mapper import RASTSeedMapper


class OntologyMapper:
    def __init__(self, seed_json_path: str, modelseed_json_path: str):
        """Initialize with paths to ontology files"""
        self.seed_data = self._load_json(seed_json_path)
        self.modelseed_data = self._load_json(modelseed_json_path)
        
        # Initialize RAST mapper for roles
        self.rast_mapper = RASTSeedMapper(seed_json_path)
        
        # Build lookup dictionaries
        self._build_lookups()
        
        # Track unmapped entities
        self.unmapped_roles = []
        self.unmapped_compounds = []
        self.unmapped_reactions = []
        
        # Role mapping lookup for complex processing
        self.role_to_seed = {}
        
        # Counters
        self.stats = {
            'roles': {'total': 0, 'modelseed': 0, 'mapped': 0},
            'compounds': {'total': 0, 'mapped': 0},
            'reactions': {'total': 0, 'mapped': 0},
            'complexes': {'total': 0, 'mapped': 0}
        }
    
    def _load_json(self, path: str) -> dict:
        """Load JSON file"""
        with open(path, 'r') as f:
            return json.load(f)
    
    def _build_lookups(self):
        """Build lookup dictionaries for fast access"""
        # Build compound and reaction lookups from modelseed
        self.compound_lookup = {}
        self.reaction_lookup = {}
        
        if 'graphs' in self.modelseed_data:
            for graph in self.modelseed_data['graphs']:
                if 'nodes' in graph:
                    for node in graph['nodes']:
                        node_id = node.get('id', '')
                        # Compounds: https://modelseed.org/biochem/compounds/cpd00001
                        if '/compounds/' in node_id:
                            cpd_match = re.search(r'cpd\d+', node_id)
                            if cpd_match:
                                self.compound_lookup[cpd_match.group()] = node
                        # Reactions: https://modelseed.org/biochem/reactions/rxn00001
                        elif '/reactions/' in node_id:
                            rxn_match = re.search(r'rxn\d+', node_id)
                            if rxn_match:
                                self.reaction_lookup[rxn_match.group()] = node
    
    def map_role(self, role: dict) -> dict:
        """Add seed ontology mappings to a role"""
        self.stats['roles']['total'] += 1
        
        # Only process ModelSEED roles
        if role.get('source') != 'ModelSEED':
            return role
        
        self.stats['roles']['modelseed'] += 1
        
        # Try to map using the role name
        role_name = role.get('name', '')
        role_id = role.get('id', '')
        
        if role_name:
            seed_id = self.rast_mapper.map_annotation(role_name)
            if seed_id:
                # Extract role number
                role_num = seed_id.split(':')[-1]
                role['seed_url'] = f"https://pubseed.theseed.org/RoleEditor.cgi?page=ShowRole&Role={role_num}"
                role['seed_id'] = seed_id
                self.stats['roles']['mapped'] += 1
                
                # Store mapping for complex processing
                if role_id:
                    self.role_to_seed[role_id] = seed_id
            else:
                self.unmapped_roles.append({
                    'id': role_id,
                    'name': role_name,
                    'source': 'ModelSEED'
                })
        
        return role
    
    def map_compound(self, compound: dict) -> dict:
        """Add seed.compound mappings"""
        self.stats['compounds']['total'] += 1
        cpd_id = compound.get('id', '')
        
        if cpd_id in self.compound_lookup:
            node = self.compound_lookup[cpd_id]
            # Use the URL from the ontology
            compound['seed_url'] = node.get('id', f"https://modelseed.org/biochem/compounds/{cpd_id}")
            compound['seed_id'] = f"seed.compound:{cpd_id}"
            self.stats['compounds']['mapped'] += 1
            
            # Add cross-references if available
            if 'meta' in node:
                xrefs = node['meta'].get('xrefs', [])
                kegg_ids = []
                chebi_ids = []
                
                for xref in xrefs:
                    val = xref.get('val', '')
                    if val.startswith('KEGG.COMPOUND:'):
                        kegg_ids.append(val.replace('KEGG.COMPOUND:', ''))
                    elif val.startswith('CHEBI:'):
                        chebi_ids.append(val)
                
                if kegg_ids:
                    compound['kegg_ids'] = kegg_ids
                if chebi_ids:
                    compound['chebi_ids'] = chebi_ids
        else:
            self.unmapped_compounds.append({
                'id': cpd_id,
                'name': compound.get('name', ''),
                'formula': compound.get('formula', '')
            })
        
        return compound
    
    def map_reaction(self, reaction: dict) -> dict:
        """Add seed.reaction mappings"""
        self.stats['reactions']['total'] += 1
        rxn_id = reaction.get('id', '')
        
        # Remove compartment suffix if present
        base_rxn_id = rxn_id.split('_')[0]
        
        if base_rxn_id in self.reaction_lookup:
            node = self.reaction_lookup[base_rxn_id]
            # Use the URL from the ontology
            reaction['seed_url'] = node.get('id', f"https://modelseed.org/biochem/reactions/{base_rxn_id}")
            reaction['seed_id'] = f"seed.reaction:{base_rxn_id}"
            self.stats['reactions']['mapped'] += 1
            
            # Add cross-references
            if 'meta' in node:
                xrefs = node['meta'].get('xrefs', [])
                ec_numbers = []
                kegg_ids = []
                metacyc_ids = []
                
                for xref in xrefs:
                    val = xref.get('val', '')
                    if val.startswith('EC:'):
                        ec_numbers.append(val.replace('EC:', ''))
                    elif val.startswith('KEGG.REACTION:'):
                        kegg_ids.append(val.replace('KEGG.REACTION:', ''))
                    elif val.startswith('MetaCyc:'):
                        metacyc_ids.append(val.replace('MetaCyc:', ''))
                
                if ec_numbers:
                    reaction['ec_numbers'] = ec_numbers
                if kegg_ids:
                    reaction['kegg_ids'] = kegg_ids
                if metacyc_ids:
                    reaction['metacyc_ids'] = metacyc_ids
        else:
            self.unmapped_reactions.append({
                'id': rxn_id,
                'base_id': base_rxn_id,
                'name': reaction.get('name', '')
            })
        
        return reaction
    
    def map_complex(self, complex_data: dict) -> dict:
        """Add seed.complex mappings using the complex ID"""
        self.stats['complexes']['total'] += 1
        
        cpx_id = complex_data.get('id', '')
        complex_data['seed_url'] = f"https://modelseed.org/biochem/complexes/{cpx_id}"
        complex_data['seed_id'] = f"seed.complex:{cpx_id}"
        self.stats['complexes']['mapped'] += 1
        
        # Map roles in complex to seed IDs using our lookup
        role_refs = complex_data.get('complexroles', [])
        role_seeds = []
        
        for role_ref in role_refs:
            # Extract role ID from reference
            if isinstance(role_ref, dict):
                role_ref_str = role_ref.get('templaterole_ref', '')
            else:
                role_ref_str = str(role_ref)
            
            # Extract role ID from reference string
            role_match = re.search(r'ftr\d+', role_ref_str)
            if role_match:
                role_id = role_match.group()
                # Look up the seed ID from our mapping
                if role_id in self.role_to_seed:
                    role_seeds.append(self.role_to_seed[role_id])
                # If not mapped, skip (don't add placeholder)
        
        if role_seeds:
            complex_data['role_seeds'] = role_seeds
        
        return complex_data
    
    def process_template(self, template_path: str, output_path: str) -> Tuple[dict, str, str]:
        """Process a template file and add ontology mappings"""
        print(f"\nLoading template from {template_path}")
        with open(template_path, 'r') as f:
            template = json.load(f)
        
        # Reset stats for this template
        for category in self.stats.values():
            for key in category:
                category[key] = 0
        self.unmapped_roles = []
        self.unmapped_compounds = []
        self.unmapped_reactions = []
        
        # Process roles
        if 'roles' in template:
            print(f"Processing {len(template['roles'])} roles...")
            for i, role in enumerate(template['roles']):
                template['roles'][i] = self.map_role(role)
            
            print(f"  Total roles: {self.stats['roles']['total']}")
            print(f"  ModelSEED roles: {self.stats['roles']['modelseed']}")
            print(f"  Successfully mapped: {self.stats['roles']['mapped']}")
            print(f"  Unmapped: {len(self.unmapped_roles)}")
        
        # Process compounds
        if 'compounds' in template:
            print(f"\nProcessing {len(template['compounds'])} compounds...")
            for i, compound in enumerate(template['compounds']):
                template['compounds'][i] = self.map_compound(compound)
            
            print(f"  Successfully mapped: {self.stats['compounds']['mapped']}")
            print(f"  Unmapped: {len(self.unmapped_compounds)}")
        
        # Process reactions
        if 'reactions' in template:
            print(f"\nProcessing {len(template['reactions'])} reactions...")
            for i, reaction in enumerate(template['reactions']):
                template['reactions'][i] = self.map_reaction(reaction)
            
            print(f"  Successfully mapped: {self.stats['reactions']['mapped']}")
            print(f"  Unmapped: {len(self.unmapped_reactions)}")
        
        # Process complexes
        if 'complexes' in template:
            print(f"\nProcessing {len(template['complexes'])} complexes...")
            for i, complex_data in enumerate(template['complexes']):
                template['complexes'][i] = self.map_complex(complex_data)
            
            print(f"  All {self.stats['complexes']['total']} complexes mapped")
        
        # Save output
        print(f"\nSaving enhanced template to {output_path}")
        with open(output_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        # Generate unmapped report
        template_name = Path(template_path).stem
        report_path = Path(output_path).parent / f"{template_name}_unmapped.csv"
        
        print(f"\nGenerating unmapped entities report to {report_path}")
        with open(report_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Entity Type', 'ID', 'Name/Details', 'Additional Info'])
            
            # Write unmapped roles
            for role in self.unmapped_roles:
                writer.writerow(['role', role['id'], role['name'], 'ModelSEED'])
            
            # Write unmapped compounds
            for compound in self.unmapped_compounds:
                writer.writerow(['compound', compound['id'], compound['name'], compound['formula']])
            
            # Write unmapped reactions
            for reaction in self.unmapped_reactions:
                writer.writerow(['reaction', reaction['id'], reaction['name'], f"base: {reaction['base_id']}"])
        
        print("\n=== MAPPING SUMMARY ===")
        print(f"Roles: {self.stats['roles']['mapped']}/{self.stats['roles']['modelseed']} ModelSEED roles mapped")
        print(f"Compounds: {self.stats['compounds']['mapped']}/{self.stats['compounds']['total']} mapped")
        print(f"Reactions: {self.stats['reactions']['mapped']}/{self.stats['reactions']['total']} mapped")
        print(f"Complexes: {self.stats['complexes']['mapped']}/{self.stats['complexes']['total']} mapped")
        
        return template, str(output_path), str(report_path)


def main():
    # Paths
    seed_json = "/Users/jplfaria/repos/ModelSEEDTemplates/templates/ontology/json/seed.json"
    modelseed_json = "/Users/jplfaria/repos/ModelSEEDTemplates/templates/ontology/json/modelseed.json"
    
    # Decompress modelseed.json if needed
    import gzip
    modelseed_gz = "/Users/jplfaria/repos/ModelSEEDTemplates/templates/ontology/json/modelseed.json.gz"
    
    if not Path(modelseed_json).exists() and Path(modelseed_gz).exists():
        print("Decompressing modelseed.json.gz...")
        with gzip.open(modelseed_gz, 'rt') as f_in:
            with open(modelseed_json, 'w') as f_out:
                f_out.write(f_in.read())
    
    # Initialize mapper
    mapper = OntologyMapper(seed_json, modelseed_json)
    
    # Create output directory
    output_dir = Path("/Users/jplfaria/repos/ModelSEEDTemplates/templates/ontology/enhanced_templates")
    output_dir.mkdir(exist_ok=True)
    
    # Process GramNegative template
    template_path = "/Users/jplfaria/repos/ModelSEEDTemplates/templates/v6.0/GramNegModelTemplateV6.json"
    output_path = output_dir / "GramNegModelTemplateV6_with_ontology.json"
    
    enhanced_template, out_path, report_path = mapper.process_template(str(template_path), str(output_path))
    
    # Show some examples
    print("\n=== EXAMPLE ENHANCED ENTRIES ===")
    
    # Show example role
    print("\nExample Role with seed.role mapping:")
    for role in enhanced_template.get('roles', [])[:100]:
        if 'seed_id' in role:
            print(json.dumps({
                'id': role['id'],
                'name': role['name'],
                'seed_id': role['seed_id'],
                'seed_url': role['seed_url']
            }, indent=2))
            break
    
    # Show example compound
    print("\nExample Compound with seed.compound mapping:")
    for compound in enhanced_template.get('compounds', [])[:10]:
        if 'seed_id' in compound:
            print(json.dumps({
                'id': compound['id'],
                'name': compound['name'],
                'seed_id': compound['seed_id'],
                'seed_url': compound['seed_url']
            }, indent=2))
            break
    
    # Show example reaction
    print("\nExample Reaction with seed.reaction mapping:")
    for reaction in enhanced_template.get('reactions', [])[:10]:
        if 'seed_id' in reaction:
            print(json.dumps({
                'id': reaction['id'],
                'name': reaction['name'][:50] + '...',
                'seed_id': reaction['seed_id'],
                'seed_url': reaction['seed_url']
            }, indent=2))
            break
    
    # Show example complex
    print("\nExample Complex with seed.complex mapping:")
    if enhanced_template.get('complexes'):
        complex_ex = enhanced_template['complexes'][0]
        print(json.dumps({
            'id': complex_ex['id'],
            'name': complex_ex['name'],
            'seed_id': complex_ex['seed_id'],
            'seed_url': complex_ex['seed_url']
        }, indent=2))


if __name__ == "__main__":
    main()