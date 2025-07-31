"""
ModelSEED Extractor for modelseed.json.gz

Extracts:
- Compound definitions with cross-references
- Reaction definitions with cross-references  
- KEGG, ChEBI, MetaCyc mappings
- ModelSEED-specific metadata
"""

import json
import gzip
import logging
from typing import Dict, List, Set, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelSEEDExtractor:
    """Extracts compounds and reactions from ModelSEED JSON files."""
    
    def __init__(self, modelseed_path: str):
        """Initialize with path to modelseed.json.gz file."""
        self.modelseed_path = Path(modelseed_path)
        self.data = None
        self._load_modelseed()
    
    def _load_modelseed(self):
        """Load the compressed ModelSEED JSON file."""
        try:
            with gzip.open(self.modelseed_path, 'rt') as f:
                self.data = json.load(f)
            
            # ModelSEED JSON follows OBOJSON format with graphs
            self.nodes = []
            self.edges = []
            
            for graph in self.data.get('graphs', []):
                self.nodes.extend(graph.get('nodes', []))
                self.edges.extend(graph.get('edges', []))
            
            logger.info(f"Loaded ModelSEED with {len(self.nodes)} nodes and {len(self.edges)} edges")
        except Exception as e:
            logger.error(f"Failed to load ModelSEED data: {e}")
            raise
    
    def _parse_xrefs(self, xrefs_list: List[Dict]) -> Dict[str, List[str]]:
        """
        Parse cross-references from ModelSEED format.
        
        Args:
            xrefs_list: List of xref dictionaries with 'val' field
            
        Returns:
            Dict mapping database names to lists of IDs
        """
        xrefs = {}
        
        for xref in xrefs_list:
            xref_val = xref.get('val', '')
            
            # Parse different xref formats
            if xref_val.startswith('CHEBI:'):
                xrefs.setdefault('chebi', []).append(xref_val)
            elif xref_val.startswith('kegg.compound:'):
                # Handle multiple KEGG IDs separated by semicolon
                kegg_ids = xref_val.replace('kegg.compound:', '').rstrip(';').split(';')
                xrefs.setdefault('kegg', []).extend([kid.strip() for kid in kegg_ids if kid.strip()])
            elif xref_val.startswith('metacyc.compound:'):
                # Handle multiple MetaCyc IDs separated by semicolon
                metacyc_ids = xref_val.replace('metacyc.compound:', '').rstrip(';').split(';')
                xrefs.setdefault('metacyc', []).extend([mid.strip() for mid in metacyc_ids if mid.strip()])
            elif xref_val.startswith('seed.reaction:'):
                seed_rxn_id = xref_val.replace('seed.reaction:', '')
                xrefs.setdefault('seed_reaction', []).append(seed_rxn_id)
        
        return xrefs
    
    def extract_compounds(self) -> Dict[str, Dict]:
        """
        Extract compound definitions with cross-references.
        
        Returns:
            Dict mapping compound IDs to compound data
        """
        compounds = {}
        
        for node in self.nodes:
            node_id = node.get('id', '')
            
            # Filter for compound nodes
            if 'compounds' in node_id and node.get('type') == 'CLASS':
                # Extract ModelSEED compound ID (cpd00001 from URL)
                compound_id = node_id.split('/')[-1]
                
                # Parse cross-references
                xrefs = {}
                if 'meta' in node and 'xrefs' in node['meta']:
                    xrefs = self._parse_xrefs(node['meta']['xrefs'])
                
                compounds[compound_id] = {
                    'id': compound_id,
                    'name': node.get('lbl', ''),
                    'uri': node_id,
                    'xrefs': xrefs,
                    'type': 'compound'
                }
        
        logger.info(f"Extracted {len(compounds)} compounds")
        return compounds
    
    def extract_reactions(self) -> Dict[str, Dict]:
        """
        Extract reaction definitions with cross-references.
        
        Returns:
            Dict mapping reaction IDs to reaction data
        """
        reactions = {}
        
        for node in self.nodes:
            node_id = node.get('id', '')
            
            # Filter for reaction nodes
            if 'reactions' in node_id and node.get('type') == 'CLASS':
                # Extract ModelSEED reaction ID (rxn00001 from URL)
                reaction_id = node_id.split('/')[-1]
                
                # Parse cross-references
                xrefs = {}
                if 'meta' in node and 'xrefs' in node['meta']:
                    xrefs = self._parse_xrefs(node['meta']['xrefs'])
                
                reactions[reaction_id] = {
                    'id': reaction_id,
                    'name': node.get('lbl', ''),
                    'uri': node_id,
                    'xrefs': xrefs,
                    'type': 'reaction'
                }
        
        logger.info(f"Extracted {len(reactions)} reactions")
        return reactions
    
    def extract_relationships(self) -> List[Dict]:
        """
        Extract relationships between entities from edges.
        
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        
        for edge in self.edges:
            relationship = {
                'subject': edge.get('sub'),
                'predicate': edge.get('pred'),
                'object': edge.get('obj'),
                'type': 'relationship'
            }
            relationships.append(relationship)
        
        logger.info(f"Extracted {len(relationships)} relationships")
        return relationships
    
    def get_compound_xrefs_summary(self) -> Dict[str, int]:
        """
        Get summary of cross-reference coverage for compounds.
        
        Returns:
            Dict mapping database names to counts
        """
        compounds = self.extract_compounds()
        xref_counts = {}
        
        for compound_data in compounds.values():
            for db_name, db_refs in compound_data['xrefs'].items():
                xref_counts[db_name] = xref_counts.get(db_name, 0) + len(db_refs)
        
        return xref_counts
    
    def get_reaction_xrefs_summary(self) -> Dict[str, int]:
        """
        Get summary of cross-reference coverage for reactions.
        
        Returns:
            Dict mapping database names to counts
        """
        reactions = self.extract_reactions()
        xref_counts = {}
        
        for reaction_data in reactions.values():
            for db_name, db_refs in reaction_data['xrefs'].items():
                xref_counts[db_name] = xref_counts.get(db_name, 0) + len(db_refs)
        
        return xref_counts
    
    def extract_all_data(self) -> Dict:
        """
        Extract all data from ModelSEED in a single call.
        
        Returns:
            Dict containing all extracted data
        """
        return {
            'compounds': self.extract_compounds(),
            'reactions': self.extract_reactions(),
            'relationships': self.extract_relationships(),
            'compound_xrefs_summary': self.get_compound_xrefs_summary(),
            'reaction_xrefs_summary': self.get_reaction_xrefs_summary()
        }