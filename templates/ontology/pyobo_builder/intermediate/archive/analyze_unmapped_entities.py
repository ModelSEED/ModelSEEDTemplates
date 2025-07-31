#!/usr/bin/env python3
"""
Comprehensive SEED Unified Ontology Analysis Tool

Analyzes the template data to identify ALL unmapped entities across all types:
- Template roles without seed_id mappings
- Template reactions without seed_id mappings  
- Template compounds without seed_id mappings
- Template complexes without proper mappings

Also checks role source filtering and creates separation strategy files.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UnmappedEntitiesAnalyzer:
    """Analyzes template data for unmapped entities and mapping coverage."""
    
    def __init__(self, template_data_path: str):
        """Initialize with path to template data JSON."""
        self.template_data_path = Path(template_data_path)
        self.data = None
        self.analysis_results = {}
        self._load_template_data()
    
    def _load_template_data(self):
        """Load the template data JSON file."""
        try:
            with open(self.template_data_path, 'r') as f:
                self.data = json.load(f)
            logger.info(f"Loaded template data with {len(self.data.get('roles', {}))} roles, "
                       f"{len(self.data.get('reactions', {}))} reactions, "
                       f"{len(self.data.get('complexes', {}))} complexes")
        except Exception as e:
            logger.error(f"Failed to load template data: {e}")
            raise
    
    def analyze_role_mappings(self) -> Dict:
        """Analyze role mappings and source filtering."""
        logger.info("Analyzing role mappings and source filtering...")
        
        roles = self.data.get('roles', {})
        role_analysis = {
            'total_roles': len(roles),
            'mapped_roles': 0,
            'unmapped_roles': 0,
            'source_breakdown': defaultdict(int),
            'mapped_by_source': defaultdict(int),
            'unmapped_by_source': defaultdict(int),
            'unmapped_role_examples': [],
            'mapped_role_examples': []
        }
        
        for role_id, role_data in roles.items():
            source = role_data.get('source', 'unknown')
            role_analysis['source_breakdown'][source] += 1
            
            seed_id = role_data.get('seed_id')
            if seed_id and seed_id.strip() and not seed_id.startswith('null'):
                role_analysis['mapped_roles'] += 1
                role_analysis['mapped_by_source'][source] += 1
                if len(role_analysis['mapped_role_examples']) < 5:
                    role_analysis['mapped_role_examples'].append({
                        'id': role_id,
                        'name': role_data.get('name'),
                        'source': source,
                        'seed_id': seed_id
                    })
            else:
                role_analysis['unmapped_roles'] += 1
                role_analysis['unmapped_by_source'][source] += 1
                if len(role_analysis['unmapped_role_examples']) < 10:
                    role_analysis['unmapped_role_examples'].append({
                        'id': role_id,
                        'name': role_data.get('name'),
                        'source': source,
                        'seed_id': seed_id or 'missing'
                    })
        
        # Convert defaultdicts to regular dicts for JSON serialization
        role_analysis['source_breakdown'] = dict(role_analysis['source_breakdown'])
        role_analysis['mapped_by_source'] = dict(role_analysis['mapped_by_source'])
        role_analysis['unmapped_by_source'] = dict(role_analysis['unmapped_by_source'])
        
        logger.info(f"Role analysis: {role_analysis['mapped_roles']} mapped, "
                   f"{role_analysis['unmapped_roles']} unmapped")
        
        return role_analysis
    
    def analyze_reaction_mappings(self) -> Dict:
        """Analyze reaction mappings."""
        logger.info("Analyzing reaction mappings...")
        
        reactions = self.data.get('reactions', {})
        reaction_analysis = {
            'total_reactions': len(reactions),
            'mapped_reactions': 0,
            'unmapped_reactions': 0,
            'unmapped_reaction_examples': [],
            'mapped_reaction_examples': [],
            'reactions_with_complexes': 0,
            'reactions_without_complexes': 0
        }
        
        for reaction_id, reaction_data in reactions.items():
            seed_id = reaction_data.get('seed_id')
            complexes = reaction_data.get('complexes', [])
            
            if complexes:
                reaction_analysis['reactions_with_complexes'] += 1
            else:
                reaction_analysis['reactions_without_complexes'] += 1
            
            if seed_id and seed_id.strip() and not seed_id.startswith('null'):
                reaction_analysis['mapped_reactions'] += 1
                if len(reaction_analysis['mapped_reaction_examples']) < 5:
                    reaction_analysis['mapped_reaction_examples'].append({
                        'id': reaction_id,
                        'name': reaction_data.get('name'),
                        'seed_id': seed_id,
                        'has_complexes': len(complexes) > 0,
                        'complex_count': len(complexes)
                    })
            else:
                reaction_analysis['unmapped_reactions'] += 1
                if len(reaction_analysis['unmapped_reaction_examples']) < 10:
                    reaction_analysis['unmapped_reaction_examples'].append({
                        'id': reaction_id,
                        'name': reaction_data.get('name'),
                        'seed_id': seed_id or 'missing',
                        'has_complexes': len(complexes) > 0,
                        'complex_count': len(complexes)
                    })
        
        logger.info(f"Reaction analysis: {reaction_analysis['mapped_reactions']} mapped, "
                   f"{reaction_analysis['unmapped_reactions']} unmapped")
        
        return reaction_analysis
    
    def analyze_complex_mappings(self) -> Dict:
        """Analyze complex mappings."""
        logger.info("Analyzing complex mappings...")
        
        complexes = self.data.get('complexes', {})
        complex_analysis = {
            'total_complexes': len(complexes),
            'mapped_complexes': 0,
            'unmapped_complexes': 0,
            'complexes_with_role_seeds': 0,
            'complexes_without_role_seeds': 0,
            'unmapped_complex_examples': [],
            'mapped_complex_examples': [],
            'broken_role_references': []
        }
        
        # Get all valid role IDs for reference checking
        valid_role_ids = set(self.data.get('roles', {}).keys())
        
        for complex_id, complex_data in complexes.items():
            seed_id = complex_data.get('seed_id')
            role_seeds = complex_data.get('role_seeds', [])
            roles = complex_data.get('roles', [])
            
            # Check for broken role references
            for role_id in roles:
                if role_id not in valid_role_ids:
                    complex_analysis['broken_role_references'].append({
                        'complex_id': complex_id,
                        'missing_role_id': role_id,
                        'complex_name': complex_data.get('name')
                    })
            
            if role_seeds:
                complex_analysis['complexes_with_role_seeds'] += 1
            else:
                complex_analysis['complexes_without_role_seeds'] += 1
            
            if seed_id and seed_id.strip() and not seed_id.startswith('null'):
                complex_analysis['mapped_complexes'] += 1
                if len(complex_analysis['mapped_complex_examples']) < 5:
                    complex_analysis['mapped_complex_examples'].append({
                        'id': complex_id,
                        'name': complex_data.get('name'),
                        'seed_id': seed_id,
                        'role_count': len(roles),
                        'has_role_seeds': len(role_seeds) > 0,
                        'confidence': complex_data.get('confidence')
                    })
            else:
                complex_analysis['unmapped_complexes'] += 1
                if len(complex_analysis['unmapped_complex_examples']) < 10:
                    complex_analysis['unmapped_complex_examples'].append({
                        'id': complex_id,
                        'name': complex_data.get('name'),
                        'seed_id': seed_id or 'missing',
                        'role_count': len(roles),
                        'has_role_seeds': len(role_seeds) > 0,
                        'confidence': complex_data.get('confidence')
                    })
        
        logger.info(f"Complex analysis: {complex_analysis['mapped_complexes']} mapped, "
                   f"{complex_analysis['unmapped_complexes']} unmapped, "
                   f"{len(complex_analysis['broken_role_references'])} broken role references")
        
        return complex_analysis
    
    def analyze_relationship_integrity(self) -> Dict:
        """Analyze integrity of relationships between entities."""
        logger.info("Analyzing relationship integrity...")
        
        # Get mapped entities
        roles = self.data.get('roles', {})
        reactions = self.data.get('reactions', {})
        complexes = self.data.get('complexes', {})
        
        mapped_roles = {rid for rid, rdata in roles.items() 
                       if rdata.get('seed_id') and rdata['seed_id'].strip() and not rdata['seed_id'].startswith('null')}
        mapped_reactions = {rid for rid, rdata in reactions.items() 
                          if rdata.get('seed_id') and rdata['seed_id'].strip() and not rdata['seed_id'].startswith('null')}
        mapped_complexes = {cid for cid, cdata in complexes.items() 
                          if cdata.get('seed_id') and cdata['seed_id'].strip() and not cdata['seed_id'].startswith('null')}
        
        integrity_analysis = {
            'complex_role_relationships': {
                'total': 0,
                'both_mapped': 0,
                'complex_mapped_role_unmapped': 0,
                'complex_unmapped_role_mapped': 0,
                'both_unmapped': 0,
                'broken_examples': []
            },
            'reaction_complex_relationships': {
                'total': 0,
                'both_mapped': 0,
                'reaction_mapped_complex_unmapped': 0,
                'reaction_unmapped_complex_mapped': 0,
                'both_unmapped': 0,
                'broken_examples': []
            }
        }
        
        # Analyze complex-role relationships
        for complex_id, complex_data in complexes.items():
            for role_id in complex_data.get('roles', []):
                integrity_analysis['complex_role_relationships']['total'] += 1
                
                complex_mapped = complex_id in mapped_complexes
                role_mapped = role_id in mapped_roles
                
                if complex_mapped and role_mapped:
                    integrity_analysis['complex_role_relationships']['both_mapped'] += 1
                elif complex_mapped and not role_mapped:
                    integrity_analysis['complex_role_relationships']['complex_mapped_role_unmapped'] += 1
                    if len(integrity_analysis['complex_role_relationships']['broken_examples']) < 5:
                        integrity_analysis['complex_role_relationships']['broken_examples'].append({
                            'complex_id': complex_id,
                            'role_id': role_id,
                            'issue': 'role_unmapped'
                        })
                elif not complex_mapped and role_mapped:
                    integrity_analysis['complex_role_relationships']['complex_unmapped_role_mapped'] += 1
                    if len(integrity_analysis['complex_role_relationships']['broken_examples']) < 5:
                        integrity_analysis['complex_role_relationships']['broken_examples'].append({
                            'complex_id': complex_id,
                            'role_id': role_id,
                            'issue': 'complex_unmapped'
                        })
                else:
                    integrity_analysis['complex_role_relationships']['both_unmapped'] += 1
        
        # Analyze reaction-complex relationships
        for reaction_id, reaction_data in reactions.items():
            for complex_id in reaction_data.get('complexes', []):
                integrity_analysis['reaction_complex_relationships']['total'] += 1
                
                reaction_mapped = reaction_id in mapped_reactions
                complex_mapped = complex_id in mapped_complexes
                
                if reaction_mapped and complex_mapped:
                    integrity_analysis['reaction_complex_relationships']['both_mapped'] += 1
                elif reaction_mapped and not complex_mapped:
                    integrity_analysis['reaction_complex_relationships']['reaction_mapped_complex_unmapped'] += 1
                    if len(integrity_analysis['reaction_complex_relationships']['broken_examples']) < 5:
                        integrity_analysis['reaction_complex_relationships']['broken_examples'].append({
                            'reaction_id': reaction_id,
                            'complex_id': complex_id,
                            'issue': 'complex_unmapped'
                        })
                elif not reaction_mapped and complex_mapped:
                    integrity_analysis['reaction_complex_relationships']['reaction_unmapped_complex_mapped'] += 1
                    if len(integrity_analysis['reaction_complex_relationships']['broken_examples']) < 5:
                        integrity_analysis['reaction_complex_relationships']['broken_examples'].append({
                            'reaction_id': reaction_id,
                            'complex_id': complex_id,
                            'issue': 'reaction_unmapped'
                        })
                else:
                    integrity_analysis['reaction_complex_relationships']['both_unmapped'] += 1
        
        logger.info("Relationship integrity analysis completed")
        return integrity_analysis
    
    def extract_unmapped_entities(self) -> Dict:
        """Extract all unmapped entities for separate storage."""
        logger.info("Extracting unmapped entities...")
        
        roles = self.data.get('roles', {})
        reactions = self.data.get('reactions', {})
        complexes = self.data.get('complexes', {})
        
        unmapped_entities = {
            'unmapped_roles': {},
            'unmapped_reactions': {},
            'unmapped_complexes': {},
            'summary': {
                'unmapped_role_count': 0,
                'unmapped_reaction_count': 0,
                'unmapped_complex_count': 0
            }
        }
        
        # Extract unmapped roles
        for role_id, role_data in roles.items():
            seed_id = role_data.get('seed_id')
            if not seed_id or not seed_id.strip() or seed_id.startswith('null'):
                unmapped_entities['unmapped_roles'][role_id] = role_data
                unmapped_entities['summary']['unmapped_role_count'] += 1
        
        # Extract unmapped reactions
        for reaction_id, reaction_data in reactions.items():
            seed_id = reaction_data.get('seed_id')
            if not seed_id or not seed_id.strip() or seed_id.startswith('null'):
                unmapped_entities['unmapped_reactions'][reaction_id] = reaction_data
                unmapped_entities['summary']['unmapped_reaction_count'] += 1
        
        # Extract unmapped complexes
        for complex_id, complex_data in complexes.items():
            seed_id = complex_data.get('seed_id')
            if not seed_id or not seed_id.strip() or seed_id.startswith('null'):
                unmapped_entities['unmapped_complexes'][complex_id] = complex_data
                unmapped_entities['summary']['unmapped_complex_count'] += 1
        
        logger.info(f"Extracted {unmapped_entities['summary']['unmapped_role_count']} unmapped roles, "
                   f"{unmapped_entities['summary']['unmapped_reaction_count']} unmapped reactions, "
                   f"{unmapped_entities['summary']['unmapped_complex_count']} unmapped complexes")
        
        return unmapped_entities
    
    def extract_broken_relationships(self) -> Dict:
        """Extract relationships that reference unmapped entities."""
        logger.info("Extracting broken relationships...")
        
        roles = self.data.get('roles', {})
        reactions = self.data.get('reactions', {})
        complexes = self.data.get('complexes', {})
        
        # Get unmapped entity sets
        unmapped_roles = {rid for rid, rdata in roles.items() 
                         if not rdata.get('seed_id') or not rdata['seed_id'].strip() or rdata['seed_id'].startswith('null')}
        unmapped_reactions = {rid for rid, rdata in reactions.items() 
                            if not rdata.get('seed_id') or not rdata['seed_id'].strip() or rdata['seed_id'].startswith('null')}
        unmapped_complexes = {cid for cid, cdata in complexes.items() 
                            if not cdata.get('seed_id') or not cdata['seed_id'].strip() or cdata['seed_id'].startswith('null')}
        
        broken_relationships = {
            'complex_role_broken': [],
            'reaction_complex_broken': [],
            'summary': {
                'complex_role_broken_count': 0,
                'reaction_complex_broken_count': 0
            }
        }
        
        # Find broken complex-role relationships
        for complex_id, complex_data in complexes.items():
            for role_id in complex_data.get('roles', []):
                if complex_id in unmapped_complexes or role_id in unmapped_roles:
                    broken_relationships['complex_role_broken'].append({
                        'complex_id': complex_id,
                        'complex_name': complex_data.get('name'),
                        'role_id': role_id,
                        'role_name': roles.get(role_id, {}).get('name', 'unknown'),
                        'complex_unmapped': complex_id in unmapped_complexes,
                        'role_unmapped': role_id in unmapped_roles
                    })
                    broken_relationships['summary']['complex_role_broken_count'] += 1
        
        # Find broken reaction-complex relationships
        for reaction_id, reaction_data in reactions.items():
            for complex_id in reaction_data.get('complexes', []):
                if reaction_id in unmapped_reactions or complex_id in unmapped_complexes:
                    broken_relationships['reaction_complex_broken'].append({
                        'reaction_id': reaction_id,
                        'reaction_name': reaction_data.get('name'),
                        'complex_id': complex_id,
                        'complex_name': complexes.get(complex_id, {}).get('name', 'unknown'),
                        'reaction_unmapped': reaction_id in unmapped_reactions,
                        'complex_unmapped': complex_id in unmapped_complexes
                    })
                    broken_relationships['summary']['reaction_complex_broken_count'] += 1
        
        logger.info(f"Found {broken_relationships['summary']['complex_role_broken_count']} broken complex-role relationships, "
                   f"{broken_relationships['summary']['reaction_complex_broken_count']} broken reaction-complex relationships")
        
        return broken_relationships
    
    def extract_clean_ontology_stats(self) -> Dict:
        """Generate statistics for the clean ontology (only mapped entities)."""
        logger.info("Generating clean ontology statistics...")
        
        roles = self.data.get('roles', {})
        reactions = self.data.get('reactions', {})
        complexes = self.data.get('complexes', {})
        
        # Get mapped entities
        mapped_roles = {rid: rdata for rid, rdata in roles.items() 
                       if rdata.get('seed_id') and rdata['seed_id'].strip() and not rdata['seed_id'].startswith('null')}
        mapped_reactions = {rid: rdata for rid, rdata in reactions.items() 
                          if rdata.get('seed_id') and rdata['seed_id'].strip() and not rdata['seed_id'].startswith('null')}
        mapped_complexes = {cid: cdata for cid, cdata in complexes.items() 
                          if cdata.get('seed_id') and cdata['seed_id'].strip() and not cdata['seed_id'].startswith('null')}
        
        # Count valid relationships (both ends mapped)
        valid_complex_role_relationships = 0
        valid_reaction_complex_relationships = 0
        
        for complex_id, complex_data in mapped_complexes.items():
            for role_id in complex_data.get('roles', []):
                if role_id in mapped_roles:
                    valid_complex_role_relationships += 1
        
        for reaction_id, reaction_data in mapped_reactions.items():
            for complex_id in reaction_data.get('complexes', []):
                if complex_id in mapped_complexes:
                    valid_reaction_complex_relationships += 1
        
        # Analyze source distribution for mapped entities
        mapped_role_sources = Counter(rdata.get('source', 'unknown') for rdata in mapped_roles.values())
        
        clean_stats = {
            'entity_counts': {
                'mapped_roles': len(mapped_roles),
                'mapped_reactions': len(mapped_reactions),
                'mapped_complexes': len(mapped_complexes),
                'total_mapped_entities': len(mapped_roles) + len(mapped_reactions) + len(mapped_complexes)
            },
            'relationship_counts': {
                'valid_complex_role_relationships': valid_complex_role_relationships,
                'valid_reaction_complex_relationships': valid_reaction_complex_relationships,
                'total_valid_relationships': valid_complex_role_relationships + valid_reaction_complex_relationships
            },
            'source_distribution': {
                'mapped_role_sources': dict(mapped_role_sources)
            },
            'data_quality_metrics': {
                'role_mapping_rate': len(mapped_roles) / len(roles) if roles else 0,
                'reaction_mapping_rate': len(mapped_reactions) / len(reactions) if reactions else 0,
                'complex_mapping_rate': len(mapped_complexes) / len(complexes) if complexes else 0,
                'overall_mapping_rate': (len(mapped_roles) + len(mapped_reactions) + len(mapped_complexes)) / 
                                      (len(roles) + len(reactions) + len(complexes)) if (roles or reactions or complexes) else 0
            }
        }
        
        logger.info(f"Clean ontology will contain {clean_stats['entity_counts']['total_mapped_entities']} entities "
                   f"and {clean_stats['relationship_counts']['total_valid_relationships']} relationships")
        
        return clean_stats
    
    def run_full_analysis(self) -> Dict:
        """Run the complete analysis and return all results."""
        logger.info("Starting comprehensive unmapped entities analysis...")
        
        self.analysis_results = {
            'analysis_metadata': {
                'template_data_path': str(self.template_data_path),
                'total_entities': len(self.data.get('roles', {})) + len(self.data.get('reactions', {})) + len(self.data.get('complexes', {})),
                'analysis_timestamp': str(Path(__file__).stat().st_mtime)
            },
            'role_analysis': self.analyze_role_mappings(),
            'reaction_analysis': self.analyze_reaction_mappings(),
            'complex_analysis': self.analyze_complex_mappings(),
            'relationship_integrity': self.analyze_relationship_integrity(),
            'unmapped_entities': self.extract_unmapped_entities(),
            'broken_relationships': self.extract_broken_relationships(),
            'clean_ontology_stats': self.extract_clean_ontology_stats()
        }
        
        logger.info("Comprehensive analysis completed successfully")
        return self.analysis_results
    
    def save_results(self, output_dir: str):
        """Save analysis results to separate JSON files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save main analysis results
        with open(output_path / 'comprehensive_analysis.json', 'w') as f:
            json.dump(self.analysis_results, f, indent=2)
        
        # Save unmapped entities separately
        with open(output_path / 'unmapped_entities.json', 'w') as f:
            json.dump(self.analysis_results['unmapped_entities'], f, indent=2)
        
        # Save broken relationships separately
        with open(output_path / 'broken_relationships.json', 'w') as f:
            json.dump(self.analysis_results['broken_relationships'], f, indent=2)
        
        # Save clean ontology stats separately
        with open(output_path / 'clean_ontology_stats.json', 'w') as f:
            json.dump(self.analysis_results['clean_ontology_stats'], f, indent=2)
        
        logger.info(f"Analysis results saved to {output_path}")


def main():
    """Main execution function."""
    # Input and output paths
    template_data_path = "/Users/jplfaria/repos/ModelSEEDTemplates/templates/ontology/pyobo_builder/intermediate/template_data.json"
    output_dir = "/Users/jplfaria/repos/ModelSEEDTemplates/templates/ontology/pyobo_builder/analysis_output"
    
    # Create analyzer and run analysis
    analyzer = UnmappedEntitiesAnalyzer(template_data_path)
    results = analyzer.run_full_analysis()
    analyzer.save_results(output_dir)
    
    # Print summary
    print("\n" + "="*80)
    print("SEED UNIFIED ONTOLOGY ANALYSIS SUMMARY")
    print("="*80)
    
    print(f"\nROLE ANALYSIS:")
    role_stats = results['role_analysis']
    print(f"  Total roles: {role_stats['total_roles']}")
    print(f"  Mapped roles: {role_stats['mapped_roles']} ({role_stats['mapped_roles']/role_stats['total_roles']*100:.1f}%)")
    print(f"  Unmapped roles: {role_stats['unmapped_roles']} ({role_stats['unmapped_roles']/role_stats['total_roles']*100:.1f}%)")
    print(f"  Source breakdown: {role_stats['source_breakdown']}")
    
    print(f"\nREACTION ANALYSIS:")
    reaction_stats = results['reaction_analysis']
    print(f"  Total reactions: {reaction_stats['total_reactions']}")
    print(f"  Mapped reactions: {reaction_stats['mapped_reactions']} ({reaction_stats['mapped_reactions']/reaction_stats['total_reactions']*100:.1f}%)")
    print(f"  Unmapped reactions: {reaction_stats['unmapped_reactions']} ({reaction_stats['unmapped_reactions']/reaction_stats['total_reactions']*100:.1f}%)")
    
    print(f"\nCOMPLEX ANALYSIS:")
    complex_stats = results['complex_analysis']
    print(f"  Total complexes: {complex_stats['total_complexes']}")
    print(f"  Mapped complexes: {complex_stats['mapped_complexes']} ({complex_stats['mapped_complexes']/complex_stats['total_complexes']*100:.1f}%)")
    print(f"  Unmapped complexes: {complex_stats['unmapped_complexes']} ({complex_stats['unmapped_complexes']/complex_stats['total_complexes']*100:.1f}%)")
    
    print(f"\nRELATIONSHIP INTEGRITY:")
    integrity_stats = results['relationship_integrity']
    cr_stats = integrity_stats['complex_role_relationships']
    rc_stats = integrity_stats['reaction_complex_relationships']
    print(f"  Complex-Role relationships: {cr_stats['total']} total, {cr_stats['both_mapped']} both mapped ({cr_stats['both_mapped']/cr_stats['total']*100:.1f}%)")
    print(f"  Reaction-Complex relationships: {rc_stats['total']} total, {rc_stats['both_mapped']} both mapped ({rc_stats['both_mapped']/rc_stats['total']*100:.1f}%)")
    
    print(f"\nCLEAN ONTOLOGY PROJECTION:")
    clean_stats = results['clean_ontology_stats']
    entity_counts = clean_stats['entity_counts']
    relationship_counts = clean_stats['relationship_counts']
    print(f"  Clean entities: {entity_counts['total_mapped_entities']} ({entity_counts['mapped_roles']} roles, {entity_counts['mapped_reactions']} reactions, {entity_counts['mapped_complexes']} complexes)")
    print(f"  Valid relationships: {relationship_counts['total_valid_relationships']}")
    print(f"  Overall mapping rate: {clean_stats['data_quality_metrics']['overall_mapping_rate']*100:.1f}%")
    
    print(f"\nOUTPUT FILES GENERATED:")
    print(f"  - comprehensive_analysis.json")
    print(f"  - unmapped_entities.json") 
    print(f"  - broken_relationships.json")
    print(f"  - clean_ontology_stats.json")
    print(f"\nAll files saved to: {output_dir}")


if __name__ == "__main__":
    main()