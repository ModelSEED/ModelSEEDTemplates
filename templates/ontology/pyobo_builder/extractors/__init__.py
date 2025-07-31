"""
Data extraction modules for SEED unified ontology system.

This package contains extractors for processing the three main source files:
- Template extractor: Processes GramNegModelTemplateV6_with_ontology.json
- ModelSEED extractor: Processes modelseed.json.gz
- SEED roles extractor: Processes seed.json
"""

from .template_extractor import TemplateExtractor
from .modelseed_extractor import ModelSEEDExtractor
from .seed_roles_extractor import SEEDRolesExtractor

__all__ = ['TemplateExtractor', 'ModelSEEDExtractor', 'SEEDRolesExtractor']