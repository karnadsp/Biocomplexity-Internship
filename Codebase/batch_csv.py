#!/usr/bin/env python3

import os
import json
import csv
import statistics
from pathlib import Path
from datetime import datetime
from experimental_code import (
    run_experiment, analyze_run_consistency, format_consistency_analysis,
    generate_detailed_summary, generate_ontology_comparison,
    extract_ontologies_from_response, extract_code_from_response, calculate_similarity
)

def load_abstracts_csv(csv_file):
    """Load paper abstracts from a CSV file"""
    abstracts = []
    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)  # Use csv.reader instead of DictReader
        for i, row in enumerate(reader):
            if len(row) >= 2:
                title = row[0].strip()  # First column is paper name
                abstract = row[1].strip()  # Second column is abstract
                
                abstracts.append({
                    'name': title,
                    'abstract': abstract
                })
            else:
                print(f"Warning: Row {i+1} doesn't have enough columns, skipping")
    return abstracts

def get_experiment_name_from_title(title, paper_id):
    """Get experiment name from first two words of paper title"""
    words = title.split()
    if len(words) >= 2:
        # Take first two words and clean them for filename
        first_two = "_".join(words[:2])
        # Remove special characters that might cause issues in filenames
        clean_name = "".join(c for c in first_two if c.isalnum() or c in "._-").replace(" ", "_")
        return f"paper_{paper_id:02d}_{clean_name}"
    else:
        # Fallback if title has less than 2 words
        clean_name = "".join(c for c in title if c.isalnum() or c in "._-").replace(" ", "_")[:20]
        return f"paper_{paper_id:02d}_{clean_name}"

def run_full_experiment_workflow(experiment_name, description, num_runs, batch_timestamp, batch_dir=None, model_type="reasoning"):
    """
    Run the complete experimental_code.py workflow for a single paper.
    This generates all the rich outputs (ontology_comparison.txt, consistency_analysis.txt, etc.)
    and returns the experiment directories and main directory.
    """
    print(f"Running full experimental workflow for: {experiment_name} using {model_type} model")
    
    # Run multiple experiments (same as experimental_code.py main())
    experiment_dirs = []
    main_experiment_dir = None
    
    for run in range(1, num_runs + 1):
        print(f"  Running experiment {run} of {num_runs}...")
        run_dir = run_experiment(experiment_name, description, run, num_runs, batch_timestamp, batch_dir, model_type)
        experiment_dirs.append(run_dir)
        
        # Get the main experiment directory from the first run
        if main_experiment_dir is None:
            main_experiment_dir = run_dir.parent
        
        print(f"  Completed run {run}. Results saved in {run_dir}")
    
    print(f"Generating comprehensive analysis for {experiment_name}...")
    
    # Generate ontology comparison
    ontology_comparison = generate_ontology_comparison(experiment_dirs)
    with open(main_experiment_dir / "ontology_comparison.txt", 'w', encoding='utf-8') as f:
        f.write(ontology_comparison)
    
    # Generate detailed experiment summary
    detailed_summary = generate_detailed_summary(experiment_dirs, experiment_name, description)
    with open(main_experiment_dir / "experiment_summary.txt", 'w', encoding='utf-8') as f:
        f.write(detailed_summary)
    
    # Perform and save consistency analysis
    consistency_metrics = analyze_run_consistency(experiment_dirs)
    consistency_analysis = format_consistency_analysis(consistency_metrics)
    with open(main_experiment_dir / "consistency_analysis.txt", 'w', encoding='utf-8') as f:
        f.write(consistency_analysis)
    
    print(f"Full workflow completed for {experiment_name} using {model_type} model")
    print(f"Results saved in: {main_experiment_dir}")
    
    return experiment_dirs, main_experiment_dir, consistency_metrics

def extract_metrics_from_consistency_data(consistency_metrics, experiment_dirs):
    """
    Extract CSV-ready metrics from the consistency analysis data.
    This replicates the metrics that were calculated in the old batch system.
    """
    metrics = {
        'num_runs': len(experiment_dirs),
        'successful_ontology_extractions': 0,
        'successful_code_extractions': 0,
        'overall_consistency_score': 0.0,
        'consistency_grade': 'F (Inconsistent)',
    }
    
    # Initialize ontology metrics
    for category in ['CellOntology', 'GeneOntology', 'MeSH']:
        metrics[f'{category}_unique_terms'] = 0
        metrics[f'{category}_avg_consistency'] = 0.0
        metrics[f'{category}_max_consistency'] = 0.0
        metrics[f'{category}_perfect_terms'] = 0
    
    # Initialize code metrics
    metrics['code_avg_similarity'] = 0.0
    metrics['code_min_similarity'] = 0.0
    metrics['code_max_similarity'] = 0.0
    
    # Extract ontology consistency data
    if 'natural_to_ontology' in consistency_metrics:
        ontology_data = consistency_metrics['natural_to_ontology']['ontology_consistency']
        metrics['successful_ontology_extractions'] = len([d for d in experiment_dirs if (Path(d) / "experiment_data.json").exists()])
        
        for category in ['CellOntology', 'GeneOntology', 'MeSH']:
            if category in ontology_data and ontology_data[category]:
                term_frequencies = ontology_data[category]
                frequencies = list(term_frequencies.values())
                
                metrics[f'{category}_unique_terms'] = len(term_frequencies)
                metrics[f'{category}_avg_consistency'] = round(statistics.mean(frequencies), 3)
                metrics[f'{category}_max_consistency'] = round(max(frequencies), 3)
                metrics[f'{category}_perfect_terms'] = sum(1 for f in frequencies if f == 1.0)
    
    # Extract code similarity data
    if 'ontology_to_code' in consistency_metrics and consistency_metrics['ontology_to_code']['code_similarity']:
        code_similarities = consistency_metrics['ontology_to_code']['code_similarity']
        similarity_values = [pair['similarity'] for pair in code_similarities]
        metrics['successful_code_extractions'] = len([d for d in experiment_dirs if (Path(d) / "experiment_data.json").exists()])
        
        if similarity_values:
            metrics['code_avg_similarity'] = round(statistics.mean(similarity_values), 3)
            metrics['code_min_similarity'] = round(min(similarity_values), 3)
            metrics['code_max_similarity'] = round(max(similarity_values), 3)
    
    # Calculate overall consistency score (simplified version)
    ontology_scores = []
    for category in ['CellOntology', 'GeneOntology', 'MeSH']:
        if metrics[f'{category}_avg_consistency'] > 0:
            ontology_scores.append(metrics[f'{category}_avg_consistency'])
    
    if ontology_scores and metrics['code_avg_similarity'] > 0:
        # Weight ontology consistency (60%) and code similarity (40%)
        avg_ontology = statistics.mean(ontology_scores)
        metrics['overall_consistency_score'] = round(0.6 * avg_ontology + 0.4 * metrics['code_avg_similarity'], 3)
    elif ontology_scores:
        metrics['overall_consistency_score'] = round(statistics.mean(ontology_scores), 3)
    elif metrics['code_avg_similarity'] > 0:
        metrics['overall_consistency_score'] = round(metrics['code_avg_similarity'], 3)
    
    # Convert to letter grade
    score = metrics['overall_consistency_score']
    if score >= 0.9:
        metrics['consistency_grade'] = "A+ (Excellent)"
    elif score >= 0.8:
        metrics['consistency_grade'] = "A (Very Good)"
    elif score >= 0.7:
        metrics['consistency_grade'] = "B+ (Good)"
    elif score >= 0.6:
        metrics['consistency_grade'] = "B (Fair)"
    elif score >= 0.5:
        metrics['consistency_grade'] = "C+ (Moderate)"
    elif score >= 0.4:
        metrics['consistency_grade'] = "C (Poor)"
    elif score >= 0.3:
        metrics['consistency_grade'] = "D (Very Poor)"
    else:
        metrics['consistency_grade'] = "F (Inconsistent)"
    
    return metrics

def batch_process_to_csv(input_csv, num_runs_per_paper=3, output_csv="paper_consistency_results.csv", model_type="reasoning"):
    """
    Process papers from CSV using the full experimental_code.py workflow.
    This generates all the rich outputs for each paper AND creates a CSV summary.
    """
    
    # Load abstracts
    abstracts = load_abstracts_csv(input_csv)
    print(f"Loaded {len(abstracts)} paper abstracts from {input_csv}")
    print(f"Using {model_type} model for all experiments")
    
    # Create batch directory with model type in name
    batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = Path(f"experiments/batch_{model_type}_{batch_timestamp}")
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare CSV data
    csv_data = []
    all_experiment_dirs = []
    
    # Process each paper using the FULL experimental workflow
    for i, paper in enumerate(abstracts, 1):
        print(f"\n{'='*80}")
        print(f"PROCESSING PAPER {i}/{len(abstracts)} with {model_type.upper()} MODEL")
        print(f"{'='*80}")
        print(f"Title: {paper['name'][:60]}...")
        print(f"Abstract length: {len(paper['abstract'])} characters")
        
        # Generate experiment name from first two words of paper title
        experiment_name = get_experiment_name_from_title(paper['name'], i)
        print(f"Experiment name: {experiment_name}")
        
        try:
            # Run the COMPLETE experimental_code.py workflow with specified model
            experiment_dirs, main_experiment_dir, consistency_metrics = run_full_experiment_workflow(
                experiment_name, paper['abstract'], num_runs_per_paper, batch_timestamp, batch_dir, model_type
            )
            
            # Extract metrics for CSV
            metrics = extract_metrics_from_consistency_data(consistency_metrics, experiment_dirs)
            
            # Prepare row data
            row_data = {
                'paper_id': i,
                'paper_name': paper['name'],
                'experiment_name': experiment_name,
                'model_type': model_type,
                'abstract_length': len(paper['abstract']),
                'experiment_directory': str(main_experiment_dir),
                **metrics  # Include all extracted metrics
            }
            
            csv_data.append(row_data)
            all_experiment_dirs.extend(experiment_dirs)
            
            print(f"Paper {i} complete. Overall Score: {metrics['overall_consistency_score']:.3f} ({metrics['consistency_grade']})")
            print(f"Rich outputs saved in: {main_experiment_dir}")
            
        except Exception as e:
            print(f"Error processing paper {i}: {str(e)}")
            # Add error row to CSV
            row_data = {
                'paper_id': i,
                'paper_name': paper['name'],
                'experiment_name': experiment_name,
                'model_type': model_type,
                'abstract_length': len(paper['abstract']),
                'experiment_directory': 'ERROR',
                'num_runs': 0,
                'successful_ontology_extractions': 0,
                'successful_code_extractions': 0,
                'overall_consistency_score': 0.0,
                'consistency_grade': 'ERROR',
            }
            
            # Initialize error metrics
            for category in ['CellOntology', 'GeneOntology', 'MeSH']:
                row_data[f'{category}_unique_terms'] = 0
                row_data[f'{category}_avg_consistency'] = 0.0
                row_data[f'{category}_max_consistency'] = 0.0
                row_data[f'{category}_perfect_terms'] = 0
            
            row_data.update({
                'code_avg_similarity': 0.0,
                'code_min_similarity': 0.0,
                'code_max_similarity': 0.0
            })
            
            csv_data.append(row_data)
    
    # Write CSV summary
    output_path = batch_dir / output_csv
    
    if csv_data:
        fieldnames = [
            'paper_id', 'paper_name', 'experiment_name', 'model_type', 'abstract_length', 'experiment_directory',
            'num_runs', 'successful_ontology_extractions', 'successful_code_extractions',
            'overall_consistency_score', 'consistency_grade',
            'CellOntology_unique_terms', 'CellOntology_avg_consistency', 'CellOntology_max_consistency', 'CellOntology_perfect_terms',
            'GeneOntology_unique_terms', 'GeneOntology_avg_consistency', 'GeneOntology_max_consistency', 'GeneOntology_perfect_terms',
            'MeSH_unique_terms', 'MeSH_avg_consistency', 'MeSH_max_consistency', 'MeSH_perfect_terms',
            'code_avg_similarity', 'code_min_similarity', 'code_max_similarity'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        print(f"\n{'='*80}")
        print(f"BATCH PROCESSING COMPLETE!")
        print(f"{'='*80}")
        print(f"Model used: {model_type.upper()}")
        print(f"CSV summary saved to: {output_path}")
        
        # Print enhanced summary statistics
        print(f"\nSUMMARY STATISTICS:")
        print(f"Papers processed: {len(csv_data)}")
        
        # Calculate overall averages (only for papers with data)
        overall_scores = [row['overall_consistency_score'] for row in csv_data if row['overall_consistency_score'] > 0]
        cell_ont_values = [row['CellOntology_avg_consistency'] for row in csv_data if row['CellOntology_avg_consistency'] > 0]
        gene_ont_values = [row['GeneOntology_avg_consistency'] for row in csv_data if row['GeneOntology_avg_consistency'] > 0]
        mesh_values = [row['MeSH_avg_consistency'] for row in csv_data if row['MeSH_avg_consistency'] > 0]
        code_values = [row['code_avg_similarity'] for row in csv_data if row['code_avg_similarity'] > 0]
        
        if overall_scores:
            avg_overall = statistics.mean(overall_scores)
            print(f"\nOVERALL CONSISTENCY METRICS:")
            print(f"Average Overall Score: {avg_overall:.3f}")
            print(f"Best Paper Score: {max(overall_scores):.3f}")
            print(f"Worst Paper Score: {min(overall_scores):.3f}")
            print(f"Standard Deviation: {statistics.stdev(overall_scores):.3f}")
            
            # Grade distribution
            grades = [row['consistency_grade'] for row in csv_data if row['overall_consistency_score'] > 0]
            grade_counts = {}
            for grade in grades:
                grade_letter = grade.split()[0]  # Extract just the letter grade
                grade_counts[grade_letter] = grade_counts.get(grade_letter, 0) + 1
            
            print(f"\nGRADE DISTRIBUTION:")
            for grade, count in sorted(grade_counts.items()):
                print(f"{grade}: {count} papers ({100*count/len(overall_scores):.1f}%)")
        
        print(f"\nCOMPONENT METRICS:")
        if cell_ont_values:
            print(f"Average CellOntology consistency: {statistics.mean(cell_ont_values):.1%}")
        if gene_ont_values:
            print(f"Average GeneOntology consistency: {statistics.mean(gene_ont_values):.1%}")
        if mesh_values:
            print(f"Average MeSH consistency: {statistics.mean(mesh_values):.1%}")
        if code_values:
            print(f"Average code similarity: {statistics.mean(code_values):.1%}")
        
        print(f"\nEach paper has been processed with the FULL experimental workflow using {model_type.upper()} model.")
        print(f"Check individual experiment directories for rich outputs:")
        print(f"  • ontology_comparison.txt - Side-by-side ontology comparison")
        print(f"  • experiment_summary.txt - Detailed run information")  
        print(f"  • consistency_analysis.txt - Professional analysis report")
        print(f"  • run_X/experiment_data.json - Comprehensive data per run")
        print(f"  • run_X/generated_cc3d_model.cc3d - Generated models")
        print(f"  • Thinking processes logged for reasoning model runs")
    
    return output_path

if __name__ == "__main__":
    # Example usage
    input_csv = input("Enter path to input CSV file: ")
    num_runs = int(input("Enter number of runs per paper (default 3): ") or "3")
    
    # Model selection
    print("\nChoose the AI model to use for all papers:")
    print("1. DeepSeek R1 (reasoning model) - Shows step-by-step thinking")
    print("2. DeepSeek V3 (non-reasoning model) - Direct responses")
    model_choice = input("Enter your choice (1 or 2, default: 1): ").strip() or "1"
    
    if model_choice == "1":
        model_type = "reasoning"
        print("Using DeepSeek R1 (reasoning model) for all papers")
    elif model_choice == "2":
        model_type = "non_reasoning"
        print("Using DeepSeek V3 (non-reasoning model) for all papers")
    else:
        model_type = "reasoning"
        print("Invalid choice, defaulting to DeepSeek R1 (reasoning model)")
    
    output_name = input("Enter output CSV filename (default: paper_consistency_results.csv): ") or "paper_consistency_results.csv"
    
    batch_process_to_csv(input_csv, num_runs, output_name, model_type) 