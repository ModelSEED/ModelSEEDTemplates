#!/usr/bin/env python3
"""
Complete SEED Ontology Workflow

Runs the complete workflow to build, validate, and generate all formats
of the SEED Unified Ontology.

Usage:
    python run_complete_workflow.py
"""

import subprocess
import sys
import os
import time


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    print(f"   Command: {command}")
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    duration = time.time() - start_time
    
    if result.returncode == 0:
        print(f"   ✅ Completed in {duration:.1f}s")
        if result.stdout:
            # Show last few lines of output
            lines = result.stdout.strip().split('\n')
            for line in lines[-3:]:
                print(f"   {line}")
    else:
        print(f"   ❌ Failed after {duration:.1f}s")
        print(f"   Error: {result.stderr}")
        return False
    
    return True


def main():
    """Run complete workflow"""
    print("🚀 SEED Unified Ontology - Complete Workflow")
    print("=" * 60)
    
    workflow_start = time.time()
    
    # Step 1: Build ontology
    if not run_command("python build_seed_ontology_v2.py", "Building SEED Unified Ontology"):
        print("💥 Workflow failed at build step")
        sys.exit(1)
    
    # Step 2: Validate ontology
    if not run_command("python validate_ontology.py", "Validating ontology completeness"):
        print("💥 Workflow failed at validation step")
        sys.exit(1)
    
    # Step 3: Generate OBO format
    if not run_command("python generate_obo.py", "Generating OBO format"):
        print("💥 Workflow failed at OBO generation step")
        sys.exit(1)
    
    # Show final results
    total_duration = time.time() - workflow_start
    
    print(f"\n🎉 Complete workflow finished in {total_duration:.1f}s")
    print("=" * 60)
    
    # Show output files
    if os.path.exists("output"):
        print(f"\n📁 Generated files:")
        for filename in sorted(os.listdir("output")):
            filepath = os.path.join("output", filename)
            if os.path.isfile(filepath):
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                if size_mb >= 1:
                    print(f"   {filename}: {size_mb:.1f} MB")
                else:
                    size_kb = os.path.getsize(filepath) / 1024
                    print(f"   {filename}: {size_kb:.1f} KB")
    
    print(f"\n✨ SEED Unified Ontology is ready for use!")
    print(f"   📖 See README.md for usage examples")
    print(f"   🔧 Use seed_unified.owl for complete functionality")
    print(f"   ⚡ Use with semsql, ROBOT, Protégé, or custom tools")


if __name__ == "__main__":
    main()