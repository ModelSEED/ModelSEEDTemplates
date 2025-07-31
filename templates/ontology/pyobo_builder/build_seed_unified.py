#!/usr/bin/env python3
"""
Build script for SEED unified ontology.

This script orchestrates the complete pipeline:
1. Extract data from 3 source files
2. Process and validate data  
3. Generate PyOBO ontology
4. Export to OWL and JSON-LD formats
5. Generate validation reports

Usage:
    python build_seed_unified.py [--output-dir OUTPUT_DIR] [--validate]
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add src and current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "src"))
sys.path.insert(0, str(current_dir))

from extractors import TemplateExtractor, ModelSEEDExtractor, SEEDRolesExtractor
from seed_ontology.sources.seed_unified import get_obo
import pyobo


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SEEDUnifiedBuilder:
    """Main builder class for SEED unified ontology."""
    
    def __init__(self, source_dir: Path, output_dir: Path):
        """
        Initialize builder with source and output directories.
        
        Args:
            source_dir: Directory containing source files
            output_dir: Directory for output files
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.intermediate_dir = Path(__file__).parent / "intermediate"
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.intermediate_dir.mkdir(parents=True, exist_ok=True)
        
        # Define source file paths
        self.template_path = self.source_dir / "enhanced_templates" / "GramNegModelTemplateV6_with_ontology.json"
        self.modelseed_path = self.source_dir / "json" / "modelseed.json.gz"
        self.seed_path = self.source_dir / "json" / "seed.json"
        
        # Validate source files exist
        self._validate_source_files()
    
    def _validate_source_files(self):
        """Validate that all required source files exist."""
        missing_files = []
        
        if not self.template_path.exists():
            missing_files.append(str(self.template_path))
        if not self.modelseed_path.exists():
            missing_files.append(str(self.modelseed_path))
        if not self.seed_path.exists():
            missing_files.append(str(self.seed_path))
        
        if missing_files:
            raise FileNotFoundError(f"Missing source files: {missing_files}")
        
        logger.info("All source files found")
    
    def extract_data(self) -> Dict[str, Any]:
        """
        Extract data from all source files.
        
        Returns:
            Dictionary containing all extracted data
        """
        logger.info("=== PHASE 1: EXTRACTING DATA ===")
        
        # Extract template data
        logger.info("Extracting template data...")
        template_extractor = TemplateExtractor(str(self.template_path))
        template_data = template_extractor.extract_all_data()
        
        # Save intermediate template data
        template_file = self.intermediate_dir / "template_data.json"
        with open(template_file, 'w') as f:
            json.dump(template_data, f, indent=2)
        logger.info(f"Saved template data to {template_file}")
        
        # Extract ModelSEED data
        logger.info("Extracting ModelSEED data...")
        modelseed_extractor = ModelSEEDExtractor(str(self.modelseed_path))
        modelseed_data = modelseed_extractor.extract_all_data()
        
        # Save intermediate ModelSEED data
        modelseed_file = self.intermediate_dir / "modelseed_data.json"
        with open(modelseed_file, 'w') as f:
            json.dump(modelseed_data, f, indent=2)
        logger.info(f"Saved ModelSEED data to {modelseed_file}")
        
        # Extract SEED roles data
        logger.info("Extracting SEED roles data...")
        seed_extractor = SEEDRolesExtractor(str(self.seed_path))
        seed_data = seed_extractor.extract_all_data()
        
        # Save intermediate SEED data
        seed_file = self.intermediate_dir / "seed_roles_data.json"
        with open(seed_file, 'w') as f:
            json.dump(seed_data, f, indent=2)
        logger.info(f"Saved SEED roles data to {seed_file}")
        
        # Combine all data
        combined_data = {
            'template': template_data,
            'modelseed': modelseed_data,
            'seed_roles': seed_data
        }
        
        # Generate extraction summary
        self._generate_extraction_summary(combined_data)
        
        return combined_data
    
    def _generate_extraction_summary(self, data: Dict[str, Any]):
        """Generate summary of extracted data."""
        summary = {
            'extraction_timestamp': str(Path(__file__).stat().st_mtime),
            'template': {
                'complexes': len(data['template'].get('complexes', {})),
                'reactions': len(data['template'].get('reactions', {})),
                'roles': len(data['template'].get('roles', {})),
                'complex_role_relationships': len(data['template'].get('complex_role_relationships', [])),
                'reaction_complex_relationships': len(data['template'].get('reaction_complex_relationships', []))
            },
            'modelseed': {
                'compounds': len(data['modelseed'].get('compounds', {})),
                'reactions': len(data['modelseed'].get('reactions', {})),
                'relationships': len(data['modelseed'].get('relationships', [])),
                'compound_xrefs_summary': data['modelseed'].get('compound_xrefs_summary', {}),
                'reaction_xrefs_summary': data['modelseed'].get('reaction_xrefs_summary', {})
            },
            'seed_roles': {
                'roles': len(data['seed_roles'].get('roles', {})),
                'role_hierarchies': len(data['seed_roles'].get('role_hierarchies', [])),
                'roles_with_reactions': len(data['seed_roles'].get('roles_with_reactions', [])),
                'role_reaction_mappings': len(data['seed_roles'].get('role_reaction_mappings', {}))
            }
        }
        
        summary_file = self.intermediate_dir / "extraction_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info("=== EXTRACTION SUMMARY ===")
        logger.info(f"Template: {summary['template']['complexes']} complexes, {summary['template']['reactions']} reactions, {summary['template']['roles']} roles")
        logger.info(f"ModelSEED: {summary['modelseed']['compounds']} compounds, {summary['modelseed']['reactions']} reactions")
        logger.info(f"SEED: {summary['seed_roles']['roles']} roles, {summary['seed_roles']['roles_with_reactions']} with reactions")
        logger.info(f"Relationships: {summary['template']['complex_role_relationships']} complex-role, {summary['template']['reaction_complex_relationships']} reaction-complex")
    
    def build_ontology(self) -> Any:
        """
        Build the unified ontology using PyOBO.
        
        Returns:
            PyOBO Obo object
        """
        logger.info("=== PHASE 2: BUILDING ONTOLOGY ===")
        
        try:
            obo = get_obo()
            logger.info(f"Built ontology with {len(obo.terms)} terms and {len(obo.typedefs)} type definitions")
            return obo
        except Exception as e:
            logger.error(f"Failed to build ontology: {e}")
            raise
    
    def export_formats(self, obo: Any):
        """
        Export ontology to different formats.
        
        Args:
            obo: PyOBO Obo object
        """
        logger.info("=== PHASE 3: EXPORTING FORMATS ===")
        
        try:
            # Export to OWL format
            owl_file = self.output_dir / "seed_unified.owl"
            logger.info(f"Exporting to OWL: {owl_file}")
            obo.write_default(owl_file)
            
            # Export to JSON-LD (OBOJSON) format
            json_file = self.output_dir / "seed_unified.json"
            logger.info(f"Exporting to JSON-LD: {json_file}")
            # Use OBO format for JSON export - modern PyOBO doesn't have write_obograph
            with open(json_file, 'w') as f:
                json.dump(obo.to_obo_graph(), f, indent=2, default=str)
            
            # Export term mappings
            mappings_file = self.output_dir / "term_mappings.json"
            mappings = {
                'id_to_name': {term.reference.identifier: term.name for term in obo.terms},
                'id_to_definition': {term.reference.identifier: term.definition for term in obo.terms if term.definition}
            }
            with open(mappings_file, 'w') as f:
                json.dump(mappings, f, indent=2)
            logger.info(f"Exported term mappings: {mappings_file}")
            
        except Exception as e:
            logger.error(f"Failed to export formats: {e}")
            raise
    
    def validate_ontology(self, obo: Any) -> Dict[str, Any]:
        """
        Validate the built ontology.
        
        Args:
            obo: PyOBO Obo object
            
        Returns:
            Validation report dictionary
        """
        logger.info("=== PHASE 4: VALIDATION ===")
        
        validation_report = {
            'total_terms': len(obo.terms),
            'total_typedefs': len(obo.typedefs),
            'terms_by_type': {},
            'terms_with_definitions': 0,
            'terms_with_xrefs': 0,
            'relationship_counts': {},
            'issues': []
        }
        
        # Count terms by type
        for term in obo.terms:
            term_id = term.reference.identifier
            if term_id.startswith('role_'):
                validation_report['terms_by_type']['roles'] = validation_report['terms_by_type'].get('roles', 0) + 1
            elif term_id.startswith('compound_'):
                validation_report['terms_by_type']['compounds'] = validation_report['terms_by_type'].get('compounds', 0) + 1
            elif term_id.startswith('reaction_'):
                validation_report['terms_by_type']['reactions'] = validation_report['terms_by_type'].get('reactions', 0) + 1
            elif term_id.startswith('complex_'):
                validation_report['terms_by_type']['complexes'] = validation_report['terms_by_type'].get('complexes', 0) + 1
            
            # Count terms with definitions
            if term.definition:
                validation_report['terms_with_definitions'] += 1
            
            # Count terms with cross-references
            if term.xrefs:
                validation_report['terms_with_xrefs'] += 1
            
            # Count relationships
            for annotation in term.annotations:
                rel_type = str(annotation.annotation_property)
                validation_report['relationship_counts'][rel_type] = validation_report['relationship_counts'].get(rel_type, 0) + 1
        
        # Check for potential issues
        if validation_report['terms_with_definitions'] < len(obo.terms) * 0.9:
            validation_report['issues'].append("Less than 90% of terms have definitions")
        
        if not validation_report['terms_by_type']:
            validation_report['issues'].append("No terms found by type classification")
        
        # Save validation report
        report_file = self.output_dir / "validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(validation_report, f, indent=2)
        
        logger.info("=== VALIDATION RESULTS ===")
        logger.info(f"Total terms: {validation_report['total_terms']}")
        logger.info(f"Terms by type: {validation_report['terms_by_type']}")
        logger.info(f"Terms with definitions: {validation_report['terms_with_definitions']}")
        logger.info(f"Terms with xrefs: {validation_report['terms_with_xrefs']}")
        logger.info(f"Issues found: {len(validation_report['issues'])}")
        
        for issue in validation_report['issues']:
            logger.warning(f"  - {issue}")
        
        return validation_report
    
    def build_full_pipeline(self, validate: bool = True) -> Dict[str, Any]:
        """
        Run the complete build pipeline.
        
        Args:
            validate: Whether to run validation
            
        Returns:
            Build results dictionary
        """
        logger.info("Starting SEED unified ontology build pipeline")
        
        try:
            # Extract data
            extracted_data = self.extract_data()
            
            # Build ontology
            obo = self.build_ontology()
            
            # Export formats
            self.export_formats(obo)
            
            # Validate if requested
            validation_report = None
            if validate:
                validation_report = self.validate_ontology(obo)
            
            results = {
                'success': True,
                'extracted_data_summary': {
                    'template_complexes': len(extracted_data['template'].get('complexes', {})),
                    'modelseed_compounds': len(extracted_data['modelseed'].get('compounds', {})),
                    'modelseed_reactions': len(extracted_data['modelseed'].get('reactions', {})),
                    'seed_roles': len(extracted_data['seed_roles'].get('roles', {}))
                },
                'ontology_terms': len(obo.terms),
                'ontology_typedefs': len(obo.typedefs),
                'validation_report': validation_report,
                'output_files': [
                    str(self.output_dir / "seed_unified.owl"),
                    str(self.output_dir / "seed_unified.json"),
                    str(self.output_dir / "term_mappings.json"),
                    str(self.output_dir / "validation_report.json") if validate else None
                ]
            }
            
            logger.info("=== BUILD COMPLETED SUCCESSFULLY ===")
            logger.info(f"Generated ontology with {results['ontology_terms']} terms")
            logger.info(f"Output files saved to: {self.output_dir}")
            
            return results
            
        except Exception as e:
            logger.error(f"Build pipeline failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'output_files': []
            }


def main():
    """Main entry point for the build script."""
    parser = argparse.ArgumentParser(description="Build SEED unified ontology")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Directory containing source files (default: parent directory)"
    )
    parser.add_argument(
        "--output-dir", 
        type=Path,
        default=Path(__file__).parent / "output",
        help="Output directory for generated files"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validation after building ontology"
    )
    parser.add_argument(
        "--verbose",
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Build the ontology
    builder = SEEDUnifiedBuilder(args.source_dir, args.output_dir)
    results = builder.build_full_pipeline(validate=args.validate)
    
    if results['success']:
        print("\nBuild completed successfully!")
        print(f"Generated {results['ontology_terms']} terms")
        print(f"Output files:")
        for file_path in results['output_files']:
            if file_path:
                print(f"  - {file_path}")
        
        if results.get('validation_report'):
            issues = results['validation_report'].get('issues', [])
            if issues:
                print(f"\nValidation issues found ({len(issues)}):")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print("\nValidation passed with no issues!")
        
        sys.exit(0)
    else:
        print(f"\nBuild failed: {results['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()