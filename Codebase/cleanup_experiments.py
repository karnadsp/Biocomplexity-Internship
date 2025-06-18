import os
import shutil
from datetime import datetime
from pathlib import Path
import argparse

def get_experiment_age(exp_dir):
    """Get the age of an experiment directory based on its timestamp"""
    try:
        # Try to extract timestamp from directory name
        parts = exp_dir.name.split('_')
        for i, part in enumerate(parts):
            # Look for timestamp patterns like YYYYMMDD_HHMMSS or MMDD_HHMM
            if len(part) >= 8 and part.isdigit():
                if i + 1 < len(parts) and len(parts[i + 1]) >= 4 and parts[i + 1].isdigit():
                    # Found timestamp pattern
                    timestamp_str = f"{part}_{parts[i + 1]}"
                    try:
                        if len(part) == 8:  # YYYYMMDD format
                            return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        elif len(part) == 4:  # MMDD format
                            year = datetime.now().year
                            return datetime.strptime(f"{year}{timestamp_str}", "%Y%m%d_%H%M")
                    except ValueError:
                        continue
        
        # Fallback to file modification time
        return datetime.fromtimestamp(exp_dir.stat().st_mtime)
    except:
        return datetime.fromtimestamp(exp_dir.stat().st_mtime)

def cleanup_experiments(keep_recent=5, keep_patterns=None, dry_run=False):
    """Clean up the experiments folder by archiving old experiments and keeping only recent ones
    
    Args:
        keep_recent (int): Number of most recent experiments to keep
        keep_patterns (list): List of patterns to always keep (e.g., ["batch_", "summary"])
        dry_run (bool): If True, show what would be done without actually doing it
    """
    # Handle relative path - check if we're in Codebase directory
    if Path.cwd().name == "Codebase":
        experiments_dir = Path("../experiments")
    else:
        experiments_dir = Path("experiments")
    
    if not experiments_dir.exists():
        print(f"Error: Experiments directory not found at {experiments_dir.absolute()}")
        return
    
    archive_dir = experiments_dir / "archive"
    
    # Create archive directory if it doesn't exist (only if not dry run)
    if not dry_run:
        archive_dir.mkdir(exist_ok=True)
    
    print(f"Scanning experiments directory: {experiments_dir.absolute()}")
    
    # Get all experiment directories (exclude archive and summary directories)
    experiment_dirs = []
    for d in experiments_dir.iterdir():
        if d.is_dir() and d.name != "archive":
            experiment_dirs.append(d)
    
    if not experiment_dirs:
        print("No experiment directories found.")
        return
    
    print(f"Found {len(experiment_dirs)} experiment directories")
    
    # Sort by age (most recent first)
    experiment_dirs.sort(key=get_experiment_age, reverse=True)
    
    # Determine which experiments to keep
    to_keep = []
    to_archive = []
    
    # Always keep recent experiments
    recent_experiments = experiment_dirs[:keep_recent]
    to_keep.extend(recent_experiments)
    
    # Keep experiments matching specific patterns
    if keep_patterns:
        for exp_dir in experiment_dirs:
            if any(pattern in exp_dir.name for pattern in keep_patterns):
                if exp_dir not in to_keep:
                    to_keep.append(exp_dir)
    
    # Everything else gets archived
    for exp_dir in experiment_dirs:
        if exp_dir not in to_keep:
            to_archive.append(exp_dir)
    
    # Display what will be kept and archived
    print(f"\n{'='*60}")
    print("CLEANUP PLAN")
    print(f"{'='*60}")
    
    print(f"\nWILL KEEP ({len(to_keep)} directories):")
    for exp_dir in sorted(to_keep, key=get_experiment_age, reverse=True):
        age = get_experiment_age(exp_dir)
        print(f"  ✓ {exp_dir.name} (from {age.strftime('%Y-%m-%d %H:%M')})")
    
    print(f"\nWILL ARCHIVE ({len(to_archive)} directories):")
    for exp_dir in sorted(to_archive, key=get_experiment_age, reverse=True):
        age = get_experiment_age(exp_dir)
        print(f"  → {exp_dir.name} (from {age.strftime('%Y-%m-%d %H:%M')})")
    
    if not to_archive:
        print("  (No directories to archive)")
        return
    
    # Confirm action if not dry run
    if not dry_run:
        print(f"\n{'='*60}")
        response = input(f"Archive {len(to_archive)} old experiments? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Cleanup cancelled.")
            return
    
    # Perform archiving
    if to_archive and not dry_run:
        archive_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_subdir = archive_dir / f"archive_{archive_timestamp}"
        archive_subdir.mkdir(exist_ok=True)
        
        print(f"\nArchiving {len(to_archive)} experiments to {archive_subdir.name}...")
        
        archived_count = 0
        for exp_dir in to_archive:
            try:
                # Move to archive
                destination = archive_subdir / exp_dir.name
                shutil.move(str(exp_dir), str(destination))
                print(f"  ✓ Archived: {exp_dir.name}")
                archived_count += 1
            except Exception as e:
                print(f"  ✗ Error archiving {exp_dir.name}: {str(e)}")
        
        print(f"\nArchived {archived_count}/{len(to_archive)} experiments successfully.")
    
    # Clean up any temporary files
    temp_files = list(experiments_dir.glob("*.tmp")) + list(experiments_dir.glob("*.temp"))
    if temp_files:
        print(f"\nCleaning up {len(temp_files)} temporary files...")
        for temp_file in temp_files:
            try:
                if not dry_run:
                    temp_file.unlink()
                print(f"  ✓ Removed: {temp_file.name}")
            except Exception as e:
                print(f"  ✗ Error removing {temp_file.name}: {str(e)}")
    
    print(f"\n{'='*60}")
    if dry_run:
        print("DRY RUN COMPLETE - No changes were made")
    else:
        print("CLEANUP COMPLETE!")
    print(f"Kept: {len(to_keep)} experiments")
    print(f"Archived: {len(to_archive)} experiments")
    print(f"{'='*60}")

def main():
    parser = argparse.ArgumentParser(description="Clean up experiment directories")
    parser.add_argument("--keep-recent", "-k", type=int, default=5,
                        help="Number of most recent experiments to keep (default: 5)")
    parser.add_argument("--keep-patterns", "-p", nargs="*", default=None,
                        help="Patterns to always keep (e.g., batch_ summary)")
    parser.add_argument("--dry-run", "-d", action="store_true",
                        help="Show what would be done without actually doing it")
    
    args = parser.parse_args()
    
    print("Experiment Cleanup Tool")
    print("=" * 30)
    
    cleanup_experiments(
        keep_recent=args.keep_recent,
        keep_patterns=args.keep_patterns,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main() 