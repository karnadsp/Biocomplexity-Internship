#!/usr/bin/env python3

"""
Data Flow Explanation - Where results come from and how they're created
"""

import json
from pathlib import Path

def explain_data_flow():
    """Explain the complete data flow from input to object analysis"""
    
    print("🔄 CC3D OBJECT ANALYSIS DATA FLOW")
    print("=" * 60)
    
    print("\n📥 INPUT SOURCES:")
    print("1. Paper abstracts (from CSV files)")
    print("2. Your experimental_code.py system")
    
    print("\n🏗️  EXPERIMENT CREATION PROCESS:")
    print("   Abstract → LLM → Ontology → LLM → CC3D Python Code")
    print("   ↓")
    print("   Stored in: experiments/paper_XX_Name_TIMESTAMP/run_Y/experiment_data.json")
    
    print("\n📁 DATA STORAGE STRUCTURE:")
    print("experiments/")
    print("├── paper_01_Lattice-Based_Model_20250618_160019/")
    print("│   ├── run_1/")
    print("│   │   ├── experiment_data.json  ← MAIN DATA SOURCE")
    print("│   │   └── generated_cc3d_model.cc3d")
    print("│   ├── run_2/")
    print("│   │   ├── experiment_data.json")
    print("│   │   └── generated_cc3d_model.cc3d")
    print("│   └── ... (run_3 to run_10)")
    print("└── paper_02_Using_Mathematical_20250618_160019/")
    print("    └── ... (similar structure)")
    
    print("\n📊 OBJECT ANALYSIS EXTRACTION PROCESS:")
    print("1. cc3d_object_analyzer.py reads experiment_data.json files")
    print("2. Extracts Python code from TWO possible locations:")
    print("   a) metadata.cc3d_file_creation.python_code (preferred)")
    print("   b) llm_responses[1].response (fallback)")
    print("3. Parses Python code using AST and regex patterns")
    print("4. Extracts structured objects (classes, imports, parameters, etc.)")
    print("5. Compares objects across runs")
    
    print("\n🔍 WHAT GETS EXTRACTED:")
    
    # Show example data
    experiment_dir = Path("experiments/paper_01_Lattice-Based_Model_20250618_160019")
    if experiment_dir.exists():
        data_file = experiment_dir / "run_1" / "experiment_data.json"
        if data_file.exists():
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            print(f"\n📄 EXAMPLE FROM RUN 1:")
            print(f"   Input Abstract: {data['inputs']['initial_description']['data']['description'][:100]}...")
            
            if 'llm_responses' in data and len(data['llm_responses']) > 1:
                ontology_response = data['llm_responses'][0]['response']
                print(f"   LLM Ontology: {ontology_response[:100]}...")
                
                code_response = data['llm_responses'][1]['response']
                print(f"   LLM Code: {code_response[:100]}...")
            
            if 'metadata' in data and 'cc3d_file_creation' in data['metadata']:
                final_code = data['metadata']['cc3d_file_creation']['python_code']
                print(f"   Final Code: {final_code[:100]}...")
    
    print("\n⚙️  OBJECT EXTRACTION DETAILS:")
    print("From the Python code, we extract:")
    print("• API Style: modern (cc3d.core.PyCoreSpecs) vs legacy (pybind)")
    print("• Imports: All import statements")
    print("• Classes: Class names, methods, inheritance")
    print("• Cell Types: MAMMARY_EPITHELIAL, EPITHELIAL, etc.")
    print("• Parameters: targetVolume=25, lambdaVolume=2.0, etc.")
    print("• Plugins: CellTypePlugin, VolumePlugin, ContactPlugin")
    print("• Behaviors: proliferation, apoptosis, adhesion, etc.")
    print("• Energy Matrices: Cell-cell interaction energies")
    
    print("\n📈 RESULTS OUTPUT:")
    print("The object analyzer produces:")
    print("• Per-run object summaries")
    print("• Cross-run comparisons")
    print("• Consistency metrics")
    print("• Detailed difference analysis")
    
    print("\n🎯 KEY INSIGHT:")
    print("Instead of comparing raw text similarity (which was ~15-65%),")
    print("we now compare STRUCTURED OBJECTS to understand:")
    print("• Why code is different (API style, parameters, cell types)")
    print("• What specific objects differ between runs")
    print("• Which differences are scientifically meaningful")

def show_specific_extraction_example():
    """Show exactly how one piece of code gets analyzed"""
    
    print("\n" + "="*60)
    print("🔬 SPECIFIC EXTRACTION EXAMPLE")
    print("="*60)
    
    # Sample code from the experiment
    sample_code = '''from cc3d.core.PyCoreSpecs import Metadata, CellTypePlugin, VolumePlugin, ContactPlugin
from cc3d.cpp import CompuCell
import CompuCellSetup
from cc3d import steppables

class EpithelialSimulation(steppables.SteppableBasePy):
    def __init__(self, frequency=1):
        steppables.SteppableBasePy.__init__(self, frequency)
        self.mammary_epithelial = None
        self.epithelial = None

    def start(self):
        self.mammary_epithelial = self.cell_type.MAMMARY_EPITHELIAL
        self.epithelial = self.cell_type.EPITHELIAL
        
        for cell in self.cell_list:
            if cell.type == self.mammary_epithelial:
                cell.targetVolume = 25
                cell.lambdaVolume = 2.0'''
    
    print("📝 SAMPLE CODE:")
    print(sample_code)
    
    print("\n🔍 EXTRACTED OBJECTS:")
    print("API Style: 'modern' (uses cc3d.core.PyCoreSpecs)")
    print("Imports: ['cc3d.core.PyCoreSpecs.Metadata', 'cc3d.core.PyCoreSpecs.CellTypePlugin', ...]")
    print("Classes: [{'name': 'EpithelialSimulation', 'methods': ['__init__', 'start']}]")
    print("Cell Types: {'MAMMARY_EPITHELIAL': {...}, 'EPITHELIAL': {...}}")
    print("Parameters: {'targetVolume': 25.0, 'lambdaVolume': 2.0, 'frequency': 1.0}")
    print("Behaviors: {'growth', 'adhesion'} (detected from keywords)")
    
    print("\n🔄 COMPARISON PROCESS:")
    print("1. Extract objects from Run 1 (modern API, targetVolume=25)")
    print("2. Extract objects from Run 2 (legacy API, targetVolume=40)")
    print("3. Compare:")
    print("   • API Style: modern ≠ legacy → INCONSISTENT")
    print("   • Parameters: targetVolume 25 ≠ 40 → INCONSISTENT")
    print("   • Cell Types: MAMMARY_EPITHELIAL vs MammaryEpithelial → INCONSISTENT")
    
    print("\n💡 SCIENTIFIC INSIGHT:")
    print("These aren't just 'text differences' - they represent:")
    print("• Different CC3D frameworks (incompatible)")
    print("• Different cell sizes (different biology)")
    print("• Different naming conventions (different ontologies)")

if __name__ == "__main__":
    explain_data_flow()
    show_specific_extraction_example()
    
    print("\n" + "="*60)
    print("📍 SUMMARY: WHERE RESULTS COME FROM")
    print("="*60)
    print("INPUT: Paper abstracts → Your experimental_code.py")
    print("STORED: experiments/*/run_*/experiment_data.json")
    print("ANALYZED: cc3d_object_analyzer.py extracts structured objects")
    print("OUTPUT: Object-level comparison showing scientific differences")
    print("\nThis gives you much deeper insight than text similarity!") 