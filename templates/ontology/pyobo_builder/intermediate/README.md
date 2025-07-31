# Intermediate Processing Files

This directory contains intermediate files generated during the ontology build process.

## Files in this directory:

- `extraction_summary.json` - Summary of data extraction statistics
- `modelseed_data.json` - **[REGENERATED]** Extracted ModelSEED data (large file, not in git)
- `seed_roles_data.json` - **[REGENERATED]** Extracted SEED roles data (large file, not in git)  
- `template_data.json` - **[REGENERATED]** Extracted template data (large file, not in git)

## Note on Large Files

The large JSON files (`*_data.json`) are not stored in git due to size constraints (>100MB). 
These files are automatically regenerated when you run the build process.

To regenerate intermediate files:
```bash
python build_seed_unified.py
```

The build system will:
1. Extract data from the 3 source files
2. Create intermediate processing files
3. Generate the final ontology files in `output/`

## Archive Directory

The `archive/` directory contains historical versions and development files that are preserved for reference but not part of the main build process.