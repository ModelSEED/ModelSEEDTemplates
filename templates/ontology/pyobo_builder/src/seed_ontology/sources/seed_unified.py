"""
PyOBO source for SEED unified ontology.

This module creates a unified ontology combining:
- SEED roles and subsystems
- ModelSEED compounds and reactions 
- Template complexes and relationships

Following OBO Foundry principles and PyOBO conventions.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Iterable, Tuple

import bioontologies
from pyobo import Obo, Reference, Term, TypeDef
from pyobo.utils.io import multidict
from pyobo.utils.path import ensure_df

logger = logging.getLogger(__name__)

# Ontology metadata
PREFIX = "seed_unified"
DEFINITION = "SEED unified ontology combining roles, compounds, reactions, and complexes"
HOMEPAGE = "https://modelseed.org"
VERSION = "2025-01-30"

# Define custom relationship types following OBO conventions
# Use RO prefix for standard relations ontology compatibility
ROLE_ENABLES_REACTION = TypeDef(
    reference=Reference(prefix="RO", identifier="0002328"),
    definition="A role that enables a biochemical reaction to occur",
    comment="Based on RO:0002328 'functionally related to'"
)

COMPLEX_HAS_ROLE = TypeDef(
    reference=Reference(prefix="RO", identifier="0000087"),
    definition="A protein complex that has a specific functional role",
    comment="Based on RO:0000087 'has role'"
)

REACTION_HAS_PRODUCT = TypeDef(
    reference=Reference(prefix="RO", identifier="0002234"),
    definition="A reaction that produces a specific compound",
    comment="Based on RO:0002234 'has output'"
)

REACTION_HAS_REACTANT = TypeDef(
    reference=Reference(prefix="RO", identifier="0002233"),
    definition="A reaction that consumes a specific compound",
    comment="Based on RO:0002233 'has input'"
)

HAS_NORMALIZED_FORM = TypeDef(
    reference=Reference(prefix="SEED", identifier="0000001"),
    definition="Links an entity to its normalized representation for performance",
    comment="Custom property for optimized matching and querying"
)

COMPLEX_ENABLES_REACTION = TypeDef(
    reference=Reference(prefix="SEED", identifier="0000002"),
    definition="A protein complex that enables a biochemical reaction",
    comment="Derived relationship from complex->role->reaction chains"
)

# Define entity type constants
ROLE_TYPE = "SEEDRole"
COMPOUND_TYPE = "SEEDCompound" 
REACTION_TYPE = "SEEDReaction"
COMPLEX_TYPE = "SEEDComplex"


def get_obo() -> Obo:
    """Build the SEED unified ontology using PyOBO."""
    logger.info("Building SEED unified ontology")
    
    # Initialize ontology with metadata
    obo = Obo(
        ontology=PREFIX,
        name="SEED Unified Ontology",
        definition=DEFINITION,
        homepage=HOMEPAGE,
        version=VERSION
    )
    
    # Add custom relationship types
    obo.typedefs.extend([
        ROLE_ENABLES_REACTION,
        COMPLEX_HAS_ROLE,
        REACTION_HAS_PRODUCT,
        REACTION_HAS_REACTANT,
        HAS_NORMALIZED_FORM,
        COMPLEX_ENABLES_REACTION
    ])
    
    # Load data from extractors
    data = _load_extracted_data()
    
    # Add terms for each entity type
    _add_role_terms(obo, data)
    _add_compound_terms(obo, data)
    _add_reaction_terms(obo, data)
    _add_complex_terms(obo, data)
    
    # Add relationships
    _add_relationships(obo, data)
    
    logger.info(f"Built ontology with {len(obo.terms)} terms")
    return obo


def _load_extracted_data() -> Dict:
    """Load pre-extracted data from intermediate files."""
    # This will be populated by the build pipeline
    intermediate_dir = Path(__file__).parent.parent.parent.parent / "intermediate"
    
    data = {}
    
    # Load template data
    template_file = intermediate_dir / "template_data.json"
    if template_file.exists():
        with open(template_file) as f:
            data['template'] = json.load(f)
    
    # Load ModelSEED data  
    modelseed_file = intermediate_dir / "modelseed_data.json"
    if modelseed_file.exists():
        with open(modelseed_file) as f:
            data['modelseed'] = json.load(f)
    
    # Load SEED roles data
    seed_file = intermediate_dir / "seed_roles_data.json"
    if seed_file.exists():
        with open(seed_file) as f:
            data['seed_roles'] = json.load(f)
    
    return data


def _add_role_terms(obo: Obo, data: Dict) -> None:
    """Add SEED role terms to the ontology."""
    if 'seed_roles' not in data or 'roles' not in data['seed_roles']:
        logger.warning("No SEED roles data found")
        return
    
    roles = data['seed_roles']['roles']
    logger.info(f"Adding {len(roles)} role terms")
    
    for role_id, role_data in roles.items():
        # Create role term
        term = Term(
            reference=Reference(prefix=PREFIX, identifier=f"role_{role_id}"),
            name=role_data['name'],
            definition=f"SEED functional role: {role_data['name']}",
            comment=f"SEED role ID: {role_id}"
        )
        
        # Add normalized form for performance
        if role_data.get('normalized_name'):
            term.annotate_literal(
                HAS_NORMALIZED_FORM,
                role_data['normalized_name']
            )
        
        # Add cross-references
        if 'xrefs' in role_data:
            for db, refs in role_data['xrefs'].items():
                for ref in refs:
                    if db == 'seed_reactions':
                        term.annotate_object(
                            ROLE_ENABLES_REACTION,
                            Reference(prefix=PREFIX, identifier=f"reaction_{ref}")
                        )
        
        # Add original SEED URI as annotation
        term.annotate_literal("original_uri", role_data.get('uri', ''))
        
        obo.terms.append(term)


def _add_compound_terms(obo: Obo, data: Dict) -> None:
    """Add ModelSEED compound terms to the ontology."""
    if 'modelseed' not in data or 'compounds' not in data['modelseed']:
        logger.warning("No ModelSEED compounds data found")
        return
    
    compounds = data['modelseed']['compounds']
    logger.info(f"Adding {len(compounds)} compound terms")
    
    for compound_id, compound_data in compounds.items():
        # Create compound term
        term = Term(
            reference=Reference(prefix=PREFIX, identifier=f"compound_{compound_id}"),
            name=compound_data['name'],
            definition=f"ModelSEED compound: {compound_data['name']}",
            comment=f"ModelSEED compound ID: {compound_id}"
        )
        
        # Add cross-references to external databases
        if 'xrefs' in compound_data:
            for db, refs in compound_data['xrefs'].items():
                for ref in refs:
                    if db == 'chebi':
                        term.append_xref(Reference(prefix='CHEBI', identifier=ref.replace('CHEBI:', '')))
                    elif db == 'kegg':
                        term.append_xref(Reference(prefix='kegg.compound', identifier=ref))
                    elif db == 'metacyc':
                        term.append_xref(Reference(prefix='metacyc.compound', identifier=ref))
        
        # Add original ModelSEED URI
        term.annotate_literal("original_uri", compound_data.get('uri', ''))
        
        obo.terms.append(term)


def _add_reaction_terms(obo: Obo, data: Dict) -> None:
    """Add ModelSEED reaction terms to the ontology."""
    if 'modelseed' not in data or 'reactions' not in data['modelseed']:
        logger.warning("No ModelSEED reactions data found")
        return
    
    reactions = data['modelseed']['reactions']
    logger.info(f"Adding {len(reactions)} reaction terms")
    
    for reaction_id, reaction_data in reactions.items():
        # Create reaction term
        term = Term(
            reference=Reference(prefix=PREFIX, identifier=f"reaction_{reaction_id}"),
            name=reaction_data['name'],
            definition=f"ModelSEED reaction: {reaction_data['name']}",
            comment=f"ModelSEED reaction ID: {reaction_id}"
        )
        
        # Add cross-references
        if 'xrefs' in reaction_data:
            for db, refs in reaction_data['xrefs'].items():
                for ref in refs:
                    if db == 'kegg':
                        term.append_xref(Reference(prefix='kegg.reaction', identifier=ref))
                    elif db == 'metacyc':
                        term.append_xref(Reference(prefix='metacyc.reaction', identifier=ref))
        
        # Add original ModelSEED URI
        term.annotate_literal("original_uri", reaction_data.get('uri', ''))
        
        obo.terms.append(term)


def _add_complex_terms(obo: Obo, data: Dict) -> None:
    """Add template complex terms to the ontology."""
    if 'template' not in data or 'complexes' not in data['template']:
        logger.warning("No template complexes data found")
        return
    
    complexes = data['template']['complexes']
    logger.info(f"Adding {len(complexes)} complex terms")
    
    for complex_id, complex_data in complexes.items():
        # Create complex term
        term = Term(
            reference=Reference(prefix=PREFIX, identifier=f"complex_{complex_id}"),
            name=complex_data['name'],
            definition=f"ModelSEED protein complex: {complex_data['name']}",
            comment=f"ModelSEED complex ID: {complex_id}"
        )
        
        # Add confidence score
        if 'confidence' in complex_data:
            term.annotate_literal("confidence", complex_data['confidence'])
        
        # Add source information
        if 'source' in complex_data:
            term.annotate_literal("source", complex_data['source'])
        
        # Add original SEED URI
        if 'seed_url' in complex_data:
            term.annotate_literal("original_uri", complex_data['seed_url'])
        
        obo.terms.append(term)


def _add_relationships(obo: Obo, data: Dict) -> None:
    """Add semantic relationships between entities."""
    logger.info("Adding semantic relationships")
    
    # Add complex-role relationships
    _add_complex_role_relationships(obo, data)
    
    # Add reaction-complex relationships  
    _add_reaction_complex_relationships(obo, data)
    
    # Add derived complex-reaction relationships
    _add_derived_complex_reaction_relationships(obo, data)


def _add_complex_role_relationships(obo: Obo, data: Dict) -> None:
    """Add relationships between complexes and roles."""
    if 'template' not in data or 'complex_role_relationships' not in data['template']:
        return
    
    relationships = data['template']['complex_role_relationships']
    
    for complex_id, role_id, metadata in relationships:
        # Find the complex and role terms
        complex_ref = Reference(prefix=PREFIX, identifier=f"complex_{complex_id}")
        role_ref = Reference(prefix=PREFIX, identifier=f"role_{role_id}")
        
        # Find complex term and add relationship
        for term in obo.terms:
            if term.reference == complex_ref:
                term.annotate_object(COMPLEX_HAS_ROLE, role_ref)
                
                # Add metadata as annotations
                if metadata.get('triggering'):
                    term.annotate_literal("has_triggering_role", role_id)
                if metadata.get('optional'):
                    term.annotate_literal("has_optional_role", role_id)
                break


def _add_reaction_complex_relationships(obo: Obo, data: Dict) -> None:
    """Add relationships between reactions and complexes."""
    if 'template' not in data or 'reaction_complex_relationships' not in data['template']:
        return
    
    relationships = data['template']['reaction_complex_relationships']
    
    for reaction_id, complex_id in relationships:
        # Find the reaction and complex terms
        reaction_ref = Reference(prefix=PREFIX, identifier=f"reaction_{reaction_id}")
        complex_ref = Reference(prefix=PREFIX, identifier=f"complex_{complex_id}")
        
        # Add bidirectional relationship
        for term in obo.terms:
            if term.reference == complex_ref:
                term.annotate_object(COMPLEX_ENABLES_REACTION, reaction_ref)
                break


def _add_derived_complex_reaction_relationships(obo: Obo, data: Dict) -> None:
    """Add derived relationships: complex -> role -> reaction chains."""
    if not all(k in data for k in ['template', 'seed_roles']):
        return
    
    # Build mapping from role to reactions
    role_to_reactions = {}
    if 'role_reaction_mappings' in data['seed_roles']:
        role_to_reactions = data['seed_roles']['role_reaction_mappings']
    
    # Build mapping from complex to roles
    complex_to_roles = {}
    if 'complex_role_relationships' in data['template']:
        for complex_id, role_id, metadata in data['template']['complex_role_relationships']:
            complex_to_roles.setdefault(complex_id, []).append(role_id)
    
    # Create derived complex -> reaction relationships
    derived_count = 0
    for complex_id, role_ids in complex_to_roles.items():
        complex_ref = Reference(prefix=PREFIX, identifier=f"complex_{complex_id}")
        
        for role_id in role_ids:
            if role_id in role_to_reactions:
                for reaction_id in role_to_reactions[role_id]:
                    reaction_ref = Reference(prefix=PREFIX, identifier=f"reaction_{reaction_id}")
                    
                    # Add derived relationship
                    for term in obo.terms:
                        if term.reference == complex_ref:
                            term.annotate_object(COMPLEX_ENABLES_REACTION, reaction_ref)
                            derived_count += 1
                            break
    
    logger.info(f"Added {derived_count} derived complex-reaction relationships")


# For compatibility with PyOBO discovery
def get_id_name_mapping() -> Dict[str, str]:
    """Get mapping of identifiers to names."""
    obo = get_obo()
    return {term.reference.identifier: term.name for term in obo.terms}


def get_id_definition_mapping() -> Dict[str, str]:
    """Get mapping of identifiers to definitions."""
    obo = get_obo()
    return {term.reference.identifier: term.definition for term in obo.terms if term.definition}


# PyOBO source configuration
if __name__ == "__main__":
    # Allow direct execution for testing
    obo = get_obo()
    print(f"Generated ontology with {len(obo.terms)} terms")
    print(f"Typedefs: {len(obo.typedefs)}")
    
    # Show sample terms
    for i, term in enumerate(obo.terms[:5]):
        print(f"  {term.reference}: {term.name}")
        if i >= 4:
            print("  ...")
            break