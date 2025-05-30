import openai
import json
from openai import OpenAI
import os
import zipfile
import tempfile

# Initialize the OpenAI client
client = OpenAI(api_key='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')

def get_llm_response(prompt, system_message):
    """Helper function to get response from OpenAI API"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def generate_clarification_questions(description):
    """Generate ontology-focused clarification questions based on the description"""
    system_message = """You are a biological modeling expert. Generate specific clarification questions 
    focusing on Cell Ontology, Gene Ontology (GO), and MeSH terms that would help understand the system better.
    Format your response as a numbered list of questions."""
    
    prompt = f"Based on this biological system description, what clarification questions would help identify relevant ontologies?\n\nDescription: {description}"
    return get_llm_response(prompt, system_message)

def generate_ontology_annotations(description, clarifications):
    """Generate structured ontology-based annotations from the clarifications"""
    system_message = """You are a biological modeling expert. Create structured ontology annotations 
    based on the provided information. Include relevant Cell Ontology, GO, and MeSH terms where applicable.
    Format your response as a JSON object with categories for different ontology types."""
    
    prompt = f"""Original description: {description}\n\nClarifications provided: {clarifications}\n\n
    Please provide structured ontology annotations based on this information."""
    return get_llm_response(prompt, system_message)

def generate_cc3d_starter_code(annotations):
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
    
    return get_llm_response(prompt, system_message)

def create_cc3d_file(python_code):
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
        
        return output_file

def main():
    print("Welcome to the Biological System Modeling Assistant!")
    print("\nPlease provide a description of the biological system you wish to model:")
    description = input("> ")
    
    print("\nGenerating clarification questions...")
    questions = generate_clarification_questions(description)
    print("\nPlease answer these clarification questions:")
    print(questions)
    
    clarifications = input("\nEnter your clarifications:\n> ")
    
    print("\nGenerating ontology annotations...")
    annotations = generate_ontology_annotations(description, clarifications)
    print("\nGenerated annotations:")
    print(annotations)
    
    print("\nGenerating CC3D starter code...")
    cc3d_code = generate_cc3d_starter_code(annotations)
    
    # Clean up the code by removing any markdown code block markers
    cc3d_code = cc3d_code.replace("```python", "").replace("```", "").strip()
    
    # Ensure the code has the basic required structure
    if "from cc3d.core.PySteppables import *" not in cc3d_code:
        cc3d_code = "from cc3d.core.PySteppables import *\n\n" + cc3d_code
    
    print("\nGenerated CC3D starter code:")
    print(cc3d_code)
    
    # Create and save the .cc3d file
    output_file = create_cc3d_file(cc3d_code)
    print(f"\nCC3D simulation has been saved to '{output_file}'")

if __name__ == "__main__":
    main() 