#!/usr/bin/env python3
"""
Cleanup script to archive unused code files
"""

import shutil
from pathlib import Path
from datetime import datetime

def cleanup_codebase():
    """Archive unused files to keep the codebase clean"""
    
    # Create archive directory
    archive_dir = Path("archived_code")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_subdir = archive_dir / f"cleanup_{timestamp}"
    archive_subdir.mkdir(parents=True, exist_ok=True)
    
    # Files to archive (likely unused/obsolete)
    files_to_archive = [
        "analyze_experiments.py",          # Superseded by experimental_code.py
        "originalcomparer.py",             # Old comparison logic
        "comparer_ontology.py",            # Old comparison logic  
        "comparer_code.py",                # Old comparison logic
        "openai_week3_ontology.py",        # Old OpenAI version
        "openai_week3.py",                 # Old OpenAI version
        "experimental_code_openai.py",     # Old OpenAI version
        "attempt3.py",                     # Development iteration
        "create_presentation.py",          # One-time utility
        "instructions.txt",                # Likely outdated
        "batch_process_papers.py",         # Potentially superseded by batch_csv.py
        "batch_process_papers_csv.py",     # Potentially superseded by batch_csv.py
    ]
    
    # Files to keep (active/current)
    keep_files = [
        "experimental_code.py",           # Main system
        "batch_csv.py",                   # Batch processing
        "test_single_paper.py",           # Testing tool
        "cleanup_experiments.py",         # Utility tool
        "debug_csv.py",                   # Debugging tool
        "project.env",                    # Configuration
        "README.md",                      # Documentation
        ".gitignore",                     # Git configuration
    ]
    
    print("=" * 60)
    print("CODEBASE CLEANUP")
    print("=" * 60)
    
    archived_count = 0
    
    # Archive files
    for filename in files_to_archive:
        file_path = Path(filename)
        if file_path.exists():
            try:
                shutil.move(str(file_path), str(archive_subdir / filename))
                print(f"✓ Archived: {filename}")
                archived_count += 1
            except Exception as e:
                print(f"✗ Error archiving {filename}: {str(e)}")
        else:
            print(f"- Not found: {filename}")
    
    # Archive old code directory
    old_code_dir = Path("old code")
    if old_code_dir.exists():
        try:
            shutil.move(str(old_code_dir), str(archive_subdir / "old_code"))
            print(f"✓ Archived: old code/ directory")
            archived_count += 1
        except Exception as e:
            print(f"✗ Error archiving old code directory: {str(e)}")
    
    # Show what's being kept
    print(f"\n{'='*60}")
    print("KEEPING ACTIVE FILES:")
    print("=" * 60)
    
    for filename in keep_files:
        file_path = Path(filename)
        if file_path.exists():
            size = file_path.stat().st_size / 1024  # Size in KB
            print(f"✓ {filename:<30} ({size:.1f} KB)")
        else:
            print(f"- {filename:<30} (not found)")
    
    # Show archived location
    print(f"\n{'='*60}")
    print("CLEANUP SUMMARY")
    print("=" * 60)
    print(f"Archived {archived_count} files/directories")
    print(f"Archive location: {archive_subdir}")
    print(f"")
    print("To restore a file:")
    print(f"  mv {archive_subdir}/filename.py ./")
    print(f"")
    print("To permanently delete archive:")
    print(f"  rm -rf {archive_dir}")
    print("=" * 60)

if __name__ == "__main__":
    cleanup_codebase() 