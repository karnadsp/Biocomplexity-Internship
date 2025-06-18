
import json
import os
import zipfile
import tempfile
from datetime import datetime
from pathlib import Path
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("project.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

class ExperimentLogger:
    def __init__(self, experiment_name):
        self.experiment_name = experiment_name
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.experiment_dir = Path(f"experiments/{experiment_name}_{self.timestamp}")
        self.experiment_dir.mkdir(parents=True, exist_ok=True)
        self.interaction_log = []
        
    def log_interaction(self, step_name, input_data, output_data):
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "input": input_data,
            "output": output_data
        }
        self.interaction_log.append(interaction)
        interaction_file = self.experiment_dir / f"{step_name}_{len(self.interaction_log)}.json"
        with open(interaction_file, 'w') as f:
            json.dump(interaction, f, indent=2)
            
    def save_experiment_summary(self):
        summary_file = self.experiment_dir / "experiment_summary.json"
        with open(summary_file, 'w') as f:
            json.dump({
                "experiment_name": self.experiment_name,
                "timestamp": self.timestamp,
                "interactions": self.interaction_log
            }, f, indent=2)

def get_llm_response(prompt, system_message, logger):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    result = response['choices'][0]['message']['content'].strip()
    logger.log_interaction("llm_response", {"prompt": prompt, "system_message": system_message}, {"response": result})
    return result

def generate_clarification_questions(description, logger):
    system_message = "You are a biological modeling expert. Generate specific clarification questions focusing on Cell Ontology, Gene Ontology (GO), and MeSH terms that would help understand the system better. Format your response as a numbered list of questions."
    prompt = f"Based on this biological system description, what clarification questions would help identify relevant ontologies?\n\nDescription: {description}"
    return get_llm_response(prompt, system_message, logger)

def generate_ontology_annotations(description, clarifications, logger):
    system_message = "You are a biological modeling expert. Create structured ontology annotations based on the provided information. Include relevant Cell Ontology, GO, and MeSH terms where applicable. Format your response as a JSON object with categories for different ontology types."
    prompt = f"Original description: {description}\n\nClarifications provided: {clarifications}\n\nPlease provide structured ontology annotations based on this information."
    return get_llm_response(prompt, system_message, logger)

def generate_cc3d_starter_code(annotations, logger):
    system_message = "You are a CompuCell3D expert. Generate a valid CompuCell3D simulation file that includes: 1. Required imports (CompuCellSetup, steppables), 2. A proper simulation class that inherits from steppables.SteppableBasePy, 3. Required methods (__init__, start, step), 4. Basic cell types and parameters based on the ontology annotations. Return ONLY the Python code without any additional text or explanations."
    prompt = f"Generate a valid CompuCell3D simulation file based on these ontology annotations. The code must include all required imports and a proper simulation class structure. Return ONLY the Python code:\n\n{annotations}"
    return get_llm_response(prompt, system_message, logger)

def create_cc3d_file(python_code, logger):
    with tempfile.TemporaryDirectory() as temp_dir:
        sim_file = os.path.join(temp_dir, "Simulation.py")
        with open(sim_file, "w") as f:
            f.write(python_code)
        
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
        
        output_file = "generated_cc3d_model.cc3d"
        with zipfile.ZipFile(output_file, 'w') as zipf:
            zipf.write(sim_file, "Simulation.py")
            zipf.write(config_file, "Simulation.cc3d")
        
        logger.log_interaction("cc3d_file_creation", {"python_code": python_code}, {"output_file": output_file})
        return output_file

def main():
    print("Welcome to the Biological System Modeling Assistant!")
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
    cc3d_code = cc3d_code.replace("```python", "").replace("```", "").strip()
    
    if "from cc3d.core.PySteppables import *" not in cc3d_code:
        cc3d_code = "from cc3d.core.PySteppables import *\n\n" + cc3d_code
    
    print("\nGenerated CC3D starter code:")
    print(cc3d_code)
    
    output_file = create_cc3d_file(cc3d_code, logger)
    print(f"\nCC3D simulation has been saved to '{output_file}'")
    
    logger.save_experiment_summary()
    print(f"\nExperiment summary has been saved to '{logger.experiment_dir}/experiment_summary.json'")

if __name__ == "__main__":
    main()
