import json
import os
import zipfile
import tempfile
from datetime import datetime
from pathlib import Path
import deepseek
from deepseek import DeepSeekAPI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("project.env")

# Debug prints
print("Current working directory:", os.getcwd())
print("Environment file exists:", os.path.exists("project.env"))
print("DEEPSEEK_API_KEY value:", os.getenv('DEEPSEEK_API_KEY'))

# Initialize the DeepSeek client
client = DeepSeekAPI(api_key=os.getenv('DEEPSEEK_API_KEY'))

class ExperimentLogger:
    def __init__(self, experiment_name):
        self.experiment_name = experiment_name
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.experiment_dir = Path(f"experiments/{experiment_name}_{self.timestamp}")
        self.experiment_dir.mkdir(parents=True, exist_ok=True)
        self.interaction_log = []
        
    def log_interaction(self, step_name, input_data, output_data):
        """Log an interaction with timestamps and metadata"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "input": input_data,
            "output": output_data
        }
        self.interaction_log.append(interaction)
        
        # Save individual interaction to file
        interaction_file = self.experiment_dir / f"{step_name}_{len(self.interaction_log)}.json"
        with open(interaction_file, 'w') as f:
            json.dump(interaction, f, indent=2)
            
    def save_experiment_summary(self):
        """Save complete experiment log"""
        summary_file = self.experiment_dir / "experiment_summary.json"
        with open(summary_file, 'w') as f:
            json.dump({
                "experiment_name": self.experiment_name,
                "timestamp": self.timestamp,
                "interactions": self.interaction_log
            }, f, indent=2)

def get_llm_response(prompt, system_message, logger):
    """Helper function to get response from DeepSeek API"""
    response = client.chat_completion(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
    )
    # The response is already a string, no need to access choices or message
    result = response
    logger.log_interaction("llm_response", 
                         {"prompt": prompt, "system_message": system_message},
                         {"response": result})
    return result

def generate_clarification_questions(description, logger):
    """Generate ontology-focused clarification questions based on the description"""
    system_message = """You are a biological modeling expert. Generate specific clarification questions 
    focusing on Cell Ontology, Gene Ontology (GO), and MeSH terms that would help understand the system better.
    Format your response as a numbered list of questions."""
    
    prompt = f"Based on this biological system description, what clarification questions would help identify relevant ontologies?\n\nDescription: {description}"
    return get_llm_response(prompt, system_message, logger)

def generate_ontology_annotations(description, clarifications, logger):
    """Generate structured ontology-based annotations from the clarifications"""
    system_message = """You are a biological modeling expert. Create structured ontology annotations 
    based on the provided information. Include relevant Cell Ontology, GO, and MeSH terms where applicable.
    Format your response as a JSON object with categories for different ontology types."""
    
    prompt = f"""Original description: {description}\n\nClarifications provided: {clarifications}\n\n
    Please provide structured ontology annotations based on this information."""
    return get_llm_response(prompt, system_message, logger)

def generate_cc3d_starter_code(annotations, logger):
    """Generate CC3D starter code based on the ontology annotations"""
    system_message = """You are a CompuCell3D expert. Generate a valid CompuCell3D simulation file that includes:
    1. Required imports (CompuCellSetup, steppables)
    2. A proper simulation class that inherits from steppables.SteppableBasePy
    3. Required methods (__init__, start, step)
    4. Basic cell types and parameters based on the ontology annotations
    Return ONLY the Python code without any additional text or explanations."""
    
    prompt = f"""Generate a valid CompuCell3D simulation file based on these ontology annotations.
    The code must include all required imports and a proper simulation class structure.
    Return ONLY the Python code:\n\n{annotations}"""
    
    return get_llm_response(prompt, system_message, logger)

def create_cc3d_file(python_code, logger):
    """Create a proper .cc3d file structure"""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the Python simulation file
        sim_file = os.path.join(temp_dir, "Simulation.py")
        with open(sim_file, "w") as f:
            f.write(python_code)
        
        # Create the main configuration file
        config_file = os.path.join(temp_dir, "Simulation.cc3d")
        config_content = """<?xml version="1.0" encoding="UTF-8"?>
<CompuCell3D>
    <Potts>
        <Dimensions x="100" y="100" z="1"/>
        <Steps>1000</Steps>
        <Temperature>10</Temperature>
        <NeighborOrder>2</NeighborOrder>
    </Potts>
    <Plugin Name="Volume">
        <VolumeEnergyParameters CellType="Medium" LambdaVolume="2.0" TargetVolume="25"/>
    </Plugin>
    <Plugin Name="CellType">
        <CellType TypeId="0" TypeName="Medium"/>
    </Plugin>
    <Steppable Type="Python">
        <ModuleName>Simulation</ModuleName>
    </Steppable>
</CompuCell3D>"""
        
        with open(config_file, "w") as f:
            f.write(config_content)
        
        # Create the .cc3d zip file
        output_file = "generated_cc3d_model.cc3d"
        with zipfile.ZipFile(output_file, 'w') as zipf:
            zipf.write(sim_file, "Simulation.py")
            zipf.write(config_file, "Simulation.cc3d")
        
        logger.log_interaction("cc3d_file_creation", 
                             {"python_code": python_code},
                             {"output_file": output_file})
        
        return output_file

def format_for_presentation(experiment_dir):
    """Format experiment data for easy presentation use"""
    # Read the experiment summary
    summary_file = Path(experiment_dir) / "experiment_summary.json"
    with open(summary_file, 'r') as f:
        data = json.load(f)
    
    # Format the output
    output = []
    output.append(f"Experiment: {data['experiment_name']}")
    output.append(f"Date: {data['timestamp']}\n")
    
    # Format each interaction
    for interaction in data['interactions']:
        step = interaction['step']
        if step == 'initial_description':
            output.append("Initial Description:")
            output.append(f"- {interaction['output']['description']}\n")
        elif step == 'llm_response':
            if 'ontology annotations' in interaction['input']['prompt'].lower():
                output.append("Ontology Annotations:")
                # Clean up the JSON response
                response = interaction['output']['response']
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0].strip()
                try:
                    annotations = json.loads(response)
                    for category, items in annotations.items():
                        if items:  # Only show non-empty categories
                            output.append(f"\n{category}:")
                            if isinstance(items, list):
                                for item in items:
                                    if 'CellOntology' in item:
                                        output.append(f"- {item['CellOntology']['label']} (ID: {item['CellOntology']['id']})")
                                    elif 'id' in item:
                                        output.append(f"- {item['label']} (ID: {item['id']})")
                            elif isinstance(items, dict):
                                for subcat, subitems in items.items():
                                    if subitems:
                                        output.append(f"  {subcat}:")
                                        for subitem in subitems:
                                            output.append(f"  - {subitem}")
                except json.JSONDecodeError:
                    output.append(response)
                output.append("")
        elif step == 'clarifications':
            output.append("Clarifications Provided:")
            output.append(f"- {interaction['output']['answers']}\n")
    
    return "\n".join(output)

def main():
    print("Welcome to the Biological System Modeling Assistant!")
    
    # Initialize experiment logger
    experiment_name = input("Enter a name for this experiment: ")
    logger = ExperimentLogger(experiment_name)
    
    print("\nPlease provide a description of the biological system you wish to model:")
    description = input("> ")
    logger.log_interaction("initial_description", {}, {"description": description})
    
    print("\nGenerating clarification questions...")
    questions = generate_clarification_questions(description, logger)
    print("\nPlease answer these clarification questions:")
    print(questions)
    
    clarifications = input("\nEnter your clarifications:\n> ")
    logger.log_interaction("clarifications", {"questions": questions}, {"answers": clarifications})
    
    print("\nGenerating ontology annotations...")
    annotations = generate_ontology_annotations(description, clarifications, logger)
    print("\nGenerated annotations:")
    print(annotations)
    
    print("\nGenerating CC3D starter code...")
    cc3d_code = generate_cc3d_starter_code(annotations, logger)
    
    # Clean up the code by removing any markdown code block markers
    cc3d_code = cc3d_code.replace("```python", "").replace("```", "").strip()
    
    # Ensure the code has the basic required structure
    if "from cc3d.core.PySteppables import *" not in cc3d_code:
        cc3d_code = "from cc3d.core.PySteppables import *\n\n" + cc3d_code
    
    print("\nGenerated CC3D starter code:")
    print(cc3d_code)
    
    # Create and save the .cc3d file
    output_file = create_cc3d_file(cc3d_code, logger)
    print(f"\nCC3D simulation has been saved to '{output_file}'")
    
    # Save complete experiment summary
    logger.save_experiment_summary()
    print(f"\nExperiment summary has been saved to '{logger.experiment_dir}/experiment_summary.json'")
    
    # Format and save presentation-ready output
    presentation_text = format_for_presentation(logger.experiment_dir)
    presentation_file = logger.experiment_dir / "presentation_ready.txt"
    with open(presentation_file, 'w') as f:
        f.write(presentation_text)
    print(f"\nPresentation-ready format has been saved to '{presentation_file}'")

if __name__ == "__main__":
    main() 