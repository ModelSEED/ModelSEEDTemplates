# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

ModelSEEDTemplates is a repository containing model templates used for high-throughput genome-scale metabolic model reconstruction. The templates act as "filters" by including only "modeling-ready" reactions that meet specific criteria for mass balance, charge balance, and chemical specificity.

## High-Level Architecture

### Core Components

1. **Model Templates** (`templates/`): The heart of the repository, organized by version
   - JSON files containing reactions, compounds, compartments, and biomass definitions
   - Current version: v6.0 (June 2025)
   - Previous stable: v5.0 (September 2023)
   - Legacy templates in TSV format preserved in `templates/legacy/`

2. **Biomass Formulations** (`templates/*/biomass_formulations/`): 
   - TSV files defining organism-specific biomass compositions
   - Separate formulations for Archaea, Gram-negative, and Gram-positive bacteria

3. **KBase Integration** (`WS_Specification/`):
   - Python script to fetch KBase workspace specifications
   - KBaseFBA.spec defines the data model for templates

4. **Change Tracking** (`ChangeLogs/`):
   - Version-specific change logs for each template type

### Template Structure

Each template JSON file contains:
- **biochemistry_ref**: Reference to the underlying biochemistry database
- **compartments**: Cellular compartments (e.g., cytosol, extracellular)
- **compounds**: Template-specific compound configurations
- **reactions**: Curated reactions meeting ModelSEED criteria
- **biomasses**: Organism-specific biomass objective functions

### Template Types

- **Core**: Essential metabolic reactions for bacteria
- **GramNegative**: Gram-negative bacteria-specific reactions
- **GramPositive**: Gram-positive bacteria-specific reactions  
- **Archaea**: Archaea-specific metabolic reactions

## Data Format

- Templates: JSON format following KBaseFBA specification
- Biomass formulations: TSV format
- Legacy templates: TSV format with separate files for reactions, compounds, compartments, and biomasses

## Python Development

The repository includes a Python script for KBase integration:
- Uses biokbase.workspace client library
- Connects to KBase services at https://kbase.us/services/ws
- No local build/test commands - this is primarily a data repository

## Ontology Integration

The repository is developing ontology-based versions of templates in the `templates/ontology/` directory:
- **Purpose**: Enhance templates with formal semantic annotations using ModelSEED ontology IDs
- **Benefits**: Improved interoperability, formal reasoning capabilities, and standardized identifiers
- **Tools**: ROBOT is used for OWL to JSON conversion
- **Formats**: Both OWL (compressed as .gz) and JSON-LD representations are maintained
- **Content**: Includes modelseed.owl (compounds/reactions) and seed.owl (roles/subsystems)