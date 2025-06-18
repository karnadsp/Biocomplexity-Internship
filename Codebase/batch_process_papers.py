import os
import json
from pathlib import Path
from datetime import datetime
from experimental_code import run_experiment, analyze_run_consistency, format_consistency_analysis

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

def batch_process_papers(abstracts_file, num_runs_per_paper=3):
    """Process multiple paper abstracts"""
    
    # Load abstracts
    abstracts = load_abstracts(abstracts_file)
    print(f"Loaded {len(abstracts)} paper abstracts")
    
    # Create batch directory
    batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = Path(f"experiments/batch_{batch_timestamp}")
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each paper
    all_experiment_dirs = []
    
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
            all_experiment_dirs.append(experiment_dir)
        
        # Analyze consistency for this paper
        if len(paper_dirs) > 1:
            print(f"\nAnalyzing consistency for {paper['name']}...")
            consistency_metrics = analyze_run_consistency(paper_dirs)
            consistency_analysis = format_consistency_analysis(consistency_metrics)
            
            # Save paper-specific analysis
            paper_analysis_file = batch_dir / f"paper_{i:02d}_analysis.txt"
            with open(paper_analysis_file, 'w') as f:
                f.write(f"Paper: {paper['name']}\n")
                f.write(f"Abstract: {paper['abstract'][:200]}...\n\n")
                f.write(consistency_analysis)
            
            print(f"Paper analysis saved to {paper_analysis_file}")
    
    # Overall batch analysis
    print(f"\n{'='*60}")
    print("OVERALL BATCH ANALYSIS")
    print(f"{'='*60}")
    
    if len(all_experiment_dirs) > 1:
        print("Analyzing consistency across all papers...")
        overall_metrics = analyze_run_consistency(all_experiment_dirs)
        overall_analysis = format_consistency_analysis(overall_metrics)
        
        # Save overall analysis
        overall_analysis_file = batch_dir / "overall_batch_analysis.txt"
        with open(overall_analysis_file, 'w') as f:
            f.write(f"Batch Analysis - {len(abstracts)} papers, {num_runs_per_paper} runs each\n")
            f.write(f"Total experiments: {len(all_experiment_dirs)}\n")
            f.write(f"Processed: {batch_timestamp}\n\n")
            f.write(overall_analysis)
        
        print(f"Overall analysis saved to {overall_analysis_file}")
    
    # Create summary
    summary_file = batch_dir / "batch_summary.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'batch_timestamp': batch_timestamp,
            'num_papers': len(abstracts),
            'runs_per_paper': num_runs_per_paper,
            'total_experiments': len(all_experiment_dirs),
            'papers': [{'name': p['name'], 'abstract_length': len(p['abstract'])} for p in abstracts],
            'experiment_directories': [str(d) for d in all_experiment_dirs]
        }, f, indent=2)
    
    print(f"\nBatch processing complete!")
    print(f"Results saved in: {batch_dir}")
    print(f"Summary: {summary_file}")

if __name__ == "__main__":
    # Example usage
    abstracts_file = input("Enter path to abstracts file: ")
    num_runs = int(input("Enter number of runs per paper (default 3): ") or "3")
    
    batch_process_papers(abstracts_file, num_runs) 