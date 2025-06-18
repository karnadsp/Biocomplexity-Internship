#!/usr/bin/env python3

import os
import json
import csv
import statistics
from pathlib import Path
from datetime import datetime
from experimental_code import run_experiment, extract_ontologies_from_response, extract_code_from_response, calculate_similarity

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

def calculate_overall_consistency_score(ontology_metrics, code_metrics):
    """Calculate an overall consistency score combining ontology and code metrics"""
    scores = []
    
    # Add ontology consistency scores (weighted by category importance)
    ontology_weights = {
        'CellOntology': 0.4,  # Most important for biological modeling
        'GeneOntology': 0.3,  # Important for molecular processes
        'MeSH': 0.2          # General medical terms
    }
    
    ontology_score = 0.0
    total_weight = 0.0
    
    for category, weight in ontology_weights.items():
        if category in ontology_metrics and ontology_metrics[category]['avg_consistency'] > 0:
            ontology_score += ontology_metrics[category]['avg_consistency'] * weight
            total_weight += weight
    
    if total_weight > 0:
        ontology_score = ontology_score / total_weight
        scores.append(ontology_score)
    
    # Add code similarity score
    if code_metrics and code_metrics['avg_similarity'] > 0:
        scores.append(code_metrics['avg_similarity'])
    
    # Calculate overall score as weighted average
    if scores:
        # Weight ontology consistency (60%) and code similarity (40%)
        if len(scores) == 2:  # Both ontology and code available
            overall_score = 0.6 * scores[0] + 0.4 * scores[1]
        else:  # Only one metric available
            overall_score = scores[0]
        
        return round(overall_score, 3)
    
    return 0.0

def get_consistency_grade(score):
    """Convert consistency score to letter grade"""
    if score >= 0.9:
        return "A+ (Excellent)"
    elif score >= 0.8:
        return "A (Very Good)"
    elif score >= 0.7:
        return "B+ (Good)"
    elif score >= 0.6:
        return "B (Fair)"
    elif score >= 0.5:
        return "C+ (Moderate)"
    elif score >= 0.4:
        return "C (Poor)"
    elif score >= 0.3:
        return "D (Very Poor)"
    else:
        return "F (Inconsistent)"

def calculate_ontology_consistency(ontology_results):
    """Calculate consistency metrics for ontology results"""
    if len(ontology_results) < 2:
        return {}
    
    consistency_metrics = {}
    
    for category in ['CellOntology', 'GeneOntology', 'MeSH']:
        # Get all unique terms across runs
        all_terms = set()
        for result in ontology_results:
            if result and category in result:
                all_terms.update(result[category])
        
        if not all_terms:
            consistency_metrics[category] = {
                'unique_terms': 0,
                'avg_consistency': 0.0,
                'max_consistency': 0.0,
                'terms_with_100_percent': 0
            }
            continue
        
        # Calculate frequency of each term
        term_frequencies = {}
        for term in all_terms:
            count = sum(1 for result in ontology_results 
                       if result and category in result and term in result[category])
            term_frequencies[term] = count / len(ontology_results)
        
        # Calculate metrics
        frequencies = list(term_frequencies.values())
        consistency_metrics[category] = {
            'unique_terms': len(all_terms),
            'avg_consistency': statistics.mean(frequencies) if frequencies else 0.0,
            'max_consistency': max(frequencies) if frequencies else 0.0,
            'terms_with_100_percent': sum(1 for f in frequencies if f == 1.0)
        }
    
    return consistency_metrics

def calculate_code_similarity_metrics(code_results):
    """Calculate code similarity metrics"""
    if len(code_results) < 2:
        return {}
    
    similarities = []
    for i in range(len(code_results)):
        for j in range(i + 1, len(code_results)):
            similarity = calculate_similarity(code_results[i], code_results[j])
            similarities.append(similarity)
    
    return {
        'avg_similarity': statistics.mean(similarities) if similarities else 0.0,
        'min_similarity': min(similarities) if similarities else 0.0,
        'max_similarity': max(similarities) if similarities else 0.0,
        'num_comparisons': len(similarities)
    }

def analyze_paper_consistency(paper_dirs):
    """Analyze consistency for a single paper's runs"""
    ontology_results = []
    code_results = []
    
    for run_dir in paper_dirs:
        try:
            with open(Path(run_dir) / "experiment_summary.json", 'r') as f:
                data = json.load(f)
            
            # Get LLM responses in order
            llm_responses = []
            for interaction in data['interactions']:
                if interaction['step'] == 'llm_response':
                    llm_responses.append(interaction)
            
            # Process ontology response (first response)
            if len(llm_responses) >= 1:
                raw_response = llm_responses[0]['output']['response']
                processed_response = raw_response
                
                if "</think>" in processed_response:
                    processed_response = processed_response.split("</think>")[-1].strip()
                if "```json" in processed_response:
                    processed_response = processed_response.split("```json")[1].split("```")[0].strip()
                elif "```" in processed_response:
                    processed_response = processed_response.split("```")[1].split("```")[0].strip()
                
                ontologies = extract_ontologies_from_response(processed_response)
                ontology_results.append(ontologies)
            
            # Process code response (second response)
            if len(llm_responses) >= 2:
                code = extract_code_from_response(llm_responses[1]['output']['response'])
                code_results.append(code)
        
        except Exception as e:
            print(f"Error processing {run_dir}: {str(e)}")
            continue
    
    return ontology_results, code_results

def batch_process_to_csv(input_csv, num_runs_per_paper=3, output_csv="paper_consistency_results.csv"):
    """Process papers from CSV and output consistency results to CSV"""
    
    # Load abstracts
    abstracts = load_abstracts_csv(input_csv)
    print(f"Loaded {len(abstracts)} paper abstracts from {input_csv}")
    
    # Create batch directory
    batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = Path(f"experiments/batch_{batch_timestamp}")
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare CSV data
    csv_data = []
    
    # Process each paper
    for i, paper in enumerate(abstracts, 1):
        print(f"\n{'='*60}")
        print(f"Processing Paper {i}/{len(abstracts)}: {paper['name'][:50]}...")
        print(f"{'='*60}")
        
        # Generate experiment name from first two words of paper title
        experiment_name = get_experiment_name_from_title(paper['name'], i)
        print(f"Experiment name: {experiment_name}")
        
        # Run multiple experiments for this paper
        paper_dirs = []
        for run in range(1, num_runs_per_paper + 1):
            experiment_dir = run_experiment(experiment_name, paper['abstract'], run, num_runs_per_paper)
            paper_dirs.append(experiment_dir)
        
        # Analyze consistency for this paper
        print(f"Analyzing consistency...")
        ontology_results, code_results = analyze_paper_consistency(paper_dirs)
        
        # Calculate metrics
        ontology_metrics = calculate_ontology_consistency(ontology_results)
        code_metrics = calculate_code_similarity_metrics(code_results)
        
        # Calculate overall consistency score
        overall_score = calculate_overall_consistency_score(ontology_metrics, code_metrics)
        consistency_grade = get_consistency_grade(overall_score)
        
        # Prepare row data
        row_data = {
            'paper_id': i,
            'paper_name': paper['name'],
            'experiment_name': experiment_name,
            'abstract_length': len(paper['abstract']),
            'num_runs': len(paper_dirs),
            'successful_ontology_extractions': len(ontology_results),
            'successful_code_extractions': len(code_results),
            'overall_consistency_score': overall_score,
            'consistency_grade': consistency_grade,
        }
        
        # Add ontology consistency metrics
        for category in ['CellOntology', 'GeneOntology', 'MeSH']:
            if category in ontology_metrics:
                row_data[f'{category}_unique_terms'] = ontology_metrics[category]['unique_terms']
                row_data[f'{category}_avg_consistency'] = round(ontology_metrics[category]['avg_consistency'], 3)
                row_data[f'{category}_max_consistency'] = round(ontology_metrics[category]['max_consistency'], 3)
                row_data[f'{category}_perfect_terms'] = ontology_metrics[category]['terms_with_100_percent']
            else:
                row_data[f'{category}_unique_terms'] = 0
                row_data[f'{category}_avg_consistency'] = 0.0
                row_data[f'{category}_max_consistency'] = 0.0
                row_data[f'{category}_perfect_terms'] = 0
        
        # Add code similarity metrics
        if code_metrics:
            row_data['code_avg_similarity'] = round(code_metrics['avg_similarity'], 3)
            row_data['code_min_similarity'] = round(code_metrics['min_similarity'], 3)
            row_data['code_max_similarity'] = round(code_metrics['max_similarity'], 3)
        else:
            row_data['code_avg_similarity'] = 0.0
            row_data['code_min_similarity'] = 0.0
            row_data['code_max_similarity'] = 0.0
        
        csv_data.append(row_data)
        print(f"Paper {i} complete. Overall Score: {overall_score:.3f} ({consistency_grade})")
    
    # Write to CSV
    output_path = batch_dir / output_csv
    
    if csv_data:
        fieldnames = [
            'paper_id', 'paper_name', 'experiment_name', 'abstract_length', 'num_runs',
            'successful_ontology_extractions', 'successful_code_extractions',
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
        
        print(f"\nResults saved to: {output_path}")
        
        # Print enhanced summary statistics
        print(f"\n{'='*60}")
        print(f"SUMMARY STATISTICS")
        print(f"{'='*60}")
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
            print(f"Average Overall Score: {avg_overall:.3f} ({get_consistency_grade(avg_overall)})")
            print(f"Best Paper Score: {max(overall_scores):.3f}")
            print(f"Worst Paper Score: {min(overall_scores):.3f}")
            print(f"Standard Deviation: {statistics.stdev(overall_scores):.3f}")
            
            # Grade distribution
            grades = [get_consistency_grade(score) for score in overall_scores]
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
    
    return output_path

if __name__ == "__main__":
    # Example usage
    input_csv = input("Enter path to input CSV file: ")
    num_runs = int(input("Enter number of runs per paper (default 3): ") or "3")
    output_name = input("Enter output CSV filename (default: paper_consistency_results.csv): ") or "paper_consistency_results.csv"
    
    batch_process_to_csv(input_csv, num_runs, output_name) 