#!/usr/bin/env python3
"""
Test script to run a single paper from the CSV batch for testing purposes
"""

import csv
import sys
from pathlib import Path

# Import the batch processing functions
from batch_csv import load_abstracts_csv, get_experiment_name_from_title, batch_process_to_csv
from experimental_code import run_experiment, analyze_run_consistency, format_consistency_analysis, generate_detailed_summary

def test_first_paper(csv_file="week4papers.csv", num_runs=3):
    """Test the first paper from the CSV file"""
    
    print("=" * 60)
    print("SINGLE PAPER TEST")
    print("=" * 60)
    
    # Load the CSV
    try:
        abstracts = load_abstracts_csv(csv_file)
        if not abstracts:
            print(f"Error: No papers found in {csv_file}")
            return
        
        print(f"Loaded {len(abstracts)} papers from CSV")
        
        # Get the first paper
        paper = abstracts[0]
        print(f"\nTesting with first paper:")
        print(f"Title: {paper['name'][:80]}...")
        print(f"Abstract length: {len(paper['abstract'])} characters")
        
        # Generate experiment name
        experiment_name = get_experiment_name_from_title(paper['name'], 1)
        print(f"Experiment name: {experiment_name}")
        
        # Ask for confirmation
        response = input(f"\nProceed with {num_runs} runs? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Test cancelled.")
            return
        
        print(f"\n{'='*60}")
        print(f"RUNNING {num_runs} EXPERIMENTS")
        print(f"{'='*60}")
        
        # Run the experiments
        paper_dirs = []
        for run in range(1, num_runs + 1):
            print(f"\nRun {run}/{num_runs}:")
            experiment_dir = run_experiment(experiment_name, paper['abstract'], run, num_runs)
            paper_dirs.append(experiment_dir)
            print(f"Completed run {run}")
        
        print(f"\n{'='*60}")
        print("GENERATING ANALYSIS")
        print(f"{'='*60}")
        
        # Get main experiment directory from first run
        main_experiment_dir = paper_dirs[0].parent
        
        # Generate ontology comparison
        from experimental_code import generate_ontology_comparison
        ontology_comparison = generate_ontology_comparison(paper_dirs)
        with open(main_experiment_dir / "ontology_comparison.txt", 'w', encoding='utf-8') as f:
            f.write(ontology_comparison)
        
        # Generate detailed summary
        detailed_summary = generate_detailed_summary(paper_dirs, experiment_name, paper['abstract'])
        with open(main_experiment_dir / "experiment_summary.txt", 'w', encoding='utf-8') as f:
            f.write(detailed_summary)
        
        # Analyze consistency
        consistency_metrics = analyze_run_consistency(paper_dirs)
        consistency_analysis = format_consistency_analysis(consistency_metrics)
        with open(main_experiment_dir / "consistency_analysis.txt", 'w', encoding='utf-8') as f:
            f.write(consistency_analysis)
        
        print(f"\n{'='*60}")
        print("TEST COMPLETED SUCCESSFULLY!")
        print(f"{'='*60}")
        print(f"Experiment structure:")
        print(f"  Main directory: {main_experiment_dir}")
        print(f"  Run directories: {len(paper_dirs)} subdirectories")
        print(f"")
        print("Generated files:")
        print(f"  • ontology_comparison.txt - Side-by-side ontology comparison")
        print(f"  • experiment_summary.txt - Detailed run information")
        print(f"  • consistency_analysis.txt - Pipeline consistency analysis")
        print(f"  • run_X/experiment_data.json - Comprehensive data per run")
        print(f"  • run_X/generated_cc3d_model.cc3d - Generated models")
        print(f"{'='*60}")
        
        # Quick preview of results
        print(f"\nQUICK PREVIEW:")
        print(f"Paper: {paper['name'][:60]}...")
        print(f"Runs completed: {len(paper_dirs)}")
        
        # Show some basic consistency metrics
        if consistency_metrics:
            for stage_key, stage_data in consistency_metrics.items():
                if 'ontology_consistency' in stage_data:
                    for category, terms in stage_data['ontology_consistency'].items():
                        if terms:
                            avg_consistency = sum(terms.values()) / len(terms.values())
                            print(f"{category} avg consistency: {avg_consistency:.1%}")
                
                if 'code_similarity' in stage_data and stage_data['code_similarity']:
                    similarities = [pair['similarity'] for pair in stage_data['code_similarity']]
                    avg_similarity = sum(similarities) / len(similarities)
                    print(f"Code similarity: {avg_similarity:.1%}")
        
        return summary_dir
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Parse command line arguments
    csv_file = "week4papers.csv"
    num_runs = 3
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    if len(sys.argv) > 2:
        num_runs = int(sys.argv[2])
    
    test_first_paper(csv_file, num_runs) 