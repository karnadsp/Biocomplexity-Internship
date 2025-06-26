#!/usr/bin/env python3

"""
Flexible CC3D Object Analyzer - Analyze any experiment or batch folder
"""

import ast
import re
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, Counter

@dataclass
class CC3DObjects:
    """Structured representation of objects found in a CC3D model"""
    # File identification
    file_path: str = ""
    
    # Code structure
    imports: List[str] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    functions: List[Dict[str, Any]] = field(default_factory=list)
    
    # CC3D-specific objects
    cell_types: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    plugins: List[Dict[str, Any]] = field(default_factory=list)
    steppables: List[Dict[str, Any]] = field(default_factory=list)
    
    # Configuration objects
    energy_matrices: Dict[str, Any] = field(default_factory=dict)
    contact_configs: List[Dict[str, Any]] = field(default_factory=list)
    volume_configs: List[Dict[str, Any]] = field(default_factory=list)
    
    # Biological behaviors
    behaviors: Dict[str, List[str]] = field(default_factory=dict)
    biological_processes: Set[str] = field(default_factory=set)
    
    # Syntax and structure
    syntax_errors: List[str] = field(default_factory=list)
    api_style: str = "unknown"  # "modern", "legacy", "mixed"

class CC3DObjectExtractor:
    """Extract structured objects from CC3D Python code"""
    
    def __init__(self):
        self.biological_keywords = {
            'proliferation': ['divide', 'proliferat', 'mitosis'],
            'apoptosis': ['apoptosis', 'cell_death', 'die', 'kill'],
            'migration': ['migrat', 'move', 'motil'],
            'adhesion': ['adhesion', 'contact', 'stick'],
            'differentiation': ['different', 'transform'],
            'growth': ['grow', 'volume', 'size'],
        }
        
        self.cc3d_apis = {
            'modern': [
                'cc3d.core.PyCoreSpecs', 'steppables.SteppableBasePy',
                'CellTypePlugin', 'VolumePlugin', 'ContactPlugin'
            ],
            'legacy': [
                'PySteppables', 'SteppableBasePy', 'pybind',
                'addCellType', 'cellField'
            ]
        }
    
    def extract_objects(self, code_content: str, file_path: str = "") -> CC3DObjects:
        """Extract all objects and components from CC3D code"""
        objects = CC3DObjects(file_path=file_path)
        
        # Try to parse with AST first
        try:
            tree = ast.parse(code_content)
            objects.syntax_errors = []
            self._extract_from_ast(tree, objects, code_content)
        except SyntaxError as e:
            objects.syntax_errors.append(f"Line {e.lineno}: {e.msg}")
            # Fall back to regex-based extraction
            self._extract_from_text(code_content, objects)
        
        # Always do text-based extraction for CC3D-specific patterns
        self._extract_cc3d_patterns(code_content, objects)
        
        # Determine API style
        objects.api_style = self._determine_api_style(objects)
        
        return objects
    
    def _extract_from_ast(self, tree: ast.AST, objects: CC3DObjects, code_content: str):
        """Extract objects using Abstract Syntax Tree"""
        
        for node in ast.walk(tree):
            # Extract imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    objects.imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    objects.imports.append(f"{module}.{alias.name}")
            
            # Extract classes
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'bases': [self._ast_to_string(base) for base in node.bases],
                    'methods': [],
                    'attributes': []
                }
                
                # Extract methods and attributes from class
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            'name': item.name,
                            'args': [arg.arg for arg in item.args.args],
                            'is_init': item.name == '__init__',
                            'is_start': item.name == 'start',
                            'is_step': item.name == 'step'
                        }
                        class_info['methods'].append(method_info)
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Attribute):
                                class_info['attributes'].append(target.attr)
                
                objects.classes.append(class_info)
                
                # Check if this is a steppable
                if any('steppable' in str(base).lower() for base in class_info['bases']):
                    objects.steppables.append(class_info)
            
            # Extract standalone functions
            elif isinstance(node, ast.FunctionDef):
                func_info = {
                    'name': node.name,
                    'args': [arg.arg for arg in node.args.args]
                }
                objects.functions.append(func_info)
            
            # Extract assignments for parameters
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute):
                        attr_name = target.attr
                        if isinstance(node.value, ast.Constant):
                            objects.parameters[attr_name] = node.value.value
                        elif isinstance(node.value, ast.Num):  # Python < 3.8 compatibility
                            objects.parameters[attr_name] = node.value.n
    
    def _extract_from_text(self, code_content: str, objects: CC3DObjects):
        """Extract objects using regex patterns (fallback for syntax errors)"""
        
        # Extract imports
        import_patterns = [
            r'from\s+([^\s]+)\s+import\s+([^\n]+)',
            r'import\s+([^\n]+)'
        ]
        for pattern in import_patterns:
            matches = re.findall(pattern, code_content)
            for match in matches:
                if isinstance(match, tuple):
                    objects.imports.append(f"{match[0]}.{match[1]}")
                else:
                    objects.imports.append(match)
        
        # Extract class definitions
        class_pattern = r'class\s+(\w+)\s*\([^)]*\):'
        class_matches = re.findall(class_pattern, code_content)
        for class_name in class_matches:
            objects.classes.append({'name': class_name, 'methods': [], 'bases': []})
        
        # Extract method definitions
        method_pattern = r'def\s+(\w+)\s*\([^)]*\):'
        method_matches = re.findall(method_pattern, code_content)
        for method_name in method_matches:
            objects.functions.append({'name': method_name, 'args': []})
    
    def _extract_cc3d_patterns(self, code_content: str, objects: CC3DObjects):
        """Extract CC3D-specific patterns and objects"""
        
        # Extract cell types
        cell_type_patterns = [
            r'cell_type\.(\w+)',
            r'CellTypePlugin\s*\(\s*["\']([^"\']+)["\']',
            r'addCellType\s*\(\s*["\']([^"\']+)["\']',
            r'self\.(\w+)\s*=\s*self\.cell_type\.',
            r'["\'](\w*EPITHELIAL\w*)["\']',
            r'["\'](\w*MAMMARY\w*)["\']',
            r'["\'](\w*TUMOR\w*)["\']',
            r'["\'](\w*CANCER\w*)["\']'
        ]
        
        for pattern in cell_type_patterns:
            matches = re.findall(pattern, code_content, re.IGNORECASE)
            for match in matches:
                if match and len(match) > 2:  # Filter out very short matches
                    objects.cell_types[match] = {'source': 'pattern_match'}
        
        # Extract parameters with values
        param_patterns = [
            (r'targetVolume\s*=\s*(\d+\.?\d*)', 'targetVolume'),
            (r'lambdaVolume\s*=\s*(\d+\.?\d*)', 'lambdaVolume'),
            (r'neighbor_order\s*=\s*(\d+)', 'neighbor_order'),
            (r'number_of_processors\s*=\s*(\d+)', 'number_of_processors'),
            (r'debug_output_every\s*=\s*(\d+)', 'debug_output_every'),
            (r'frequency\s*=\s*(\d+)', 'frequency'),
            (r'random\(\)\s*<\s*(\d+\.?\d*)', 'probability_threshold'),
            (r'mcs\s*%\s*(\d+)', 'time_modulo')
        ]
        
        for pattern, param_name in param_patterns:
            matches = re.findall(pattern, code_content)
            if matches:
                values = []
                for match in matches:
                    try:
                        values.append(float(match))
                    except ValueError:
                        values.append(match)
                objects.parameters[param_name] = values if len(values) > 1 else values[0]
        
        # Extract plugins
        plugin_patterns = [
            r'(CellTypePlugin|VolumePlugin|ContactPlugin|Metadata)\s*\(',
            r'(\w*Plugin)\s*\('
        ]
        
        for pattern in plugin_patterns:
            matches = re.findall(pattern, code_content)
            for match in matches:
                if match:
                    objects.plugins.append({'type': match, 'source': 'pattern_match'})
        
        # Extract energy matrices
        energy_pattern = r'energy\s*=\s*\{([^}]+)\}'
        energy_matches = re.findall(energy_pattern, code_content, re.DOTALL)
        for match in energy_matches:
            # Parse energy entries
            energy_entries = re.findall(r'["\']([^"\']+)["\']:\s*(\d+)', match)
            for interaction, energy in energy_entries:
                objects.energy_matrices[interaction] = float(energy)
        
        # Extract biological behaviors
        for behavior_type, keywords in self.biological_keywords.items():
            for keyword in keywords:
                if keyword.lower() in code_content.lower():
                    if behavior_type not in objects.behaviors:
                        objects.behaviors[behavior_type] = []
                    
                    # Find context around the keyword
                    lines = code_content.split('\n')
                    for i, line in enumerate(lines):
                        if keyword.lower() in line.lower():
                            context = line.strip()
                            if context:
                                objects.behaviors[behavior_type].append(context)
                    
                    objects.biological_processes.add(behavior_type)
    
    def _determine_api_style(self, objects: CC3DObjects) -> str:
        """Determine whether the code uses modern, legacy, or mixed CC3D APIs"""
        modern_indicators = 0
        legacy_indicators = 0
        
        for import_item in objects.imports:
            for api_type, keywords in self.cc3d_apis.items():
                for keyword in keywords:
                    if keyword in import_item:
                        if api_type == 'modern':
                            modern_indicators += 1
                        elif api_type == 'legacy':
                            legacy_indicators += 1
        
        # Also check in class inheritance and method calls
        for class_info in objects.classes:
            for base in class_info.get('bases', []):
                if 'steppables.SteppableBasePy' in base:
                    modern_indicators += 1
                elif 'SteppableBasePy' in base and 'steppables' not in base:
                    legacy_indicators += 1
        
        if modern_indicators > legacy_indicators:
            return "modern"
        elif legacy_indicators > modern_indicators:
            return "legacy"
        elif modern_indicators > 0 and legacy_indicators > 0:
            return "mixed"
        else:
            return "unknown"
    
    def _ast_to_string(self, node):
        """Convert AST node to string representation"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._ast_to_string(node.value)}.{node.attr}"
        else:
            return str(node)

def discover_experiments(base_path: Path = Path("experiments")) -> Dict[str, List[Path]]:
    """Discover all available experiments and batch folders"""
    
    experiments = {
        "individual_papers": [],
        "batch_folders": [],
        "batch_papers": {}
    }
    
    if not base_path.exists():
        return experiments
    
    for item in base_path.iterdir():
        if not item.is_dir():
            continue
            
        if item.name.startswith("paper_"):
            # Individual paper experiment
            experiments["individual_papers"].append(item)
        elif item.name.startswith("batch_"):
            # Batch folder
            experiments["batch_folders"].append(item)
            
            # Find papers within batch folder
            batch_papers = []
            for sub_item in item.iterdir():
                if sub_item.is_dir() and sub_item.name.startswith("paper_"):
                    batch_papers.append(sub_item)
            
            if batch_papers:
                experiments["batch_papers"][item.name] = batch_papers
    
    return experiments

def analyze_experiment_objects(experiment_dir: Path, num_runs: int = 10) -> Dict[str, Any]:
    """Analyze objects from all runs in an experiment"""
    extractor = CC3DObjectExtractor()
    
    objects_list = []
    run_info = []
    
    for run_num in range(1, num_runs + 1):
        run_dir = experiment_dir / f"run_{run_num}"
        if not run_dir.exists():
            continue
        
        # Extract code from experiment data
        data_file = run_dir / "experiment_data.json"
        if data_file.exists():
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            # Get the final code
            code_content = None
            if 'metadata' in data and 'cc3d_file_creation' in data['metadata']:
                code_content = data['metadata']['cc3d_file_creation']['python_code']
            elif 'llm_responses' in data and len(data['llm_responses']) > 1:
                response = data['llm_responses'][1]['response']
                if '```python' in response:
                    code_content = response.split('```python')[1].split('```')[0].strip()
                elif '```' in response:
                    code_content = response.split('```')[1].split('```')[0].strip()
            
            if code_content:
                objects = extractor.extract_objects(code_content, f"run_{run_num}")
                objects_list.append(objects)
                
                run_info.append({
                    "run": run_num,
                    "api_style": objects.api_style,
                    "num_classes": len(objects.classes),
                    "num_cell_types": len(objects.cell_types),
                    "num_parameters": len(objects.parameters),
                    "num_behaviors": len(objects.biological_processes),
                    "has_syntax_errors": len(objects.syntax_errors) > 0,
                    "syntax_errors": objects.syntax_errors
                })
    
    if len(objects_list) < 2:
        return {"error": "Need at least 2 runs with code to analyze"}
    
    # Simple analysis summary
    analysis = {
        "files_analyzed": len(objects_list),
        "run_info": run_info,
        "experiment_dir": str(experiment_dir),
        "summary": {
            "api_styles": Counter([info["api_style"] for info in run_info]),
            "avg_classes": sum(info["num_classes"] for info in run_info) / len(run_info),
            "avg_cell_types": sum(info["num_cell_types"] for info in run_info) / len(run_info),
            "avg_parameters": sum(info["num_parameters"] for info in run_info) / len(run_info),
            "avg_behaviors": sum(info["num_behaviors"] for info in run_info) / len(run_info),
            "syntax_error_runs": sum(1 for info in run_info if info["has_syntax_errors"])
        }
    }
    
    return analysis

def save_results(results: Dict[str, Any], output_dir: Path = Path("analysis_results")):
    """Save analysis results to files"""
    
    output_dir.mkdir(exist_ok=True)
    
    # Extract experiment name for filename
    exp_name = Path(results["experiment_dir"]).name
    timestamp = exp_name.split("_")[-1] if "_" in exp_name else "unknown"
    
    # Save full results as JSON
    json_file = output_dir / f"{exp_name}_object_analysis.json"
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Save run summary as CSV
    csv_file = output_dir / f"{exp_name}_run_summary.csv"
    try:
        import pandas as pd
        df = pd.DataFrame(results['run_info'])
        df.to_csv(csv_file, index=False)
    except ImportError:
        # Fallback to manual CSV writing if pandas not available
        import csv
        with open(csv_file, 'w', newline='') as f:
            if results['run_info']:
                writer = csv.DictWriter(f, fieldnames=results['run_info'][0].keys())
                writer.writeheader()
                writer.writerows(results['run_info'])
    
    print(f"✓ Results saved:")
    print(f"  JSON: {json_file}")
    print(f"  CSV:  {csv_file}")
    
    return json_file, csv_file

def interactive_mode():
    """Interactive mode for selecting experiments to analyze"""
    
    print("🔍 CC3D Object Analyzer - Interactive Mode")
    print("=" * 50)
    
    # Discover available experiments
    experiments = discover_experiments()
    
    print(f"\n📁 AVAILABLE EXPERIMENTS:")
    
    # Show individual papers
    if experiments["individual_papers"]:
        print(f"\n📄 Individual Papers ({len(experiments['individual_papers'])}):")
        for i, paper in enumerate(experiments["individual_papers"], 1):
            run_count = len([d for d in paper.iterdir() if d.is_dir() and d.name.startswith('run_')])
            print(f"  {i:2d}. {paper.name} ({run_count} runs)")
    
    # Show batch folders
    if experiments["batch_folders"]:
        print(f"\n📦 Batch Folders ({len(experiments['batch_folders'])}):")
        for i, batch in enumerate(experiments["batch_folders"], len(experiments["individual_papers"]) + 1):
            paper_count = len(experiments["batch_papers"].get(batch.name, []))
            print(f"  {i:2d}. {batch.name} ({paper_count} papers)")
    
    # Get user choice
    total_options = len(experiments["individual_papers"]) + len(experiments["batch_folders"])
    
    if total_options == 0:
        print("❌ No experiments found!")
        return
    
    try:
        choice = int(input(f"\nEnter choice (1-{total_options}): "))
        
        if 1 <= choice <= len(experiments["individual_papers"]):
            # Individual paper selected
            selected = experiments["individual_papers"][choice - 1]
            print(f"\n🔍 Analyzing: {selected.name}")
            
            results = analyze_experiment_objects(selected)
            if "error" not in results:
                print_summary(results)
                
                save_choice = input("\nSave results to files? (y/n): ").lower().strip()
                if save_choice == 'y':
                    save_results(results)
            else:
                print(f"❌ Error: {results['error']}")
                
        elif choice <= total_options:
            # Batch folder selected
            batch_idx = choice - len(experiments["individual_papers"]) - 1
            selected_batch = experiments["batch_folders"][batch_idx]
            batch_papers = experiments["batch_papers"].get(selected_batch.name, [])
            
            print(f"\n📦 Analyzing batch: {selected_batch.name}")
            print(f"Found {len(batch_papers)} papers in batch")
            
            # Analyze all papers in batch
            batch_results = {}
            for paper in batch_papers:
                print(f"\n  📄 Analyzing: {paper.name}")
                results = analyze_experiment_objects(paper)
                if "error" not in results:
                    batch_results[paper.name] = results
                    print(f"    ✓ {results['files_analyzed']} runs analyzed")
                else:
                    print(f"    ❌ {results['error']}")
            
            if batch_results:
                print(f"\n📊 BATCH SUMMARY:")
                for paper_name, results in batch_results.items():
                    print(f"  {paper_name}: {results['files_analyzed']} runs")
                
                save_choice = input("\nSave all results to files? (y/n): ").lower().strip()
                if save_choice == 'y':
                    for paper_name, results in batch_results.items():
                        save_results(results)
        else:
            print("❌ Invalid choice!")
            
    except ValueError:
        print("❌ Please enter a valid number!")
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")

def print_summary(results: Dict[str, Any]):
    """Print a summary of analysis results"""
    
    print(f"\n📊 ANALYSIS SUMMARY:")
    print(f"Experiment: {Path(results['experiment_dir']).name}")
    print(f"Runs analyzed: {results['files_analyzed']}")
    
    summary = results['summary']
    print(f"\nAPI Styles: {dict(summary['api_styles'])}")
    print(f"Avg Classes: {summary['avg_classes']:.1f}")
    print(f"Avg Cell Types: {summary['avg_cell_types']:.1f}")
    print(f"Avg Parameters: {summary['avg_parameters']:.1f}")
    print(f"Avg Behaviors: {summary['avg_behaviors']:.1f}")
    print(f"Syntax Errors: {summary['syntax_error_runs']} runs")

def main():
    """Main function with command line arguments"""
    
    parser = argparse.ArgumentParser(description="CC3D Object Analyzer")
    parser.add_argument("--experiment", "-e", type=str, help="Specific experiment directory to analyze")
    parser.add_argument("--batch", "-b", type=str, help="Batch folder to analyze")
    parser.add_argument("--save", "-s", action="store_true", help="Save results to files")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive or len(sys.argv) == 1:
        interactive_mode()
    elif args.experiment:
        experiment_path = Path("experiments") / args.experiment
        if experiment_path.exists():
            print(f"🔍 Analyzing: {experiment_path.name}")
            results = analyze_experiment_objects(experiment_path)
            if "error" not in results:
                print_summary(results)
                if args.save:
                    save_results(results)
            else:
                print(f"❌ Error: {results['error']}")
        else:
            print(f"❌ Experiment not found: {experiment_path}")
    elif args.batch:
        batch_path = Path("experiments") / args.batch
        if batch_path.exists():
            print(f"📦 Analyzing batch: {batch_path.name}")
            # Implementation for batch analysis
        else:
            print(f"❌ Batch folder not found: {batch_path}")

if __name__ == "__main__":
    main()