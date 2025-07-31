"""
SEED Roles Extractor for seed.json

Extracts:
- SEED role definitions with hierarchies
- Role-reaction cross-references
- SEED subsystem information
- Role normalization data
"""

import json
import logging
import re
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class SEEDRolesExtractor:
    """Extracts SEED roles and subsystem information."""
    
    def __init__(self, seed_path: str):
        """Initialize with path to seed.json file."""
        self.seed_path = Path(seed_path)
        self.data = None
        self.nodes = []
        self.edges = []
        self._load_seed()
    
    def _load_seed(self):
        """Load the SEED JSON file."""
        try:
            with open(self.seed_path, 'r') as f:
                self.data = json.load(f)
            
            # SEED JSON follows OBOJSON format with graphs
            for graph in self.data.get('graphs', []):
                self.nodes.extend(graph.get('nodes', []))
                self.edges.extend(graph.get('edges', []))
            
            logger.info(f"Loaded SEED with {len(self.nodes)} nodes and {len(self.edges)} edges")
        except Exception as e:
            logger.error(f"Failed to load SEED data: {e}")
            raise
    
    def _extract_role_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract SEED role ID from URL.
        
        Args:
            url: SEED role URL like 'https://pubseed.theseed.org/RoleEditor.cgi?page=ShowRole&Role=0000000000001'
            
        Returns:
            Role ID string or None
        """
        match = re.search(r'Role=(\d+)', url)
        return match.group(1) if match else None
    
    def _normalize_role_name(self, name: str) -> str:
        """
        Normalize role names for better matching.
        
        Args:
            name: Original role name
            
        Returns:
            Normalized role name
        """
        if not name:
            return ""
        
        # Convert to lowercase and normalize whitespace
        normalized = re.sub(r'\s+', ' ', name.lower().strip())
        
        # Remove common prefixes/suffixes that cause matching issues
        normalized = re.sub(r'^ec\s+', '', normalized)  # Remove EC prefix
        normalized = re.sub(r'\s+\(ec\s+[\d\.-]+\)$', '', normalized)  # Remove EC suffix
        
        return normalized
    
    def extract_roles(self) -> Dict[str, Dict]:
        """
        Extract SEED role definitions.
        
        Returns:
            Dict mapping role IDs to role data
        """
        roles = {}
        
        for node in self.nodes:
            if node.get('type') == 'CLASS':
                node_id = node.get('id', '')
                role_id = self._extract_role_id_from_url(node_id)
                
                if role_id:
                    role_name = node.get('lbl', '')
                    normalized_name = self._normalize_role_name(role_name)
                    
                    # Extract cross-references
                    xrefs = {}
                    if 'meta' in node and 'xrefs' in node['meta']:
                        for xref in node['meta']['xrefs']:
                            xref_val = xref.get('val', '')
                            if xref_val.startswith('seed.reaction:'):
                                reaction_id = xref_val.replace('seed.reaction:', '')
                                xrefs.setdefault('seed_reactions', []).append(reaction_id)
                    
                    roles[role_id] = {
                        'id': role_id,
                        'name': role_name,
                        'normalized_name': normalized_name,
                        'uri': node_id,
                        'xrefs': xrefs,
                        'type': 'role'
                    }
        
        logger.info(f"Extracted {len(roles)} SEED roles")
        return roles
    
    def extract_role_hierarchies(self) -> List[Tuple[str, str, str]]:
        """
        Extract hierarchical relationships between roles.
        
        Returns:
            List of tuples (parent_role_id, child_role_id, relationship_type)
        """
        hierarchies = []
        
        for edge in self.edges:
            pred = edge.get('pred', '')
            subject_url = edge.get('sub', '')
            object_url = edge.get('obj', '')
            
            subject_id = self._extract_role_id_from_url(subject_url)
            object_id = self._extract_role_id_from_url(object_url)
            
            if subject_id and object_id:
                # Determine relationship type based on predicate
                if 'subClassOf' in pred:
                    hierarchies.append((object_id, subject_id, 'is_a'))
                elif 'partOf' in pred:
                    hierarchies.append((object_id, subject_id, 'part_of'))
        
        logger.info(f"Extracted {len(hierarchies)} role hierarchies")
        return hierarchies
    
    def extract_role_reaction_mappings(self) -> Dict[str, List[str]]:
        """
        Extract mappings from roles to reactions.
        
        Returns:
            Dict mapping role IDs to lists of reaction IDs
        """
        mappings = {}
        roles = self.extract_roles()
        
        for role_id, role_data in roles.items():
            if 'seed_reactions' in role_data['xrefs']:
                mappings[role_id] = role_data['xrefs']['seed_reactions']
        
        logger.info(f"Extracted reaction mappings for {len(mappings)} roles")
        return mappings
    
    def build_name_to_id_index(self) -> Dict[str, List[str]]:
        """
        Build index from normalized names to role IDs for fast lookup.
        
        Returns:
            Dict mapping normalized names to lists of role IDs
        """
        name_index = {}
        roles = self.extract_roles()
        
        for role_id, role_data in roles.items():
            normalized_name = role_data['normalized_name']
            if normalized_name:
                name_index.setdefault(normalized_name, []).append(role_id)
        
        logger.info(f"Built name index with {len(name_index)} normalized names")
        return name_index
    
    def get_roles_with_reactions(self) -> Set[str]:
        """
        Get set of role IDs that have associated reactions.
        
        Returns:
            Set of role IDs with reaction mappings
        """
        roles_with_reactions = set()
        mappings = self.extract_role_reaction_mappings()
        
        for role_id, reactions in mappings.items():
            if reactions:  # Has at least one reaction
                roles_with_reactions.add(role_id)
        
        logger.info(f"Found {len(roles_with_reactions)} roles with reactions")
        return roles_with_reactions
    
    def get_subsystem_info(self) -> Dict:
        """
        Extract subsystem metadata from the graphs.
        
        Returns:
            Dict with subsystem information
        """
        subsystem_info = {}
        
        for graph in self.data.get('graphs', []):
            meta = graph.get('meta', {})
            if meta:
                subsystem_info = {
                    'title': None,
                    'description': None,
                    'version': None
                }
                
                for prop in meta.get('basicPropertyValues', []):
                    pred = prop.get('pred', '')
                    val = prop.get('val', '')
                    
                    if 'title' in pred:
                        subsystem_info['title'] = val
                    elif 'description' in pred:
                        subsystem_info['description'] = val
                    elif 'version' in pred:
                        subsystem_info['version'] = val
                
                break  # Take first graph's metadata
        
        return subsystem_info
    
    def extract_all_data(self) -> Dict:
        """
        Extract all data from SEED in a single call.
        
        Returns:
            Dict containing all extracted data
        """
        return {
            'roles': self.extract_roles(),
            'role_hierarchies': self.extract_role_hierarchies(),
            'role_reaction_mappings': self.extract_role_reaction_mappings(),
            'name_to_id_index': self.build_name_to_id_index(),
            'roles_with_reactions': list(self.get_roles_with_reactions()),
            'subsystem_info': self.get_subsystem_info()
        }