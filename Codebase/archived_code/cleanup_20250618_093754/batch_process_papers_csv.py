import os
import json
import csv
import statistics
from pathlib import Path
from datetime import datetime
from experimental_code import run_experiment, analyze_run_consistency, extract_ontologies_from_response, extract_code_from_response, calculate_similarity

def load_abstracts(abstracts_file):
    """Load paper abstracts from a file"""
    abstracts = []
    
    if abstracts_file.endswith('.json'):
        # JSON format: [{"title": "Paper 1", "abstract": "..."}, ...]
        with open(abstracts_file, 'r') as f:
            data = json.load(f)
            for item in data:
                abstracts.append({
                    'name': item.get('title', f'Paper_{len(abstracts)+1}'),
                    'abstract': item.get('abstract', item.get('text', ''))
                })
    elif abstracts_file.endswith('.csv'):
        # CSV format: title,abstract
        with open(abstracts_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                abstracts.append({
                    'name': row.get('title', row.get('Title', f'Paper_{i+1}')),
                    'abstract': row.get('abstract', row.get('Abstract', row.get('text', '')))
                })
    else:
        # Text file format: each abstract separated by "---" or empty lines
        with open(abstracts_file, 'r') as f:
            content = f.read()
            
        # Split by "---" or double newlines
        if '---' in content:
            parts = content.split('---')
        else:
            parts = content.split('\n\n\n')
            
        for i, part in enumerate(parts):
            if part.strip():
                abstracts.append({
                    'name': f'Paper_{i+1}',
                    'abstract': part.strip()
                })
    
    return abstracts

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

def batch_process_papers_to_csv(abstracts_file, num_runs_per_paper=3, output_csv="paper_consistency_results.csv"):
    """Process multiple paper abstracts and output results to CSV"""
    
    # Load abstracts
    abstracts = load_abstracts(abstracts_file)
    print(f"Loaded {len(abstracts)} paper abstracts")
    
    # Create batch directory
    batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = Path(f"experiments/batch_{batch_timestamp}")
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare CSV data
    csv_data = []
    
    # Process each paper
    for i, paper in enumerate(abstracts, 1):
        print(f"\n{'='*60}")
        print(f"Processing Paper {i}/{len(abstracts)}: {paper['name']}")
        print(f"{'='*60}")
        
        # Run multiple experiments for this paper
        paper_dirs = []
        for run in range(1, num_runs_per_paper + 1):
            experiment_name = f"paper_{i:02d}_{paper['name'][:20].replace(' ', '_')}"
            experiment_dir = run_experiment(experiment_name, paper['abstract'], run, num_runs_per_paper)
            paper_dirs.append(experiment_dir)
        
        # Analyze consistency for this paper
        print(f"Analyzing consistency for {paper['name']}...")
        ontology_results, code_results = analyze_paper_consistency(paper_dirs)
        
        # Calculate metrics
        ontology_metrics = calculate_ontology_consistency(ontology_results)
        code_metrics = calculate_code_similarity_metrics(code_results)
        
        # Prepare row data
        row_data = {
            'paper_id': i,
            'paper_name': paper['name'],
            'abstract_length': len(paper['abstract']),
            'num_runs': len(paper_dirs),
            'successful_ontology_extractions': len(ontology_results),
            'successful_code_extractions': len(code_results),
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
        print(f"Paper {i} analysis complete.")
    
    # Write to CSV
    output_path = batch_dir / output_csv
    
    if csv_data:
        fieldnames = csv_data[0].keys()
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        print(f"\nResults saved to: {output_path}")
        
        # Print summary statistics
        print(f"\nSUMMARY STATISTICS:")
        print(f"Papers processed: {len(csv_data)}")
        
        # Calculate overall averages
        cell_ont_avg = statistics.mean([row['CellOntology_avg_consistency'] for row in csv_data if row['CellOntology_avg_consistency'] > 0])
        gene_ont_avg = statistics.mean([row['GeneOntology_avg_consistency'] for row in csv_data if row['GeneOntology_avg_consistency'] > 0])
        mesh_avg = statistics.mean([row['MeSH_avg_consistency'] for row in csv_data if row['MeSH_avg_consistency'] > 0])
        code_avg = statistics.mean([row['code_avg_similarity'] for row in csv_data if row['code_avg_similarity'] > 0])
        
        print(f"Average CellOntology consistency: {cell_ont_avg:.1%}")
        print(f"Average GeneOntology consistency: {gene_ont_avg:.1%}")
        print(f"Average MeSH consistency: {mesh_avg:.1%}")
        print(f"Average code similarity: {code_avg:.1%}")
    
    return output_path

if __name__ == "__main__":
    # Example usage
    abstracts_file = input("Enter path to abstracts file: ")
    num_runs = int(input("Enter number of runs per paper (default 3): ") or "3")
    output_name = input("Enter CSV output filename (default: paper_consistency_results.csv): ") or "paper_consistency_results.csv"
    
    batch_process_papers_to_csv(abstracts_file, num_runs, output_name) 