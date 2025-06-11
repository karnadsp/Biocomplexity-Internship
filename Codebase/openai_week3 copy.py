import openai
import json
import fitz  # PyMuPDF
import os
import time


openai.api_key = ''

# def ask_llm(prompt, model="gpt-4", temperature=0.7):
#     response = openai.chat.completions.create(

#         model=model,
#         messages=[{"role": "user", "content": prompt}],
#         temperature=temperature
#     )
#     return response['choices'][0]['message']['content'].strip()

def ask_llm(prompt, model="gpt-4", temperature=0.7):
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    return response.choices[0].message.content.strip()

def extract_text_from_pdf(pdf_path, max_chars=3000):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
        if len(full_text) >= max_chars:
            break
    doc.close()
    return full_text[:max_chars]

def get_clarification_questions(description):
    prompt = f"""
You are a biomedical modeling assistant. Based on this biological system description, generate clarifying questions to identify:

- Cell types (Cell Ontology)
- Biological processes (GO)
- Diseases or physiological context (MeSH)
- Physical parameters (e.g., cell adhesion, volume, diffusion rate)

Description:
\"\"\"{description}\"\"\"

Return questions as a numbered list.
"""
    return ask_llm(prompt)

def simulate_user_answers():
    # Replace with real input if available
    return """
1. Epithelial cells and fibroblasts  
2. Wound healing and cell migration  
3. Skin tissue under mechanical stress  
4. Adhesion: moderate; Diffusion: 0.01 µm²/s; Volume: 250 units  
"""

def get_ontology_annotations(description, clarifications):
    prompt = f"""
Based on the description and clarifications below, return a JSON object with the following fields:

- cell_types (Cell Ontology)
- processes (Gene Ontology)
- context (MeSH terms)
- parameters (e.g., adhesion, volume, diffusion)

Description:
\"\"\"{description}\"\"\"

Clarifications:
\"\"\"{clarifications}\"\"\"
"""
    response = ask_llm(prompt)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        print("⚠️ Failed to parse JSON. Raw output below:\n")
        print(response)
        return {}

# def generate_cc3d_code(ontology_json):
#     prompt = f"""
# You are a CompuCell3D simulation assistant. Based on the following ontology annotations:

# {json.dumps(ontology_json, indent=2)}

# Generate the following four files in correct CompuCell3D format:

# 1. A `.cc3d` project file that includes:
#     - `<XMLScript>` tag pointing to `Simulation/auto_model.xml`
#     - `<PythonScript>` tag pointing to `Simulation/auto_model.py`
#     - `<Resource>` tag pointing to `Simulation/auto_model_steppables.py`

# 2. `auto_model.xml` — a CompuCell3D XML file with:
#     - Dimensions
#     - Potts settings
#     - CellType and Contact plugins with example energies
#     - A basic UniformInitializer

# 3. `auto_model.py` — Python file that:
#     - Imports CompuCellSetup
#     - Registers `AutoModelSteppable` from the steppables file
#     - Runs the simulation

# 4. `auto_model_steppables.py` — Python file that:
#     - Imports `SteppableBasePy`
#     - Implements `AutoModelSteppable` with `start()` and `step()` methods
#     - In `step()`, prints a few cell IDs and stops the simulation after some MCS

# Return the files using these delimiters:
# ---START CC3D---
# <cc3d file here>
# ---END CC3D---
# ---START XML---
# <xml file here>
# ---END XML---
# ---START PYTHON MAIN---
# <main Python file here>
# ---END PYTHON MAIN---
# ---START PYTHON STEPPABLE---
# <steppables Python file here>
# ---END PYTHON STEPPABLE---
# """
#     return ask_llm(prompt)

def generate_cc3d_code(ontology_json):
    prompt = f"""
You are a CompuCell3D simulation assistant. Based on the following ontology annotations:

{json.dumps(ontology_json, indent=2)}

Generate four files for a working simulation:

1. `.cc3d` file:
   - Use `Type="XML"` and `Type="Python"` only (NOT "XMLScript" or "PythonScript")
   - References `auto_model.xml`, `auto_model.py`, and `auto_modelSteppables` (as a Python module)
   - Use <Resource Type="Python" Module="auto_modelSteppables"/>

2. `auto_model.xml` (CompuCell3D XML):
   - <Metadata> with <DebugOutput Frequency="10"/>
   - <Potts> block with Dimensions x=100 y=100 z=1 and <Temperature>10.0</Temperature>
   - <Plugin Name="CellType"> with Medium (ID 0), Epithelial (ID 1), Fibroblast (ID 2)
   - <Volume> plugin with:
       <TargetVolume>250</TargetVolume>
       <LambdaVolume>2.0</LambdaVolume>
   - <Contact> plugin with EnergyMatrix for all six pairings
   - <Steppable Type="UniformInitializer"> block with:
       <Box Corner="0 0 0" Dimensions="100 100 1"/>
       <Types>Epithelial Fibroblast</Types>

3. `auto_model.py`:
   - Import from `cc3d`
   - Import `AutoModelSteppable` with: `from auto_modelSteppables import AutoModelSteppable`
   - Register and run the steppable

4. `auto_modelSteppables.py`:
   - Define `AutoModelSteppable(SteppableBasePy)`
   - `start()` prints "Simulation started"
   - `step(mcs)` prints MCS and cell ID/type
   - Stops at mcs == 200 with `self.stop_simulation()`
   - `on_stop()` prints "Simulation stopped" with try/except block

Return the files using these delimiters (no extra markdown or formatting):

---START CC3D---
<cc3d file here>
---END CC3D---
---START XML---
<xml file here>
---END XML---
---START PYTHON MAIN---
<main Python file here>
---END PYTHON MAIN---
---START PYTHON STEPPABLE---
<steppables Python file here>
---END PYTHON STEPPABLE---
"""
    return ask_llm(prompt)





def save_output(output_str, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(output_str)

if __name__ == "__main__":
    pdf_path = input("Enter the name of the PDF file (e.g., paper1.pdf): ").strip()
    paper_id = os.path.splitext(os.path.basename(pdf_path))[0]

    overall_start = time.time()

    for i in range(1, 11):
        print(f"\n🚀 Run {i} for {pdf_path}")
        run_start = time.time()

        description = extract_text_from_pdf(pdf_path)

        print(f"\n=== Step 1 (Run {i}): Clarification Questions ===")
        questions = get_clarification_questions(description)
        save_output(questions, f"outputs/{paper_id}_questions_{i}.txt")

        clarifications = simulate_user_answers()

        print(f"\n=== Step 2 (Run {i}): Ontology Annotation ===")
        ontology = get_ontology_annotations(description, clarifications)

        print(f"\n=== Step 3 (Run {i}): CC3D Code Generation ===")
        code = generate_cc3d_code(ontology)
        save_output(code, f"outputs/{paper_id}_generated_code_{i}.txt")

        run_end = time.time()
        print(f"✅ Run {i} completed in {run_end - run_start:.2f} seconds")

    overall_end = time.time()
    print(f"\n🎉 All 10 runs completed in {overall_end - overall_start:.2f} seconds")


