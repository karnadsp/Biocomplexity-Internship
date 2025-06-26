#!/usr/bin/env python3

"""
Show EXACTLY where cc3d_object_analyzer.py pulls data from and where results go
"""

from pathlib import Path
import json

def show_exact_data_sources():
    """Show precisely where the analyzer gets its data"""
    
    print("🔍 EXACT DATA FLOW FOR cc3d_object_analyzer.py")
    print("=" * 60)
    
    print("\n📥 HARDCODED INPUT SOURCE:")
    print("Line 594 in cc3d_object_analyzer.py:")
    print('    experiment_dir = Path("experiments/paper_01_Lattice-Based_Model_20250618_160019")')
    print("\n📁 This means it AUTOMATICALLY reads from:")
    
    experiment_dir = Path("experiments/paper_01_Lattice-Based_Model_20250618_160019")
    
    if experiment_dir.exists():
        print(f"✓ {experiment_dir}")
        
        # Show all the run directories it reads from
        run_dirs = [d for d in experiment_dir.iterdir() if d.is_dir() and d.name.startswith('run_')]
        run_dirs.sort(key=lambda x: int(x.name.split('_')[1]))
        
        print(f"\n📂 SPECIFIC FILES IT READS (automatically):")
        for run_dir in run_dirs:
            data_file = run_dir / "experiment_data.json"
            if data_file.exists():
                print(f"✓ {data_file}")
            else:
                print(f"❌ {data_file} (missing)")
        
        print(f"\n🔍 INSIDE EACH experiment_data.json FILE:")
        print("The analyzer looks for Python code in TWO places:")
        print("1. data['metadata']['cc3d_file_creation']['python_code']  ← PRIMARY")
        print("2. data['llm_responses'][1]['response']  ← FALLBACK")
        
        # Show example from one file
        sample_file = experiment_dir / "run_1" / "experiment_data.json"
        if sample_file.exists():
            with open(sample_file, 'r') as f:
                data = json.load(f)
            
            print(f"\n📄 EXAMPLE FROM {sample_file}:")
            
            # Check primary source
            if 'metadata' in data and 'cc3d_file_creation' in data['metadata']:
                code = data['metadata']['cc3d_file_creation']['python_code']
                print(f"✓ Found code in metadata (PRIMARY): {len(code)} characters")
                print(f"   First 100 chars: {code[:100]}...")
            
            # Check fallback source
            if 'llm_responses' in data and len(data['llm_responses']) > 1:
                response = data['llm_responses'][1]['response']
                print(f"✓ Found LLM response (FALLBACK): {len(response)} characters")
                print(f"   First 100 chars: {response[:100]}...")
    else:
        print(f"❌ {experiment_dir} (not found)")
    
    print(f"\n📤 WHERE RESULTS GO:")
    print("The analyzer does NOT save results to files automatically!")
    print("Results are only:")
    print("1. 🖥️  Printed to console/terminal")
    print("2. 🔄 Returned as Python objects in memory")
    print("3. 💾 Only saved if YOU explicitly write code to save them")

def show_how_to_save_results():
    """Show how to save the analyzer results"""
    
    print(f"\n" + "="*60)
    print("💾 HOW TO SAVE ANALYZER RESULTS")
    print("="*60)
    
    print(f"\nCurrently, when you run:")
    print("python Codebase/cc3d_object_analyzer.py")
    print(f"\nThe results are:")
    print("✓ Displayed on screen")
    print("❌ NOT saved to any file")
    
    print(f"\n📝 TO SAVE RESULTS, you would need to modify the code:")
    
    save_example = '''
# Add this to the end of cc3d_object_analyzer.py:
if __name__ == "__main__":
    experiment_dir = Path("experiments/paper_01_Lattice-Based_Model_20250618_160019")
    results = analyze_experiment_objects(experiment_dir)
    
    # Save to JSON file
    output_file = Path("object_analysis_results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results saved to: {output_file}")
    
    # Save to CSV summary
    import pandas as pd
    df = pd.DataFrame(results['run_info'])
    df.to_csv("run_summary.csv", index=False)
    print("Run summary saved to: run_summary.csv")
'''
    
    print(save_example)

def show_current_vs_desired_flow():
    """Show current flow vs what you might want"""
    
    print(f"\n" + "="*60)
    print("🔄 CURRENT vs DESIRED DATA FLOW")
    print("="*60)
    
    print(f"\n📋 CURRENT FLOW:")
    print("1. You run: python Codebase/cc3d_object_analyzer.py")
    print("2. It reads: experiments/paper_01_Lattice-Based_Model_20250618_160019/run_*/experiment_data.json")
    print("3. It analyzes: Python code objects from those files")
    print("4. It prints: Results to console")
    print("5. Results disappear when script ends")
    
    print(f"\n🎯 WHAT YOU PROBABLY WANT:")
    print("1. Analyze ALL experiments (not just paper_01)")
    print("2. Save results to files for later analysis")
    print("3. Generate reports comparing all papers")
    print("4. Integrate with your existing batch processing")
    
    print(f"\n💡 AVAILABLE EXPERIMENTS TO ANALYZE:")
    experiments_dir = Path("experiments")
    if experiments_dir.exists():
        paper_dirs = [d for d in experiments_dir.iterdir() 
                     if d.is_dir() and d.name.startswith('paper_')]
        for paper_dir in sorted(paper_dirs):
            run_count = len([d for d in paper_dir.iterdir() 
                           if d.is_dir() and d.name.startswith('run_')])
            print(f"   • {paper_dir.name} ({run_count} runs)")

if __name__ == "__main__":
    show_exact_data_sources()
    show_how_to_save_results()
    show_current_vs_desired_flow()
    
    print(f"\n" + "="*60)
    print("📍 SUMMARY: EXACT DATA LOCATIONS")
    print("="*60)
    print("INPUT: Hardcoded path to experiments/paper_01_Lattice-Based_Model_20250618_160019/")
    print("READS: run_*/experiment_data.json files")
    print("EXTRACTS: Python code from metadata or llm_responses")
    print("OUTPUTS: Console display only (no files saved)")
    print("RESULT: Temporary analysis that disappears when script ends") 