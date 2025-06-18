import json
import os
from pathlib import Path
import difflib
from collections import Counter
import re
from typing import Dict, List, Tuple, Optional
import statistics
import argparse
import fnmatch

def extract_ontology_terms(text: str) -> Dict[str, List[str]]:
    """Extract ontology terms from the presentation text."""
    # Initialize categories
    categories = {
        'CellOntology': [],
        'GeneOntology': [],
        'MeSH': [],
        'Other': []
    }
    
    # Extract terms based on patterns
    current_category = None
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Check for category headers
        if line.endswith(':'):
            current_category = line[:-1]
            continue
            
        # Extract terms from lines starting with '-'
        if line.startswith('-'):
            term = line[1:].strip()
            # Extract ID if present
            id_match = re.search(r'\(ID: ([^)]+)\)', term)
            if id_match:
                term = term[:id_match.start()].strip()
            
            # Categorize the term
            if current_category in categories:
                categories[current_category].append(term)
            else:
                categories['Other'].append(term)
    
    return categories

def calculate_code_similarity(code1: str, code2: str) -> float:
    """Calculate similarity between two code snippets using difflib."""
    matcher = difflib.SequenceMatcher(None, code1, code2)
    return matcher.ratio()

def calculate_ontology_similarity(terms1: Dict[str, List[str]], terms2: Dict[str, List[str]]) -> Dict[str, float]:
    """Calculate similarity between ontology terms using Jaccard similarity."""
    similarities = {}
    
    for category in terms1.keys():
        set1 = set(terms1[category])
        set2 = set(terms2[category])
        
        if not set1 and not set2:
            similarity = 1.0  # Both empty sets are considered identical
        elif not set1 or not set2:
            similarity = 0.0  # One empty set means no similarity
        else:
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            similarity = intersection / union if union > 0 else 0.0
            
        similarities[category] = similarity
    
    return similarities

def analyze_experiment_runs(summary_dir: Path, run_dirs: Optional[list] = None) -> dict:
    """Analyze the results of multiple experiment runs."""
    results = {
        'code_similarities': [],
        'ontology_similarities': [],
        'run_details': []
    }
    if run_dirs is None:
        # Get all run directories (only those with '_run' in their name)
        run_dirs = [d for d in summary_dir.parent.iterdir() if d.is_dir() and '_run' in d.name]
        run_dirs.sort(key=lambda x: int(x.name.split('_run')[1]))
    else:
        run_dirs.sort(key=lambda x: int(x.name.split('_run')[1]))
    
    # Extract code and ontology data from each run
    run_data = []
    for run_dir in run_dirs:
        run_number = int(run_dir.name.split('_run')[1])
        
        # Read CC3D code
        code_file = run_dir / "presentation_ready_ontology_to_code.txt"
        if code_file.exists():
            with open(code_file, 'r') as f:
                code_content = f.read()
                # Extract code section
                code_match = re.search(r'Generated CC3D Code:(.*?)(?=\n\n|$)', code_content, re.DOTALL)
                code = code_match.group(1).strip() if code_match else ""
        else:
            code = ""
            
        # Read ontology annotations
        ontology_file = run_dir / "presentation_ready_abstract_to_ontology.txt"
        if ontology_file.exists():
            with open(ontology_file, 'r') as f:
                ontology_content = f.read()
                ontology_terms = extract_ontology_terms(ontology_content)
        else:
            ontology_terms = {k: [] for k in ['CellOntology', 'GeneOntology', 'MeSH', 'Other']}
            
        run_data.append({
            'run_number': run_number,
            'code': code,
            'ontology_terms': ontology_terms
        })
    
    # Calculate similarities between runs
    for i in range(len(run_data)):
        for j in range(i + 1, len(run_data)):
            # Code similarity
            code_sim = calculate_code_similarity(run_data[i]['code'], run_data[j]['code'])
            results['code_similarities'].append({
                'run1': run_data[i]['run_number'],
                'run2': run_data[j]['run_number'],
                'similarity': code_sim
            })
            
            # Ontology similarity
            ontology_sim = calculate_ontology_similarity(
                run_data[i]['ontology_terms'],
                run_data[j]['ontology_terms']
            )
            results['ontology_similarities'].append({
                'run1': run_data[i]['run_number'],
                'run2': run_data[j]['run_number'],
                'similarities': ontology_sim
            })
    
    # Calculate statistics
    if results['code_similarities']:
        code_sims = [s['similarity'] for s in results['code_similarities']]
        results['code_statistics'] = {
            'mean': statistics.mean(code_sims),
            'median': statistics.median(code_sims),
            'stdev': statistics.stdev(code_sims) if len(code_sims) > 1 else 0
        }
    
    # Calculate ontology statistics
    ontology_stats = {}
    for category in ['CellOntology', 'GeneOntology', 'MeSH', 'Other']:
        sims = [s['similarities'][category] for s in results['ontology_similarities']]
        if sims:
            ontology_stats[category] = {
                'mean': statistics.mean(sims),
                'median': statistics.median(sims),
                'stdev': statistics.stdev(sims) if len(sims) > 1 else 0
            }
    results['ontology_statistics'] = ontology_stats
    
    return results

def generate_report(analysis_results: Dict, output_file: Path):
    """Generate a human-readable report from the analysis results."""
    with open(output_file, 'w') as f:
        f.write("Experiment Analysis Report\n")
        f.write("=" * 50 + "\n\n")
        
        # Code similarity section
        f.write("Code Similarity Analysis\n")
        f.write("-" * 30 + "\n")
        if 'code_statistics' in analysis_results:
            stats = analysis_results['code_statistics']
            f.write(f"Mean similarity: {stats['mean']:.3f}\n")
            f.write(f"Median similarity: {stats['median']:.3f}\n")
            f.write(f"Standard deviation: {stats['stdev']:.3f}\n\n")
        
        f.write("Pairwise Code Similarities:\n")
        for sim in analysis_results['code_similarities']:
            f.write(f"Runs {sim['run1']} vs {sim['run2']}: {sim['similarity']:.3f}\n")
        f.write("\n")
        
        # Ontology similarity section
        f.write("Ontology Similarity Analysis\n")
        f.write("-" * 30 + "\n")
        if 'ontology_statistics' in analysis_results:
            stats = analysis_results['ontology_statistics']
            for category, cat_stats in stats.items():
                f.write(f"\n{category}:\n")
                f.write(f"  Mean similarity: {cat_stats['mean']:.3f}\n")
                f.write(f"  Median similarity: {cat_stats['median']:.3f}\n")
                f.write(f"  Standard deviation: {cat_stats['stdev']:.3f}\n")
        
        f.write("\nPairwise Ontology Similarities:\n")
        for sim in analysis_results['ontology_similarities']:
            f.write(f"\nRuns {sim['run1']} vs {sim['run2']}:\n")
            for category, similarity in sim['similarities'].items():
                f.write(f"  {category}: {similarity:.3f}\n")

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Analyze experiment results')
    parser.add_argument('--summary-dir', type=str, help='Path to the experiment summary directory')
    args = parser.parse_args()
    
    summary_dir = None
    if args.summary_dir:
        summary_dir = Path(args.summary_dir)
        if not summary_dir.exists():
            print(f"Error: Summary directory '{summary_dir}' does not exist!")
            return
    else:
        # List only summary directories for selection (any with '_summary' in the name)
        experiments_dir = Path("experiments")
        if not experiments_dir.exists():
            print("No experiments directory found!")
            return
        summary_dirs = [d for d in experiments_dir.iterdir() if d.is_dir() and '_summary' in d.name]
        if not summary_dirs:
            print("No experiment summaries found!")
            return
        print("Available experiment summary directories:")
        for idx, d in enumerate(summary_dirs, 1):
            print(f"  {idx}. {d}")
        print("  0. Enter a custom path")
        try:
            choice = int(input("Select a summary directory by number (or 0 to enter a path): "))
        except ValueError:
            print("Invalid input. Exiting.")
            return
        if choice == 0:
            custom_path = input("Enter the path to the summary directory: ").strip()
            summary_dir = Path(custom_path)
            if not summary_dir.exists():
                print(f"Error: Summary directory '{summary_dir}' does not exist!")
                return
        elif 1 <= choice <= len(summary_dirs):
            summary_dir = summary_dirs[choice - 1]
        else:
            print("Invalid selection. Exiting.")
            return
    
    print(f"Analyzing experiment results from: {summary_dir}")
    
    # Only analyze run directories that match the summary prefix and '_run' pattern
    summary_prefix = re.sub(r'_summary.*$', '', summary_dir.name)
    run_dirs = [d for d in summary_dir.parent.iterdir() if d.is_dir() and d.name.startswith(summary_prefix) and '_run' in d.name]
    if not run_dirs:
        print(f"No valid run directories found for summary '{summary_dir.name}'.")
        return
    
    # Patch analyze_experiment_runs to accept run_dirs
    analysis_results = analyze_experiment_runs(summary_dir, run_dirs)
    
    # Generate report
    report_file = summary_dir / "analysis_report.txt"
    generate_report(analysis_results, report_file)
    
    print(f"\nAnalysis complete! Report saved to: {report_file}")

if __name__ == "__main__":
    main() 