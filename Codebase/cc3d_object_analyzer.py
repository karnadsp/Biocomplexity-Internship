#!/usr/bin/env python3

"""
CC3D Object Analyzer - Extract and compare objects/components from CC3D model files
"""

import ast
import re
import json
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

class CC3DObjectComparator:
    """Compare objects extracted from multiple CC3D files"""
    
    def compare_objects(self, objects_list: List[CC3DObjects]) -> Dict[str, Any]:
        """Compare objects across multiple CC3D files"""
        if len(objects_list) < 2:
            return {"error": "Need at least 2 objects to compare"}
        
        comparison = {
            "files_analyzed": len(objects_list),
            "api_styles": self._analyze_api_styles(objects_list),
            "imports": self._compare_imports(objects_list),
            "classes": self._compare_classes(objects_list),
            "cell_types": self._compare_cell_types(objects_list),
            "parameters": self._compare_parameters(objects_list),
            "plugins": self._compare_plugins(objects_list),
            "behaviors": self._compare_behaviors(objects_list),
            "energy_matrices": self._compare_energy_matrices(objects_list),
            "consistency_summary": {}
        }
        
        # Calculate overall consistency metrics
        comparison["consistency_summary"] = self._calculate_consistency_metrics(comparison)
        
        return comparison
    
    def _analyze_api_styles(self, objects_list: List[CC3DObjects]) -> Dict[str, Any]:
        """Analyze API style consistency"""
        styles = [obj.api_style for obj in objects_list]
        style_counts = Counter(styles)
        
        return {
            "style_distribution": dict(style_counts),
            "most_common_style": style_counts.most_common(1)[0] if style_counts else ("unknown", 0),
            "is_consistent": len(style_counts) == 1,
            "consistency_percentage": max(style_counts.values()) / len(styles) if styles else 0
        }
    
    def _compare_imports(self, objects_list: List[CC3DObjects]) -> Dict[str, Any]:
        """Compare import statements across files"""
        all_imports = set()
        import_frequency = defaultdict(int)
        
        for obj in objects_list:
            for imp in obj.imports:
                all_imports.add(imp)
                import_frequency[imp] += 1
        
        total_files = len(objects_list)
        consistent_imports = {imp: freq for imp, freq in import_frequency.items() if freq == total_files}
        inconsistent_imports = {imp: freq for imp, freq in import_frequency.items() if freq < total_files}
        
        return {
            "total_unique_imports": len(all_imports),
            "consistent_imports": consistent_imports,
            "inconsistent_imports": inconsistent_imports,
            "consistency_percentage": len(consistent_imports) / len(all_imports) if all_imports else 0
        }
    
    def _compare_classes(self, objects_list: List[CC3DObjects]) -> Dict[str, Any]:
        """Compare class definitions across files"""
        all_classes = set()
        class_frequency = defaultdict(int)
        method_analysis = defaultdict(lambda: defaultdict(int))
        
        for obj in objects_list:
            for class_info in obj.classes:
                class_name = class_info['name']
                all_classes.add(class_name)
                class_frequency[class_name] += 1
                
                # Analyze methods within classes
                for method in class_info.get('methods', []):
                    method_analysis[class_name][method['name']] += 1
        
        total_files = len(objects_list)
        
        return {
            "total_unique_classes": len(all_classes),
            "class_frequency": dict(class_frequency),
            "consistent_classes": {cls: freq for cls, freq in class_frequency.items() if freq == total_files},
            "method_consistency": {cls: {method: freq for method, freq in methods.items()} 
                                 for cls, methods in method_analysis.items()},
            "has_steppable_class": any(len(obj.steppables) > 0 for obj in objects_list)
        }
    
    def _compare_cell_types(self, objects_list: List[CC3DObjects]) -> Dict[str, Any]:
        """Compare cell types across files"""
        all_cell_types = set()
        cell_type_frequency = defaultdict(int)
        
        for obj in objects_list:
            for cell_type in obj.cell_types.keys():
                all_cell_types.add(cell_type)
                cell_type_frequency[cell_type] += 1
        
        total_files = len(objects_list)
        
        return {
            "total_unique_cell_types": len(all_cell_types),
            "cell_type_frequency": dict(cell_type_frequency),
            "consistent_cell_types": {ct: freq for ct, freq in cell_type_frequency.items() if freq == total_files},
            "inconsistent_cell_types": {ct: freq for ct, freq in cell_type_frequency.items() if freq < total_files},
            "consistency_percentage": len([ct for ct, freq in cell_type_frequency.items() if freq == total_files]) / len(all_cell_types) if all_cell_types else 0
        }
    
    def _compare_parameters(self, objects_list: List[CC3DObjects]) -> Dict[str, Any]:
        """Compare parameters across files"""
        all_parameters = set()
        parameter_values = defaultdict(list)
        
        for obj in objects_list:
            for param, value in obj.parameters.items():
                all_parameters.add(param)
                parameter_values[param].append(value)
        
        parameter_analysis = {}
        for param, values in parameter_values.items():
            unique_values = list(set(str(v) for v in values))  # Convert to string for comparison
            parameter_analysis[param] = {
                "values": values,
                "unique_values": unique_values,
                "is_consistent": len(unique_values) == 1,
                "frequency": len(values),
                "consistency_percentage": max(Counter(str(v) for v in values).values()) / len(values) if values else 0
            }
        
        return {
            "total_unique_parameters": len(all_parameters),
            "parameter_analysis": parameter_analysis,
            "consistent_parameters": {p: analysis for p, analysis in parameter_analysis.items() if analysis["is_consistent"]},
            "inconsistent_parameters": {p: analysis for p, analysis in parameter_analysis.items() if not analysis["is_consistent"]}
        }
    
    def _compare_plugins(self, objects_list: List[CC3DObjects]) -> Dict[str, Any]:
        """Compare plugins used across files"""
        all_plugins = set()
        plugin_frequency = defaultdict(int)
        
        for obj in objects_list:
            for plugin in obj.plugins:
                plugin_type = plugin['type']
                all_plugins.add(plugin_type)
                plugin_frequency[plugin_type] += 1
        
        total_files = len(objects_list)
        
        return {
            "total_unique_plugins": len(all_plugins),
            "plugin_frequency": dict(plugin_frequency),
            "consistent_plugins": {p: freq for p, freq in plugin_frequency.items() if freq == total_files},
            "inconsistent_plugins": {p: freq for p, freq in plugin_frequency.items() if freq < total_files}
        }
    
    def _compare_behaviors(self, objects_list: List[CC3DObjects]) -> Dict[str, Any]:
        """Compare biological behaviors across files"""
        all_behaviors = set()
        behavior_frequency = defaultdict(int)
        
        for obj in objects_list:
            for behavior in obj.biological_processes:
                all_behaviors.add(behavior)
                behavior_frequency[behavior] += 1
        
        total_files = len(objects_list)
        
        return {
            "total_unique_behaviors": len(all_behaviors),
            "behavior_frequency": dict(behavior_frequency),
            "consistent_behaviors": {b: freq for b, freq in behavior_frequency.items() if freq == total_files},
            "inconsistent_behaviors": {b: freq for b, freq in behavior_frequency.items() if freq < total_files},
            "consistency_percentage": len([b for b, freq in behavior_frequency.items() if freq == total_files]) / len(all_behaviors) if all_behaviors else 1.0
        }
    
    def _compare_energy_matrices(self, objects_list: List[CC3DObjects]) -> Dict[str, Any]:
        """Compare energy matrix configurations"""
        all_interactions = set()
        energy_values = defaultdict(list)
        
        for obj in objects_list:
            for interaction, energy in obj.energy_matrices.items():
                all_interactions.add(interaction)
                energy_values[interaction].append(energy)
        
        energy_analysis = {}
        for interaction, values in energy_values.items():
            unique_values = list(set(values))
            energy_analysis[interaction] = {
                "values": values,
                "unique_values": unique_values,
                "is_consistent": len(unique_values) == 1,
                "mean_value": sum(values) / len(values) if values else 0,
                "frequency": len(values)
            }
        
        return {
            "total_unique_interactions": len(all_interactions),
            "energy_analysis": energy_analysis,
            "consistent_energies": {i: analysis for i, analysis in energy_analysis.items() if analysis["is_consistent"]},
            "inconsistent_energies": {i: analysis for i, analysis in energy_analysis.items() if not analysis["is_consistent"]}
        }
    
    def _calculate_consistency_metrics(self, comparison: Dict[str, Any]) -> Dict[str, float]:
        """Calculate overall consistency metrics"""
        metrics = {}
        
        # API consistency
        metrics["api_consistency"] = comparison["api_styles"]["consistency_percentage"]
        
        # Import consistency
        metrics["import_consistency"] = comparison["imports"]["consistency_percentage"]
        
        # Cell type consistency  
        metrics["cell_type_consistency"] = comparison["cell_types"]["consistency_percentage"]
        
        # Behavior consistency
        metrics["behavior_consistency"] = comparison["behaviors"]["consistency_percentage"]
        
        # Parameter consistency (average of consistent parameters)
        param_consistencies = [analysis["consistency_percentage"] 
                             for analysis in comparison["parameters"]["parameter_analysis"].values()]
        metrics["parameter_consistency"] = sum(param_consistencies) / len(param_consistencies) if param_consistencies else 0
        
        # Overall consistency (weighted average)
        weights = {
            "api_consistency": 0.3,
            "import_consistency": 0.2,
            "cell_type_consistency": 0.2,
            "behavior_consistency": 0.2,
            "parameter_consistency": 0.1
        }
        
        metrics["overall_consistency"] = sum(metrics[key] * weight for key, weight in weights.items())
        
        return metrics

def analyze_experiment_objects(experiment_dir: Path, num_runs: int = 10) -> Dict[str, Any]:
    """Analyze objects from all runs in an experiment"""
    extractor = CC3DObjectExtractor()
    comparator = CC3DObjectComparator()
    
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
    
    # Perform comparison
    comparison = comparator.compare_objects(objects_list)
    comparison["run_info"] = run_info
    comparison["experiment_dir"] = str(experiment_dir)
    
    return comparison

if __name__ == "__main__":
    # Test with existing experiment
    experiment_dir = Path("experiments/paper_01_Lattice-Based_Model_20250618_160019")
    if experiment_dir.exists():
        print("Analyzing CC3D Objects in Experiment...")
        print("=" * 50)
        
        results = analyze_experiment_objects(experiment_dir)
        
        if "error" not in results:
            print(f"Analyzed {results['files_analyzed']} runs")
            print(f"\nAPI Style Distribution:")
            for style, count in results['api_styles']['style_distribution'].items():
                print(f"  {style}: {count} files")
            
            print(f"\nCell Type Consistency:")
            print(f"  Consistent: {len(results['cell_types']['consistent_cell_types'])} types")
            print(f"  Inconsistent: {len(results['cell_types']['inconsistent_cell_types'])} types")
            
            print(f"\nOverall Consistency Metrics:")
            for metric, value in results['consistency_summary'].items():
                print(f"  {metric}: {value:.1%}")
        else:
            print(f"Error: {results['error']}")
    else:
        print("Experiment directory not found") 