import openai
import json
import fitz  # PyMuPDF
import os

openai.api_key = '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'

def ask_llm(prompt, model="gpt-4", temperature=0.7):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    return response['choices'][0]['message']['content'].strip()

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

def generate_cc3d_code(ontology_json):
    prompt = f"""
You are a CC3D model assistant. Generate starter CompuCell3D XML and Python code using these annotations:

{json.dumps(ontology_json, indent=2)}

Keep it minimal but syntactically valid. Return:
---START XML---
[XML code here]
---END XML---
---START PYTHON---
[Python code here]
---END PYTHON---
"""
    return ask_llm(prompt)

def save_output(output_str, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(output_str)

if __name__ == "__main__":
    pdf_path = desc_path = input("Enter path to your PDF file: ").strip()
    print(f"\nExtracting text from {pdf_path}...")
    description = extract_text_from_pdf(pdf_path)

    print("\n=== Step 1: Clarification Questions ===")
    questions = get_clarification_questions(description)
    print(questions)

    print("\n=== Step 2: Simulated Clarifications ===")
    clarifications = simulate_user_answers()
    print(clarifications)

    print("\n=== Step 3: Ontology Annotation ===")
    ontology = get_ontology_annotations(description, clarifications)
    print(json.dumps(ontology, indent=2))

    print("\n=== Step 4: Generate CC3D Code ===")
    code = generate_cc3d_code(ontology)
    save_output(code, "outputs/paper1_generated_code.txt")
    print("Code saved to outputs/paper1_generated_code.txt")
