#!/usr/bin/env python3
"""
Enhanced ontology mapper with normalization-based SEED ID assignment

This version assigns legitimate SEED IDs to template roles through:
1. Exact string matching (highest priority)
2. RASTSeedMapper exact matching  
3. Normalization-based fallback matching (new feature)

This maintains ontological integrity by only using legitimate SEED IDs,
never creating synthetic terms.

Usage:
    python add_ontology_mappings_with_normalization.py [template_file] [output_dir]
    
Author: ModelSEED Team (Normalization Enhanced)
Date: January 2025
"""

import json
import sys
import re
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

# Add path for RASTSeedMapper
sys.path.insert(0, '/Users/jplfaria/repos/cdm-data-loader-utils/src')
from utils.rast_seed_mapper import RASTSeedMapper


def normalize_role(s: str) -> str:
    """
    Normalize role name exactly as ModelSEEDpy does
    This enables fast string matching without complex regex
    """
    s = s.strip().lower()
    s = re.sub(r"[\W_]+", "", s)
    return s


class NormalizationEnhancedMapper:
    def __init__(self, seed_json_path: str, modelseed_json_path: str):
        """Initialize with paths to ontology files"""
        self.seed_data = self._load_json(seed_json_path)
        self.modelseed_data = self._load_json(modelseed_json_path)
        
        # Initialize RAST mapper for roles
        self.rast_mapper = RASTSeedMapper(seed_json_path)
        
        # Build lookup dictionaries
        self._build_lookups()
        
        # NEW: Build normalization-based SEED role lookup
        self._build_normalization_lookup()
        
        # NEW: Track which roles are used in complexes
        self.roles_in_complexes = set()
        
        # Track mapping results
        self.unmapped_roles = []
        self.unmapped_compounds = []
        self.unmapped_reactions = []
        self.normalization_matches = []
        self.potential_collisions = []
        
        # Role mapping lookup for complex processing
        self.role_to_seed = {}
        
        # Counters
        self.stats = {
            'roles': {
                'total': 0, 
                'modelseed': 0,
                'kegg': 0,
                'plantseed': 0,
                'seed': 0,
                'other': 0,
                'in_complexes': 0,
                'exact_mapped': 0, 
                'rast_mapped': 0,
                'normalization_mapped': 0,
                'normalized': 0,
                'final_mapped': 0
            },
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
    
    def _build_normalization_lookup(self):
        """
        Build normalization-based lookup for SEED roles
        Maps normalized role names to SEED role information
        """
        print("Building normalization-based SEED role lookup...")
        
        self.seed_role_by_normalized = {}
        self.normalization_collisions = defaultdict(list)
        
        # Process SEED roles from seed.json
        if 'graphs' in self.seed_data:
            for graph in self.seed_data['graphs']:
                if 'nodes' in graph:
                    for node in graph['nodes']:
                        node_id = node.get('id', '')
                        node_label = node.get('lbl', '')
                        
                        # Look for role nodes (have numeric IDs in the URL)
                        if 'Role=' in node_id and node_label:
                            # Extract role number from URL
                            role_match = re.search(r'Role=(\d+)', node_id)
                            if role_match:
                                role_number = role_match.group(1)
                                seed_id = f"seed.role:{role_number}"
                                
                                # Normalize the role label
                                normalized = normalize_role(node_label)
                                
                                role_info = {
                                    'seed_id': seed_id,
                                    'seed_url': node_id,
                                    'original_name': node_label,
                                    'normalized': normalized
                                }
                                
                                # Store in lookup (check for collisions)
                                if normalized in self.seed_role_by_normalized:
                                    # Collision detected
                                    existing = self.seed_role_by_normalized[normalized]
                                    self.normalization_collisions[normalized].extend([existing, role_info])
                                    print(f"⚠️  Normalization collision: '{normalized}'")
                                    print(f"   Existing: {existing['original_name']}")
                                    print(f"   New: {node_label}")
                                else:
                                    self.seed_role_by_normalized[normalized] = role_info
        
        print(f"   Built lookup for {len(self.seed_role_by_normalized)} SEED roles")
        print(f"   Found {len(self.normalization_collisions)} normalization collisions")
    
    def _identify_roles_in_complexes(self, template: dict):
        """Identify all role IDs that are referenced in complexes"""
        print("Identifying roles used in complexes...")
        
        self.roles_in_complexes = set()
        
        for complex_data in template.get('complexes', []):
            for complex_role in complex_data.get('complexroles', []):
                role_ref = complex_role.get('templaterole_ref', '')
                # Extract role ID from reference like '~/roles/id/ftr31282'
                role_match = re.search(r'ftr\d+', role_ref)
                if role_match:
                    self.roles_in_complexes.add(role_match.group())
        
        print(f"   Found {len(self.roles_in_complexes)} roles used in complexes")
    
    def map_role(self, role: dict) -> dict:
        """
        Enhanced role mapping with normalization fallback for ALL roles in complexes
        Priority: 1) Exact match, 2) RAST mapper, 3) Normalization match
        """
        self.stats['roles']['total'] += 1
        
        role_id = role.get('id', '')
        source = role.get('source', '')
        
        # Count by source
        if source == 'ModelSEED':
            self.stats['roles']['modelseed'] += 1
        elif source == 'KEGG':
            self.stats['roles']['kegg'] += 1
        elif source == 'PlantSEED':
            self.stats['roles']['plantseed'] += 1
        elif source == 'SEED':
            self.stats['roles']['seed'] += 1
        else:
            self.stats['roles']['other'] += 1
        
        # NEW: Only process roles that are used in complexes (regardless of source)
        if role_id not in self.roles_in_complexes:
            return role
        
        self.stats['roles']['in_complexes'] += 1
        
        role_name = role.get('name', '')
        role_id = role.get('id', '')
        
        if not role_name:
            return role
        
        # Always add normalized form
        normalized = normalize_role(role_name)
        role['hasNormalizedForm'] = normalized
        self.stats['roles']['normalized'] += 1
        
        mapping_method = None
        seed_id = None
        seed_url = None
        
        # METHOD 1: Try RASTSeedMapper exact matching first (highest priority)
        if self.rast_mapper:
            seed_id = self.rast_mapper.map_annotation(role_name)
            if seed_id:
                # Extract role number and build URL
                role_num = seed_id.split(':')[-1]
                seed_url = f"https://pubseed.theseed.org/RoleEditor.cgi?page=ShowRole&Role={role_num}"
                mapping_method = "exact_rast"
                self.stats['roles']['rast_mapped'] += 1
        
        # METHOD 2: Try normalization-based matching (fallback)
        if not seed_id and normalized in self.seed_role_by_normalized:
            # Check if this normalized form has collisions
            if normalized in self.normalization_collisions:
                # Multiple SEED roles normalize to the same form - be conservative
                print(f"⚠️  Skipping normalization match for '{role_name}' due to collision")
                collision_info = {
                    'template_role': role_name,
                    'normalized': normalized,
                    'colliding_seed_roles': [r['original_name'] for r in self.normalization_collisions[normalized]]
                }
                self.potential_collisions.append(collision_info)
            else:
                # Safe to use normalization match
                seed_info = self.seed_role_by_normalized[normalized]
                seed_id = seed_info['seed_id']
                seed_url = seed_info['seed_url']
                mapping_method = "normalization"
                self.stats['roles']['normalization_mapped'] += 1
                
                # Track this normalization match for reporting
                match_info = {
                    'template_role_id': role_id,
                    'template_role_name': role_name,
                    'seed_id': seed_id,
                    'seed_role_name': seed_info['original_name'],
                    'normalized_form': normalized,
                    'method': 'normalization'
                }
                self.normalization_matches.append(match_info)
        
        # Apply mapping if found
        if seed_id:
            role['seed_id'] = seed_id
            role['seed_url'] = seed_url
            role['mapping_method'] = mapping_method
            self.stats['roles']['final_mapped'] += 1
            
            # Store mapping for complex processing
            if role_id:
                self.role_to_seed[role_id] = seed_id
        else:
            # No mapping found
            self.unmapped_roles.append({
                'id': role_id,
                'name': role_name,
                'normalized': normalized,
                'source': source
            })
        
        return role
    
    def map_compound(self, compound: dict) -> dict:
        """Add seed.compound mappings (unchanged from original)"""
        self.stats['compounds']['total'] += 1
        cpd_id = compound.get('id', '')
        
        if cpd_id in self.compound_lookup:
            node = self.compound_lookup[cpd_id]
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
        """Add seed.reaction mappings (unchanged from original)"""
        self.stats['reactions']['total'] += 1
        rxn_id = reaction.get('id', '')
        
        # Remove compartment suffix if present
        base_rxn_id = rxn_id.split('_')[0]
        
        if base_rxn_id in self.reaction_lookup:
            node = self.reaction_lookup[base_rxn_id]
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
        """Add seed.complex mappings (unchanged from original)"""
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
        
        if role_seeds:
            complex_data['role_seeds'] = role_seeds
        
        return complex_data
    
    def process_template(self, template_path: str, output_path: str) -> Tuple[dict, str, str]:
        """Process a template file and add ontology mappings"""
        print(f"\n=== NORMALIZATION-ENHANCED ONTOLOGY MAPPER (ALL ROLES IN COMPLEXES) ===")
        print(f"Loading template from {template_path}")
        with open(template_path, 'r') as f:
            template = json.load(f)
        
        # NEW: Identify roles used in complexes first
        self._identify_roles_in_complexes(template)
        
        # Reset stats
        for category in self.stats.values():
            for key in category:
                category[key] = 0
        self.unmapped_roles = []
        self.unmapped_compounds = []
        self.unmapped_reactions = []
        self.normalization_matches = []
        self.potential_collisions = []
        
        # Process roles with enhanced mapping
        if 'roles' in template:
            print(f"\nProcessing {len(template['roles'])} roles...")
            for i, role in enumerate(template['roles']):
                template['roles'][i] = self.map_role(role)
            
            print(f"  📊 Role mapping results:")
            print(f"     Total roles in template: {self.stats['roles']['total']}")
            print(f"     Roles by source:")
            print(f"       - ModelSEED: {self.stats['roles']['modelseed']}")
            print(f"       - KEGG: {self.stats['roles']['kegg']}")
            print(f"       - PlantSEED: {self.stats['roles']['plantseed']}")
            print(f"       - SEED: {self.stats['roles']['seed']}")
            print(f"       - Other: {self.stats['roles']['other']}")
            print(f"     🎯 Roles in complexes (processed): {self.stats['roles']['in_complexes']}")
            print(f"     ✅ RAST exact matches: {self.stats['roles']['rast_mapped']}")
            print(f"     ✨ Normalization matches: {self.stats['roles']['normalization_mapped']}")
            print(f"     📋 Total mapped: {self.stats['roles']['final_mapped']}")
            print(f"     ❌ Unmapped: {len(self.unmapped_roles)}")
            print(f"     ⚠️  Collision skips: {len(self.potential_collisions)}")
            
            improvement = self.stats['roles']['normalization_mapped']
            if improvement > 0:
                print(f"\n🎯 NORMALIZATION IMPROVEMENT: +{improvement} roles mapped!")
        
        # Process compounds and reactions (unchanged)
        if 'compounds' in template:
            print(f"\nProcessing {len(template['compounds'])} compounds...")
            for i, compound in enumerate(template['compounds']):
                template['compounds'][i] = self.map_compound(compound)
            print(f"  Successfully mapped: {self.stats['compounds']['mapped']}")
            print(f"  Unmapped: {len(self.unmapped_compounds)}")
        
        if 'reactions' in template:
            print(f"\nProcessing {len(template['reactions'])} reactions...")
            for i, reaction in enumerate(template['reactions']):
                template['reactions'][i] = self.map_reaction(reaction)
            print(f"  Successfully mapped: {self.stats['reactions']['mapped']}")
            print(f"  Unmapped: {len(self.unmapped_reactions)}")
        
        if 'complexes' in template:
            print(f"\nProcessing {len(template['complexes'])} complexes...")
            for i, complex_data in enumerate(template['complexes']):
                template['complexes'][i] = self.map_complex(complex_data)
            print(f"  All {self.stats['complexes']['total']} complexes mapped")
        
        # Save enhanced template
        print(f"\nSaving enhanced template to {output_path}")
        with open(output_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        # Generate enhanced reports
        self._generate_reports(template_path, output_path)
        
        return template, str(output_path), "Multiple reports generated"
    
    def _generate_reports(self, template_path: str, output_path: str):
        """Generate comprehensive reports"""
        template_name = Path(template_path).stem
        output_dir = Path(output_path).parent
        
        # 1. Enhanced unmapped report
        report_path = output_dir / f"{template_name}_unmapped_normalization_enhanced.csv"
        with open(report_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Entity Type', 'ID', 'Name/Details', 'Normalized Form', 'Additional Info'])
            
            for role in self.unmapped_roles:
                writer.writerow([
                    'role', role['id'], role['name'], role['normalized'], 'ModelSEED - No SEED mapping found'
                ])
            
            for compound in self.unmapped_compounds:
                writer.writerow(['compound', compound['id'], compound['name'], '', compound['formula']])
            
            for reaction in self.unmapped_reactions:
                writer.writerow(['reaction', reaction['id'], reaction['name'], '', f"base: {reaction['base_id']}"])
        
        print(f"✅ Enhanced unmapped report: {report_path}")
        
        # 2. Normalization success report
        norm_report_path = output_dir / f"{template_name}_normalization_successes.json"
        normalization_report = {
            'summary': {
                'total_normalization_matches': len(self.normalization_matches),
                'collisions_skipped': len(self.potential_collisions),
                'improvement_over_exact_matching': self.stats['roles']['normalization_mapped']
            },
            'normalization_matches': self.normalization_matches,
            'collision_analysis': self.potential_collisions
        }
        
        with open(norm_report_path, 'w') as f:
            json.dump(normalization_report, f, indent=2)
        
        print(f"✅ Normalization success report: {norm_report_path}")
        
        # 3. Coverage improvement analysis
        coverage_path = output_dir / f"{template_name}_coverage_improvement.json"
        total_roles = self.stats['roles']['modelseed']
        exact_coverage = self.stats['roles']['rast_mapped'] / total_roles * 100 if total_roles > 0 else 0
        enhanced_coverage = self.stats['roles']['final_mapped'] / total_roles * 100 if total_roles > 0 else 0
        
        coverage_report = {
            'mapping_performance': {
                'exact_matching_only': {
                    'mapped_roles': self.stats['roles']['rast_mapped'],
                    'coverage_pct': round(exact_coverage, 2)
                },
                'with_normalization': {
                    'mapped_roles': self.stats['roles']['final_mapped'],
                    'coverage_pct': round(enhanced_coverage, 2),
                    'improvement': self.stats['roles']['normalization_mapped']
                }
            },
            'expected_impact': {
                'note': 'These additional role mappings should help close the coverage gap',
                'additional_roles_mapped': self.stats['roles']['normalization_mapped'],
                'potential_reactions_recovered': 'TBD - requires database reconstruction'
            }
        }
        
        with open(coverage_path, 'w') as f:
            json.dump(coverage_report, f, indent=2)
        
        print(f"✅ Coverage improvement analysis: {coverage_path}")
        
        # Print final summary
        print(f"\n=== ENHANCED MAPPING SUMMARY (ALL ROLES IN COMPLEXES) ===")
        print(f"Roles in complexes: {self.stats['roles']['final_mapped']}/{self.stats['roles']['in_complexes']} roles mapped")
        print(f"  - RAST exact matches: {self.stats['roles']['rast_mapped']}")
        print(f"  - ✨ Normalization matches: {self.stats['roles']['normalization_mapped']}")
        print(f"  - Improvement: +{self.stats['roles']['normalization_mapped']} roles over exact matching!")
        print(f"Compounds: {self.stats['compounds']['mapped']}/{self.stats['compounds']['total']} mapped")
        print(f"Reactions: {self.stats['reactions']['mapped']}/{self.stats['reactions']['total']} mapped")
        print(f"Complexes: {self.stats['complexes']['mapped']}/{self.stats['complexes']['total']} mapped")


def main():
    """Main execution with normalization enhancement"""
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
    
    # Initialize normalization-enhanced mapper
    mapper = NormalizationEnhancedMapper(seed_json, modelseed_json)
    
    # Create output directory
    output_dir = Path("/Users/jplfaria/repos/ModelSEEDTemplates/templates/ontology/enhanced_templates")
    output_dir.mkdir(exist_ok=True)
    
    # Process command line arguments or use defaults
    if len(sys.argv) > 1:
        template_path = sys.argv[1]
        if len(sys.argv) > 2:
            output_dir = Path(sys.argv[2])
            output_dir.mkdir(exist_ok=True)
    else:
        # Default: Process GramNegative template
        template_path = "/Users/jplfaria/repos/ModelSEEDTemplates/templates/v6.0/GramNegModelTemplateV6.json"
    
    # Generate output filename
    template_name = Path(template_path).stem
    output_path = output_dir / f"{template_name}_with_ontology_all_complexes_enhanced.json"
    
    enhanced_template, out_path, report_info = mapper.process_template(str(template_path), str(output_path))
    
    # Show examples of normalization matches
    if mapper.normalization_matches:
        print("\n=== NORMALIZATION SUCCESS EXAMPLES ===")
        for i, match in enumerate(mapper.normalization_matches[:3]):  # Show first 3
            print(f"\nExample {i+1}:")
            print(f"  Template: {match['template_role_name']}")
            print(f"  SEED: {match['seed_role_name']}")
            print(f"  Assigned: {match['seed_id']}")
            print(f"  Normalized: {match['normalized_form']}")
    
    if mapper.potential_collisions:
        print(f"\n⚠️  {len(mapper.potential_collisions)} collision(s) detected and skipped for safety")
    
    print(f"\n✅ NORMALIZATION ENHANCEMENT COMPLETE!")
    print(f"   Enhanced template: {out_path}")
    print(f"   Added {mapper.stats['roles']['normalization_mapped']} additional SEED role mappings!")
    print(f"   🎯 This should help close the coverage gap by using legitimate SEED IDs")


if __name__ == "__main__":
    main()