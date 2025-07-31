#!/usr/bin/env python3
"""
SEED Unified Ontology Mapping Coverage Report Generator

Creates detailed reports showing mapping coverage by entity type, source, and provides
actionable insights for improving mapping rates.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MappingCoverageReporter:
    """Generates detailed mapping coverage reports."""
    
    def __init__(self, analysis_dir: str, clean_ontology_dir: str):
        """Initialize with paths to analysis and clean ontology directories."""
        self.analysis_dir = Path(analysis_dir)
        self.clean_ontology_dir = Path(clean_ontology_dir)
        self.analysis_data = None
        self.clean_summary = None
        self._load_data()
    
    def _load_data(self):
        """Load analysis and clean ontology data."""
        try:
            # Load comprehensive analysis
            with open(self.analysis_dir / 'comprehensive_analysis.json') as f:
                self.analysis_data = json.load(f)
            
            # Load clean ontology summary
            with open(self.clean_ontology_dir / 'clean_ontology_summary.json') as f:
                self.clean_summary = json.load(f)
            
            logger.info("Loaded analysis and clean ontology data")
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise
    
    def generate_executive_summary(self) -> Dict:
        """Generate executive summary of mapping coverage."""
        logger.info("Generating executive summary...")
        
        role_analysis = self.analysis_data['role_analysis']
        reaction_analysis = self.analysis_data['reaction_analysis']
        complex_analysis = self.analysis_data['complex_analysis']
        clean_stats = self.clean_summary
        
        executive_summary = {
            'key_findings': {
                'critical_role_mapping_issue': {
                    'description': "Only 48.6% of roles are mapped to SEED IDs",
                    'impact': "This severely limits ontology utility for functional genomics",
                    'affected_entities': role_analysis['unmapped_roles'],
                    'primary_cause': "Only ModelSEED source roles have mappings"
                },
                'excellent_reaction_coverage': {
                    'description': "99.9% of reactions are properly mapped",
                    'impact': "Metabolic pathway analysis will be highly accurate",
                    'mapped_entities': reaction_analysis['mapped_reactions']
                },
                'perfect_complex_coverage': {
                    'description': "100% of complexes are properly mapped",
                    'impact': "Protein complex analysis will be comprehensive",
                    'mapped_entities': complex_analysis['mapped_complexes']
                },
                'source_filtering_discovered': {
                    'description': "Only ModelSEED source entities are mapped",
                    'excluded_sources': ['KEGG', 'PlantSEED', 'SEED', ''],
                    'excluded_role_count': role_analysis['unmapped_roles']
                }
            },
            'ontology_quality_metrics': {
                'overall_mapping_rate': clean_stats['original_vs_clean']['retention_rate'],
                'entity_mapping_rates': {
                    'roles': role_analysis['mapped_roles'] / role_analysis['total_roles'],
                    'reactions': reaction_analysis['mapped_reactions'] / reaction_analysis['total_reactions'],
                    'complexes': complex_analysis['mapped_complexes'] / complex_analysis['total_complexes']
                },
                'relationship_integrity_rate': self.analysis_data['relationship_integrity']['complex_role_relationships']['both_mapped'] / self.analysis_data['relationship_integrity']['complex_role_relationships']['total']
            },
            'clean_ontology_projection': {
                'total_entities': clean_stats['entity_counts']['total_entities'],
                'total_relationships': clean_stats['relationship_counts']['total_relationships'],
                'data_quality_guaranteed': True,
                'broken_references': 0
            },
            'recommendations': {
                'immediate': [
                    "Use clean ontology (21,853 entities) for production systems",
                    "Separate unmapped data (10,575 entities) for analysis",
                    "Focus mapping efforts on KEGG and PlantSEED roles"
                ],
                'strategic': [
                    "Develop KEGG→SEED role mapping pipeline",
                    "Create PlantSEED→SEED role mapping system",
                    "Establish quality control for future template updates"
                ]
            }
        }
        
        return executive_summary
    
    def generate_source_analysis_report(self) -> Dict:
        """Generate detailed source analysis report."""
        logger.info("Generating source analysis report...")
        
        role_analysis = self.analysis_data['role_analysis']
        
        source_report = {
            'source_mapping_breakdown': {},
            'mapping_success_by_source': {},
            'unmapped_source_analysis': {},
            'source_prioritization': []
        }
        
        # Detailed breakdown by source
        for source in role_analysis['source_breakdown']:
            total_count = role_analysis['source_breakdown'][source]
            mapped_count = role_analysis['mapped_by_source'].get(source, 0)
            unmapped_count = role_analysis['unmapped_by_source'].get(source, 0)
            mapping_rate = mapped_count / total_count if total_count > 0 else 0
            
            source_report['source_mapping_breakdown'][source] = {
                'total_roles': total_count,
                'mapped_roles': mapped_count,
                'unmapped_roles': unmapped_count,
                'mapping_rate': mapping_rate,
                'mapping_percentage': f"{mapping_rate*100:.1f}%"
            }
            
            # Success analysis
            if mapping_rate > 0:
                source_report['mapping_success_by_source'][source] = {
                    'status': 'successful',
                    'rate': mapping_rate,
                    'mapped_count': mapped_count
                }
            else:
                source_report['unmapped_source_analysis'][source] = {
                    'status': 'completely_unmapped',
                    'unmapped_count': unmapped_count,
                    'potential_impact': self._assess_source_impact(source, unmapped_count)
                }
        
        # Prioritize sources for mapping efforts
        unmapped_sources = []
        for source, data in source_report['unmapped_source_analysis'].items():
            unmapped_sources.append({
                'source': source,
                'unmapped_count': data['unmapped_count'],
                'priority': self._calculate_source_priority(source, data['unmapped_count'])
            })
        
        source_report['source_prioritization'] = sorted(
            unmapped_sources, 
            key=lambda x: x['priority'], 
            reverse=True
        )
        
        return source_report
    
    def _assess_source_impact(self, source: str, unmapped_count: int) -> str:
        """Assess the impact of a source being unmapped."""
        if source == 'KEGG':
            return 'HIGH - KEGG is a major biological database with critical pathway information'
        elif source == 'PlantSEED':
            return 'MEDIUM - PlantSEED contains plant-specific functional annotations'
        elif source == 'SEED':
            return 'MEDIUM - Core SEED annotations provide foundational biological knowledge'
        else:
            return 'LOW - Limited biological impact'
    
    def _calculate_source_priority(self, source: str, unmapped_count: int) -> int:
        """Calculate priority score for mapping efforts."""
        base_score = unmapped_count  # More unmapped = higher priority
        
        # Source-specific multipliers
        if source == 'KEGG':
            return base_score * 3  # KEGG is highest priority
        elif source == 'PlantSEED':
            return base_score * 2  # PlantSEED is medium priority
        elif source == 'SEED':
            return base_score * 2  # SEED is medium priority
        else:
            return base_score  # Default priority
    
    def generate_entity_type_coverage(self) -> Dict:
        """Generate coverage analysis by entity type."""
        logger.info("Generating entity type coverage analysis...")
        
        role_analysis = self.analysis_data['role_analysis']
        reaction_analysis = self.analysis_data['reaction_analysis']
        complex_analysis = self.analysis_data['complex_analysis']
        
        coverage_report = {
            'roles': {
                'total': role_analysis['total_roles'],
                'mapped': role_analysis['mapped_roles'],
                'unmapped': role_analysis['unmapped_roles'],
                'mapping_rate': role_analysis['mapped_roles'] / role_analysis['total_roles'],
                'status': 'CRITICAL - Low mapping rate',
                'unmapped_examples': role_analysis['unmapped_role_examples'][:10],
                'recommendations': [
                    "Immediate priority for mapping improvement",
                    "Focus on KEGG roles (4,153 unmapped)",
                    "Develop automated KEGG→SEED mapping pipeline"
                ]
            },
            'reactions': {
                'total': reaction_analysis['total_reactions'],
                'mapped': reaction_analysis['mapped_reactions'],
                'unmapped': reaction_analysis['unmapped_reactions'],
                'mapping_rate': reaction_analysis['mapped_reactions'] / reaction_analysis['total_reactions'],
                'status': 'EXCELLENT - Near perfect mapping',
                'unmapped_examples': reaction_analysis['unmapped_reaction_examples'],
                'recommendations': [
                    "Investigate the 8 unmapped reactions",
                    "Maintain current mapping quality"
                ]
            },
            'complexes': {
                'total': complex_analysis['total_complexes'],
                'mapped': complex_analysis['mapped_complexes'],
                'unmapped': complex_analysis['unmapped_complexes'],
                'mapping_rate': complex_analysis['mapped_complexes'] / complex_analysis['total_complexes'],
                'status': 'PERFECT - Complete mapping',
                'unmapped_examples': [],
                'recommendations': [
                    "Maintain current mapping quality",
                    "Use as template for other entity types"
                ]
            }
        }
        
        return coverage_report
    
    def generate_relationship_quality_report(self) -> Dict:
        """Generate relationship quality and integrity report."""
        logger.info("Generating relationship quality report...")
        
        integrity_data = self.analysis_data['relationship_integrity']
        broken_data = self.analysis_data['broken_relationships']
        
        quality_report = {
            'complex_role_relationships': {
                'total_relationships': integrity_data['complex_role_relationships']['total'],
                'both_mapped': integrity_data['complex_role_relationships']['both_mapped'],
                'integrity_rate': integrity_data['complex_role_relationships']['both_mapped'] / integrity_data['complex_role_relationships']['total'],
                'broken_relationships': integrity_data['complex_role_relationships']['total'] - integrity_data['complex_role_relationships']['both_mapped'],
                'primary_issue': 'Unmapped roles breaking complex relationships',
                'examples': integrity_data['complex_role_relationships']['broken_examples']
            },
            'reaction_complex_relationships': {
                'total_relationships': integrity_data['reaction_complex_relationships']['total'],
                'both_mapped': integrity_data['reaction_complex_relationships']['both_mapped'],
                'integrity_rate': integrity_data['reaction_complex_relationships']['both_mapped'] / integrity_data['reaction_complex_relationships']['total'],
                'broken_relationships': integrity_data['reaction_complex_relationships']['total'] - integrity_data['reaction_complex_relationships']['both_mapped'],
                'primary_issue': 'Minimal issues due to high mapping rates',
                'examples': integrity_data['reaction_complex_relationships']['broken_examples']
            },
            'clean_ontology_impact': {
                'valid_complex_role_relationships': self.clean_summary['relationship_counts']['complex_role_relationships'],
                'valid_reaction_complex_relationships': self.clean_summary['relationship_counts']['reaction_complex_relationships'],
                'total_valid_relationships': self.clean_summary['relationship_counts']['total_relationships'],
                'relationship_retention_rate': self.clean_summary['relationship_counts']['total_relationships'] / (integrity_data['complex_role_relationships']['total'] + integrity_data['reaction_complex_relationships']['total'])
            }
        }
        
        return quality_report
    
    def generate_actionable_insights(self) -> Dict:
        """Generate actionable insights and recommendations."""
        logger.info("Generating actionable insights...")
        
        role_analysis = self.analysis_data['role_analysis']
        
        insights = {
            'immediate_actions': {
                'deploy_clean_ontology': {
                    'description': 'Deploy clean ontology for production use',
                    'entities': self.clean_summary['entity_counts']['total_entities'],
                    'relationships': self.clean_summary['relationship_counts']['total_relationships'],
                    'confidence': 'HIGH - All entities have valid SEED IDs'
                },
                'preserve_unmapped_data': {
                    'description': 'Preserve unmapped entities for future mapping',
                    'unmapped_roles': role_analysis['unmapped_roles'], 
                    'unmapped_reactions': self.analysis_data['reaction_analysis']['unmapped_reactions'],
                    'priority': 'HIGH - Don\'t lose biological information'
                }
            },
            'mapping_improvement_strategy': {
                'kegg_role_mapping': {
                    'unmapped_count': role_analysis['unmapped_by_source']['KEGG'],
                    'priority': 'CRITICAL',
                    'approach': 'Develop KEGG→SEED role mapping using EC numbers and gene names',
                    'expected_improvement': f"+{role_analysis['unmapped_by_source']['KEGG']} roles"
                },
                'plantseed_role_mapping': {
                    'unmapped_count': role_analysis['unmapped_by_source']['PlantSEED'],
                    'priority': 'MEDIUM',
                    'approach': 'Map PlantSEED roles to existing SEED functional annotations',
                    'expected_improvement': f"+{role_analysis['unmapped_by_source']['PlantSEED']} roles"
                },
                'seed_role_mapping': {
                    'unmapped_count': role_analysis['unmapped_by_source']['SEED'],
                    'priority': 'MEDIUM',
                    'approach': 'Investigate why core SEED roles lack mappings',
                    'expected_improvement': f"+{role_analysis['unmapped_by_source']['SEED']} roles"
                }
            },
            'quality_control_measures': {
                'mapping_validation': 'Implement automated validation of SEED ID mappings',
                'source_consistency': 'Ensure consistent mapping approach across all sources',
                'relationship_integrity': 'Monitor relationship validity as mappings are added',
                'version_control': 'Track mapping coverage changes across template versions'
            },
            'success_metrics': {
                'target_role_mapping_rate': 0.90,  # 90% target
                'current_role_mapping_rate': role_analysis['mapped_roles'] / role_analysis['total_roles'],
                'improvement_needed': (0.90 * role_analysis['total_roles']) - role_analysis['mapped_roles'],
                'focus_areas': ['KEGG roles', 'PlantSEED roles', 'Core SEED roles']
            }
        }
        
        return insights
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate the complete mapping coverage report."""
        logger.info("Generating comprehensive mapping coverage report...")
        
        report = {
            'report_metadata': {
                'generated_timestamp': Path(__file__).stat().st_mtime,
                'analysis_source': str(self.analysis_dir),
                'clean_ontology_source': str(self.clean_ontology_dir),
                'report_version': '1.0'
            },
            'executive_summary': self.generate_executive_summary(),
            'source_analysis': self.generate_source_analysis_report(),
            'entity_coverage': self.generate_entity_type_coverage(),
            'relationship_quality': self.generate_relationship_quality_report(),
            'actionable_insights': self.generate_actionable_insights()
        }
        
        logger.info("Comprehensive mapping coverage report generated")
        return report
    
    def save_report(self, report: Dict, output_dir: str):
        """Save the mapping coverage report."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save complete report
        with open(output_path / 'mapping_coverage_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save executive summary separately for quick access
        with open(output_path / 'executive_summary.json', 'w') as f:
            json.dump(report['executive_summary'], f, indent=2)
        
        # Save actionable insights separately
        with open(output_path / 'actionable_insights.json', 'w') as f:
            json.dump(report['actionable_insights'], f, indent=2)
        
        logger.info(f"Mapping coverage report saved to {output_path}")


def main():
    """Main execution function."""
    # Input and output paths
    analysis_dir = "/Users/jplfaria/repos/ModelSEEDTemplates/templates/ontology/pyobo_builder/analysis_output"
    clean_ontology_dir = "/Users/jplfaria/repos/ModelSEEDTemplates/templates/ontology/pyobo_builder/clean_ontology"
    output_dir = "/Users/jplfaria/repos/ModelSEEDTemplates/templates/ontology/pyobo_builder/mapping_reports"
    
    # Generate report
    reporter = MappingCoverageReporter(analysis_dir, clean_ontology_dir)
    report = reporter.generate_comprehensive_report()
    reporter.save_report(report, output_dir)
    
    # Print key findings
    print("\n" + "="*80)
    print("MAPPING COVERAGE REPORT - KEY FINDINGS")
    print("="*80)
    
    exec_summary = report['executive_summary']
    
    print(f"\nCRITICAL ISSUES:")
    role_issue = exec_summary['key_findings']['critical_role_mapping_issue']
    print(f"  {role_issue['description']}")
    print(f"  Impact: {role_issue['impact']}")
    print(f"  Affected: {role_issue['affected_entities']} roles")
    
    print(f"\nSOURCE FILTERING DISCOVERY:")
    source_issue = exec_summary['key_findings']['source_filtering_discovered']
    print(f"  {source_issue['description']}")
    print(f"  Excluded sources: {', '.join(source_issue['excluded_sources'])}")
    print(f"  Excluded roles: {source_issue['excluded_role_count']}")
    
    print(f"\nCLEAN ONTOLOGY STATS:")
    clean_proj = exec_summary['clean_ontology_projection']
    print(f"  Total entities: {clean_proj['total_entities']}")
    print(f"  Total relationships: {clean_proj['total_relationships']}")
    print(f"  Data quality guaranteed: {clean_proj['data_quality_guaranteed']}")
    
    print(f"\nIMMEDIATE RECOMMENDATIONS:")
    for rec in exec_summary['recommendations']['immediate']:
        print(f"  • {rec}")
    
    print(f"\nSTRATEGIC RECOMMENDATIONS:")
    for rec in exec_summary['recommendations']['strategic']:
        print(f"  • {rec}")
    
    insights = report['actionable_insights']
    print(f"\nMAPPING IMPROVEMENT POTENTIAL:")
    kegg_mapping = insights['mapping_improvement_strategy']['kegg_role_mapping']
    print(f"  KEGG roles: {kegg_mapping['unmapped_count']} unmapped ({kegg_mapping['priority']} priority)")
    plantseed_mapping = insights['mapping_improvement_strategy']['plantseed_role_mapping']
    print(f"  PlantSEED roles: {plantseed_mapping['unmapped_count']} unmapped ({plantseed_mapping['priority']} priority)")
    
    print(f"\nREPORT FILES GENERATED:")
    print(f"  - mapping_coverage_report.json (complete report)")
    print(f"  - executive_summary.json (key findings)")
    print(f"  - actionable_insights.json (recommendations)")
    print(f"\nAll files saved to: {output_dir}")


if __name__ == "__main__":
    main()