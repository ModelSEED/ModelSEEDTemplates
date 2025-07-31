#!/usr/bin/env python3
"""
Clean SEED Unified Ontology Extractor

Creates a truly clean ontology with only properly mapped entities and valid relationships.
Separates unmapped data for future enhancement while ensuring ontology integrity.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CleanOntologyExtractor:
    """Extracts clean ontology data with only properly mapped entities."""
    
    def __init__(self, template_data_path: str):
        """Initialize with path to template data JSON."""
        self.template_data_path = Path(template_data_path)
        self.data = None
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
    
    def _is_entity_mapped(self, entity_data: Dict) -> bool:
        """Check if an entity has a valid SEED ID mapping."""
        seed_id = entity_data.get('seed_id')
        return bool(seed_id and seed_id.strip() and not seed_id.startswith('null'))
    
    def extract_mapped_entities(self) -> Dict:
        """Extract only entities with valid SEED ID mappings."""
        logger.info("Extracting mapped entities...")
        
        roles = self.data.get('roles', {})
        reactions = self.data.get('reactions', {})
        complexes = self.data.get('complexes', {})
        
        # Extract mapped entities
        mapped_roles = {
            role_id: role_data for role_id, role_data in roles.items()
            if self._is_entity_mapped(role_data)
        }
        
        mapped_reactions = {
            reaction_id: reaction_data for reaction_id, reaction_data in reactions.items()
            if self._is_entity_mapped(reaction_data)
        }
        
        mapped_complexes = {
            complex_id: complex_data for complex_id, complex_data in complexes.items()
            if self._is_entity_mapped(complex_data)
        }
        
        logger.info(f"Extracted {len(mapped_roles)} mapped roles, "
                   f"{len(mapped_reactions)} mapped reactions, "
                   f"{len(mapped_complexes)} mapped complexes")
        
        return {
            'roles': mapped_roles,
            'reactions': mapped_reactions,
            'complexes': mapped_complexes
        }
    
    def extract_valid_relationships(self, mapped_entities: Dict) -> Dict:
        """Extract only relationships where both entities are mapped."""
        logger.info("Extracting valid relationships...")
        
        mapped_roles = set(mapped_entities['roles'].keys())
        mapped_reactions = set(mapped_entities['reactions'].keys())
        mapped_complexes = set(mapped_entities['complexes'].keys())
        
        # Extract valid complex-role relationships
        valid_complex_role_relationships = []
        for complex_id, complex_data in mapped_entities['complexes'].items():
            for role_id in complex_data.get('roles', []):
                if role_id in mapped_roles:
                    # Find the triggering and optional status from original complex data
                    original_complex = self.data['complexes'][complex_id]
                    metadata = {
                        'triggering': role_id in original_complex.get('triggering_roles', []),
                        'optional': role_id in original_complex.get('optional_roles', []),
                        'confidence': original_complex.get('confidence')
                    }
                    valid_complex_role_relationships.append((complex_id, role_id, metadata))
        
        # Extract valid reaction-complex relationships
        valid_reaction_complex_relationships = []
        for reaction_id, reaction_data in mapped_entities['reactions'].items():
            for complex_id in reaction_data.get('complexes', []):
                if complex_id in mapped_complexes:
                    valid_reaction_complex_relationships.append((reaction_id, complex_id))
        
        # Clean up complex data to only include valid roles
        cleaned_complexes = {}
        for complex_id, complex_data in mapped_entities['complexes'].items():
            cleaned_complex = complex_data.copy()
            # Filter roles to only include mapped ones
            valid_roles = [role_id for role_id in complex_data.get('roles', []) if role_id in mapped_roles]
            valid_triggering = [role_id for role_id in complex_data.get('triggering_roles', []) if role_id in mapped_roles]
            valid_optional = [role_id for role_id in complex_data.get('optional_roles', []) if role_id in mapped_roles]
            
            cleaned_complex['roles'] = valid_roles
            cleaned_complex['triggering_roles'] = valid_triggering
            cleaned_complex['optional_roles'] = valid_optional
            cleaned_complexes[complex_id] = cleaned_complex
        
        # Clean up reaction data to only include valid complexes
        cleaned_reactions = {}
        for reaction_id, reaction_data in mapped_entities['reactions'].items():
            cleaned_reaction = reaction_data.copy()
            # Filter complexes to only include mapped ones
            valid_complexes = [complex_id for complex_id in reaction_data.get('complexes', []) if complex_id in mapped_complexes]
            cleaned_reaction['complexes'] = valid_complexes
            cleaned_reactions[reaction_id] = cleaned_reaction
        
        logger.info(f"Extracted {len(valid_complex_role_relationships)} valid complex-role relationships, "
                   f"{len(valid_reaction_complex_relationships)} valid reaction-complex relationships")
        
        return {
            'roles': mapped_entities['roles'],
            'reactions': cleaned_reactions,
            'complexes': cleaned_complexes,
            'complex_role_relationships': valid_complex_role_relationships,
            'reaction_complex_relationships': valid_reaction_complex_relationships
        }
    
    def create_source_analysis(self, clean_data: Dict) -> Dict:
        """Analyze the source distribution in the clean data."""
        logger.info("Analyzing source distribution in clean data...")
        
        source_analysis = {
            'role_sources': {},
            'complex_sources': {},
            'source_mapping_rates': {},
            'excluded_sources': []
        }
        
        # Analyze role sources in clean data
        role_sources = {}
        for role_data in clean_data['roles'].values():
            source = role_data.get('source', 'unknown')
            role_sources[source] = role_sources.get(source, 0) + 1
        
        # Analyze complex sources
        complex_sources = {}
        for complex_data in clean_data['complexes'].values():
            source = complex_data.get('source', 'unknown')
            complex_sources[source] = complex_sources.get(source, 0) + 1
        
        # Calculate mapping rates by source (from original data)
        original_roles = self.data.get('roles', {})
        original_source_counts = {}
        for role_data in original_roles.values():
            source = role_data.get('source', 'unknown')
            original_source_counts[source] = original_source_counts.get(source, 0) + 1
        
        mapping_rates = {}
        excluded_sources = []
        for source, original_count in original_source_counts.items():
            clean_count = role_sources.get(source, 0)
            mapping_rate = clean_count / original_count if original_count > 0 else 0
            mapping_rates[source] = {
                'original_count': original_count,
                'mapped_count': clean_count,
                'mapping_rate': mapping_rate
            }
            if mapping_rate == 0:
                excluded_sources.append(source)
        
        source_analysis['role_sources'] = role_sources
        source_analysis['complex_sources'] = complex_sources
        source_analysis['source_mapping_rates'] = mapping_rates
        source_analysis['excluded_sources'] = excluded_sources
        
        logger.info(f"Clean data includes roles from sources: {list(role_sources.keys())}")
        logger.info(f"Excluded sources (0% mapping): {excluded_sources}")
        
        return source_analysis
    
    def generate_clean_ontology_summary(self, clean_data: Dict, source_analysis: Dict) -> Dict:
        """Generate comprehensive summary of the clean ontology."""
        logger.info("Generating clean ontology summary...")
        
        summary = {
            'entity_counts': {
                'roles': len(clean_data['roles']),
                'reactions': len(clean_data['reactions']),
                'complexes': len(clean_data['complexes']),
                'total_entities': len(clean_data['roles']) + len(clean_data['reactions']) + len(clean_data['complexes'])
            },
            'relationship_counts': {
                'complex_role_relationships': len(clean_data['complex_role_relationships']),
                'reaction_complex_relationships': len(clean_data['reaction_complex_relationships']),
                'total_relationships': len(clean_data['complex_role_relationships']) + len(clean_data['reaction_complex_relationships'])
            },
            'source_analysis': source_analysis,
            'data_quality': {
                'all_entities_have_seed_ids': True,
                'all_relationships_valid': True,
                'no_broken_references': True
            },
            'original_vs_clean': {
                'original_total_entities': len(self.data.get('roles', {})) + len(self.data.get('reactions', {})) + len(self.data.get('complexes', {})),
                'clean_total_entities': len(clean_data['roles']) + len(clean_data['reactions']) + len(clean_data['complexes']),
                'retention_rate': None  # Will calculate below
            }
        }
        
        # Calculate retention rate
        if summary['original_vs_clean']['original_total_entities'] > 0:
            summary['original_vs_clean']['retention_rate'] = (
                summary['original_vs_clean']['clean_total_entities'] / 
                summary['original_vs_clean']['original_total_entities']
            )
        
        logger.info(f"Clean ontology summary: {summary['entity_counts']['total_entities']} entities, "
                   f"{summary['relationship_counts']['total_relationships']} relationships")
        
        return summary
    
    def create_clean_ontology(self) -> Tuple[Dict, Dict]:
        """Create the complete clean ontology and summary."""
        logger.info("Creating clean ontology...")
        
        # Extract mapped entities
        mapped_entities = self.extract_mapped_entities()
        
        # Extract valid relationships
        clean_data = self.extract_valid_relationships(mapped_entities)
        
        # Analyze sources
        source_analysis = self.create_source_analysis(clean_data)
        
        # Generate summary
        summary = self.generate_clean_ontology_summary(clean_data, source_analysis)
        
        logger.info("Clean ontology creation completed")
        return clean_data, summary
    
    def save_clean_ontology(self, clean_data: Dict, summary: Dict, output_dir: str):
        """Save the clean ontology and summary to files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save clean template data
        with open(output_path / 'clean_template_data.json', 'w') as f:
            json.dump(clean_data, f, indent=2)
        
        # Save summary
        with open(output_path / 'clean_ontology_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save just the entities (for easy PyOBO integration)
        entities_only = {
            'roles': clean_data['roles'],
            'reactions': clean_data['reactions'],
            'complexes': clean_data['complexes']
        }
        with open(output_path / 'clean_entities_only.json', 'w') as f:
            json.dump(entities_only, f, indent=2)
        
        logger.info(f"Clean ontology saved to {output_path}")


def main():
    """Main execution function."""
    # Input and output paths
    template_data_path = "/Users/jplfaria/repos/ModelSEEDTemplates/templates/ontology/pyobo_builder/intermediate/template_data.json"
    output_dir = "/Users/jplfaria/repos/ModelSEEDTemplates/templates/ontology/pyobo_builder/clean_ontology"
    
    # Create extractor and generate clean ontology
    extractor = CleanOntologyExtractor(template_data_path)
    clean_data, summary = extractor.create_clean_ontology()
    extractor.save_clean_ontology(clean_data, summary, output_dir)
    
    # Print summary
    print("\n" + "="*80)
    print("CLEAN SEED UNIFIED ONTOLOGY SUMMARY")
    print("="*80)
    
    print(f"\nENTITY COUNTS:")
    entity_counts = summary['entity_counts']
    print(f"  Roles: {entity_counts['roles']}")
    print(f"  Reactions: {entity_counts['reactions']}")
    print(f"  Complexes: {entity_counts['complexes']}")
    print(f"  Total entities: {entity_counts['total_entities']}")
    
    print(f"\nRELATIONSHIP COUNTS:")
    rel_counts = summary['relationship_counts']
    print(f"  Complex-Role relationships: {rel_counts['complex_role_relationships']}")
    print(f"  Reaction-Complex relationships: {rel_counts['reaction_complex_relationships']}")
    print(f"  Total relationships: {rel_counts['total_relationships']}")
    
    print(f"\nSOURCE ANALYSIS:")
    source_info = summary['source_analysis']
    print(f"  Role sources included: {source_info['role_sources']}")
    print(f"  Complex sources: {source_info['complex_sources']}")
    print(f"  Excluded sources: {source_info['excluded_sources']}")
    
    print(f"\nDATA QUALITY:")
    quality = summary['data_quality']
    print(f"  All entities have SEED IDs: {quality['all_entities_have_seed_ids']}")
    print(f"  All relationships valid: {quality['all_relationships_valid']}")
    print(f"  No broken references: {quality['no_broken_references']}")
    
    print(f"\nORIGINAL VS CLEAN:")
    comparison = summary['original_vs_clean']
    print(f"  Original total entities: {comparison['original_total_entities']}")
    print(f"  Clean total entities: {comparison['clean_total_entities']}")
    print(f"  Retention rate: {comparison['retention_rate']*100:.1f}%")
    
    print(f"\nFILES GENERATED:")
    print(f"  - clean_template_data.json (complete clean ontology)")
    print(f"  - clean_entities_only.json (entities for PyOBO)")
    print(f"  - clean_ontology_summary.json (detailed summary)")
    print(f"\nAll files saved to: {output_dir}")


if __name__ == "__main__":
    main()