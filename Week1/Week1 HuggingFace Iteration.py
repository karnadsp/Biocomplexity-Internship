import requests
import json
import fitz  # PyMuPDF

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
headers = {"Authorization": "Bearer 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"}

def query_huggingface(prompt, temperature=0.7, max_tokens=1024):
    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": temperature,
            "max_new_tokens": max_tokens,
            "return_full_text": False
        }
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    return result[0]["generated_text"].strip() if isinstance(result, list) else result["generated_text"].strip()

def load_pdf_text(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

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
    return query_huggingface(prompt)

def simulate_user_answers():
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
    raw_output = query_huggingface(prompt)
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        print("Could not parse JSON. Raw output below:")
        print(raw_output)
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
    return query_huggingface(prompt, max_tokens=2048)

def save_output(text, path):
    with open(path, "w") as f:
        f.write(text)

if __name__ == "__main__":
    desc_path = "paper1.pdf"  # 📄 replace with your actual PDF path
    description = load_pdf_text(desc_path)

    print("\n=== Step 1: Clarification Questions ===")
    questions = get_clarification_questions(description)
    print(questions)

    print("\n=== Step 2: Simulated User Answers ===")
    clarifications = simulate_user_answers()
    print(clarifications)

    print("\n=== Step 3: Ontology Annotation ===")
    annotations = get_ontology_annotations(description, clarifications)
    print(json.dumps(annotations, indent=2))

    print("\n=== Step 4: Generate CC3D Code ===")
    code = generate_cc3d_code(annotations)
    print(code)

    save_output(code, "outputs/cc3d_generated_code.txt")
    print("Saved to outputs/cc3d_generated_code.txt")
