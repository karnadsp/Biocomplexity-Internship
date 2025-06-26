#!/usr/bin/env python3

"""
Test script to demonstrate CC3D object analysis on experimental data
"""

import json
from pathlib import Path
from cc3d_object_analyzer import CC3DObjectExtractor, analyze_experiment_objects

def test_single_experiment():
    """Test object analysis on a single experiment"""
    
    # Test with paper_01 experiment
    experiment_dir = Path("experiments/paper_01_Lattice-Based_Model_20250618_160019")
    
    print("CC3D Object Analysis Test")
    print("=" * 50)
    print(f"Analyzing experiment: {experiment_dir.name}")
    
    if not experiment_dir.exists():
        print(f"Error: Experiment directory not found: {experiment_dir}")
        return
    
    # Run the analysis
    results = analyze_experiment_objects(experiment_dir)
    
    if "error" in results:
        print(f"Error: {results['error']}")
        return
    
    print(f"\n✓ Successfully analyzed {results['files_analyzed']} runs")
    print(f"Experiment directory: {results['experiment_dir']}")
    
    print(f"\n📊 RUN SUMMARY:")
    print("-" * 40)
    for run_info in results['run_info']:
        print(f"Run {run_info['run']:2d}: {run_info['api_style']:8s} API | "
              f"{run_info['num_classes']:2d} classes | "
              f"{run_info['num_cell_types']:2d} cell types | "
              f"{run_info['num_parameters']:2d} parameters | "
              f"{run_info['num_behaviors']:2d} behaviors")
        
        if run_info['has_syntax_errors']:
            print(f"        ⚠️  Syntax errors: {run_info['syntax_errors']}")
    
    return results

def detailed_code_comparison():
    """Show detailed comparison of code objects between runs"""
    
    experiment_dir = Path("experiments/paper_01_Lattice-Based_Model_20250618_160019")
    extractor = CC3DObjectExtractor()
    
    print(f"\n🔍 DETAILED CODE OBJECT COMPARISON")
    print("=" * 60)
    
    # Extract objects from first few runs for detailed comparison
    run_objects = []
    
    for run_num in [1, 2, 3]:
        run_dir = experiment_dir / f"run_{run_num}"
        if not run_dir.exists():
            continue
            
        data_file = run_dir / "experiment_data.json"
        if not data_file.exists():
            continue
            
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        # Extract code
        code_content = None
        if 'llm_responses' in data and len(data['llm_responses']) > 1:
            response = data['llm_responses'][1]['response']
            if '```python' in response:
                code_content = response.split('```python')[1].split('```')[0].strip()
            elif '```' in response:
                code_content = response.split('```')[1].split('```')[0].strip()
        
        if code_content:
            objects = extractor.extract_objects(code_content, f"run_{run_num}")
            run_objects.append((run_num, objects))
            
            print(f"\n📝 RUN {run_num} OBJECTS:")
            print(f"   API Style: {objects.api_style}")
            print(f"   Imports: {len(objects.imports)} items")
            for imp in objects.imports[:3]:  # Show first 3
                print(f"     • {imp}")
            if len(objects.imports) > 3:
                print(f"     ... and {len(objects.imports) - 3} more")
            
            print(f"   Classes: {len(objects.classes)} items")
            for cls in objects.classes:
                methods = [m['name'] for m in cls['methods']]
                print(f"     • {cls['name']} with methods: {methods}")
            
            print(f"   Cell Types: {len(objects.cell_types)} items")
            for cell_type in objects.cell_types.keys():
                print(f"     • {cell_type}")
            
            print(f"   Parameters: {len(objects.parameters)} items")
            for param, value in list(objects.parameters.items())[:5]:  # Show first 5
                print(f"     • {param} = {value}")
            
            print(f"   Biological Processes: {len(objects.biological_processes)} items")
            for process in objects.biological_processes:
                print(f"     • {process}")
    
    # Compare between runs
    if len(run_objects) >= 2:
        print(f"\n🔄 COMPARISON BETWEEN RUNS:")
        print("-" * 40)
        
        run1_num, run1_obj = run_objects[0]
        run2_num, run2_obj = run_objects[1]
        
        print(f"Comparing Run {run1_num} vs Run {run2_num}:")
        
        # API Style comparison
        if run1_obj.api_style == run2_obj.api_style:
            print(f"  ✓ API Style: Both use {run1_obj.api_style}")
        else:
            print(f"  ❌ API Style: Run {run1_num}={run1_obj.api_style}, Run {run2_num}={run2_obj.api_style}")
        
        # Import comparison
        run1_imports = set(run1_obj.imports)
        run2_imports = set(run2_obj.imports)
        common_imports = run1_imports & run2_imports
        unique_run1 = run1_imports - run2_imports
        unique_run2 = run2_imports - run1_imports
        
        print(f"  📦 Imports: {len(common_imports)} common, {len(unique_run1)} unique to Run {run1_num}, {len(unique_run2)} unique to Run {run2_num}")
        if unique_run1:
            print(f"    Run {run1_num} only: {list(unique_run1)[:3]}")
        if unique_run2:
            print(f"    Run {run2_num} only: {list(unique_run2)[:3]}")
        
        # Class comparison
        run1_classes = {cls['name'] for cls in run1_obj.classes}
        run2_classes = {cls['name'] for cls in run2_obj.classes}
        common_classes = run1_classes & run2_classes
        
        print(f"  🏗️  Classes: {len(common_classes)} common")
        if run1_classes != run2_classes:
            unique_run1_cls = run1_classes - run2_classes
            unique_run2_cls = run2_classes - run1_classes
            if unique_run1_cls:
                print(f"    Run {run1_num} only: {unique_run1_cls}")
            if unique_run2_cls:
                print(f"    Run {run2_num} only: {unique_run2_cls}")
        
        # Parameter comparison
        run1_params = set(run1_obj.parameters.keys())
        run2_params = set(run2_obj.parameters.keys())
        common_params = run1_params & run2_params
        
        print(f"  ⚙️  Parameters: {len(common_params)} common parameter names")
        
        # Check if common parameters have same values
        param_differences = []
        for param in common_params:
            if run1_obj.parameters[param] != run2_obj.parameters[param]:
                param_differences.append((param, run1_obj.parameters[param], run2_obj.parameters[param]))
        
        if param_differences:
            print(f"    ❌ {len(param_differences)} parameters have different values:")
            for param, val1, val2 in param_differences[:3]:  # Show first 3
                print(f"      • {param}: Run {run1_num}={val1}, Run {run2_num}={val2}")
        else:
            print(f"    ✓ All common parameters have identical values")

if __name__ == "__main__":
    # Run the tests
    results = test_single_experiment()
    
    if results and "error" not in results:
        detailed_code_comparison()
    
    print(f"\n🎯 CONCLUSION:")
    print("The CC3D Object Analyzer can extract and compare:")
    print("  • API styles (modern vs legacy CC3D)")
    print("  • Import statements and dependencies")
    print("  • Class definitions and methods")
    print("  • Cell types and biological entities")
    print("  • Parameters and their values")
    print("  • Biological processes and behaviors")
    print("  • Syntax errors and code quality")
    print(f"\nThis gives you much more insight than simple text similarity!") 