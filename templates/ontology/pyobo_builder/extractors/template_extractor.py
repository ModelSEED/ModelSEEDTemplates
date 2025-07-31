"""
Template Extractor for GramNegModelTemplateV6_with_ontology.json

Extracts:
- Complex definitions and their roles
- Role-reaction relationships
- Triggering flags for complexes
- Template-specific metadata
"""

import json
import logging
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class TemplateExtractor:
    """Extracts semantic relationships from ModelSEED template files."""
    
    def __init__(self, template_path: str):
        """Initialize with path to template JSON file."""
        self.template_path = Path(template_path)
        self.data = None
        self._load_template()
    
    def _load_template(self):
        """Load the template JSON file."""
        try:
            with open(self.template_path, 'r') as f:
                self.data = json.load(f)
            logger.info(f"Loaded template with {len(self.data.get('complexes', []))} complexes")
        except Exception as e:
            logger.error(f"Failed to load template: {e}")
            raise
    
    def extract_complexes(self) -> Dict[str, Dict]:
        """
        Extract complex definitions with their roles and metadata.
        
        Returns:
            Dict mapping complex IDs to complex data including:
            - name, roles, triggering flags, confidence, etc.
        """
        complexes = {}
        
        for complex_data in self.data.get('complexes', []):
            complex_id = complex_data.get('id')
            if not complex_id:
                continue
                
            # Extract roles for this complex
            roles = []
            triggering_roles = []
            optional_roles = []
            
            for role_data in complex_data.get('complexroles', []):
                role_ref = role_data.get('templaterole_ref', '')
                # Extract role ID from reference (~/roles/id/ftr11152 -> ftr11152)
                role_id = role_ref.split('/')[-1] if role_ref else None
                
                if role_id:
                    roles.append(role_id)
                    if role_data.get('triggering', 0) == 1:
                        triggering_roles.append(role_id)
                    if role_data.get('optional_role', 0) == 1:
                        optional_roles.append(role_id)
            
            complexes[complex_id] = {
                'id': complex_id,
                'name': complex_data.get('name'),
                'roles': roles,
                'triggering_roles': triggering_roles,
                'optional_roles': optional_roles,
                'confidence': complex_data.get('confidence'),
                'source': complex_data.get('source'),
                'seed_url': complex_data.get('seed_url'),
                'seed_id': complex_data.get('seed_id'),
                'role_seeds': complex_data.get('role_seeds', [])
            }
        
        logger.info(f"Extracted {len(complexes)} complexes")
        return complexes
    
    def extract_reactions(self) -> Dict[str, Dict]:
        """
        Extract reaction definitions and their metadata.
        
        Returns:
            Dict mapping reaction IDs to reaction data
        """
        reactions = {}
        
        for reaction_data in self.data.get('reactions', []):
            reaction_id = reaction_data.get('id')
            if not reaction_id:
                continue
                
            # Extract complex references
            complex_refs = []
            for comp_ref in reaction_data.get('templatecomplex_refs', []):
                # Extract complex ID from reference
                complex_id = comp_ref.split('/')[-1] if comp_ref else None
                if complex_id:
                    complex_refs.append(complex_id)
            
            reactions[reaction_id] = {
                'id': reaction_id,
                'name': reaction_data.get('name'),
                'direction': reaction_data.get('direction'),
                'complexes': complex_refs,
                'type': reaction_data.get('type'),
                'reference': reaction_data.get('reference'),
                'seed_url': reaction_data.get('seed_url'),
                'seed_id': reaction_data.get('seed_id')
            }
        
        logger.info(f"Extracted {len(reactions)} reactions")
        return reactions
    
    def extract_roles(self) -> Dict[str, Dict]:
        """
        Extract role definitions from the template.
        
        Returns:
            Dict mapping role IDs to role data
        """
        roles = {}
        
        for role_data in self.data.get('roles', []):
            role_id = role_data.get('id')
            if not role_id:
                continue
                
            roles[role_id] = {
                'id': role_id,
                'name': role_data.get('name'),
                'source': role_data.get('source'),
                'seed_url': role_data.get('seed_url'),
                'seed_id': role_data.get('seed_id'),
                'aliases': role_data.get('aliases', [])
            }
        
        logger.info(f"Extracted {len(roles)} roles")
        return roles
    
    def extract_complex_role_relationships(self) -> List[Tuple[str, str, Dict]]:
        """
        Extract complex-role relationships with metadata.
        
        Returns:
            List of tuples (complex_id, role_id, metadata)
        """
        relationships = []
        
        complexes = self.extract_complexes()
        for complex_id, complex_data in complexes.items():
            for role_id in complex_data['roles']:
                metadata = {
                    'triggering': role_id in complex_data['triggering_roles'],
                    'optional': role_id in complex_data['optional_roles'],
                    'confidence': complex_data['confidence']
                }
                relationships.append((complex_id, role_id, metadata))
        
        logger.info(f"Extracted {len(relationships)} complex-role relationships")
        return relationships
    
    def extract_reaction_complex_relationships(self) -> List[Tuple[str, str]]:
        """
        Extract reaction-complex relationships.
        
        Returns:
            List of tuples (reaction_id, complex_id)
        """
        relationships = []
        
        reactions = self.extract_reactions()
        for reaction_id, reaction_data in reactions.items():
            for complex_id in reaction_data['complexes']:
                relationships.append((reaction_id, complex_id))
        
        logger.info(f"Extracted {len(relationships)} reaction-complex relationships")
        return relationships
    
    def extract_all_data(self) -> Dict:
        """
        Extract all data from the template in a single call.
        
        Returns:
            Dict containing all extracted data
        """
        return {
            'complexes': self.extract_complexes(),
            'reactions': self.extract_reactions(),
            'roles': self.extract_roles(),
            'complex_role_relationships': self.extract_complex_role_relationships(),
            'reaction_complex_relationships': self.extract_reaction_complex_relationships()
        }