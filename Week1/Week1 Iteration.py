import openai
import json
import fitz  # PyMuPDF
import os
from PIL import Image
import base64
from io import BytesIO

# Initialize OpenAI client with API key
client = openai.OpenAI(api_key='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')

def encode_image_to_base64(image_path):
    with Image.open(image_path) as img:
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

def ask_llm(prompt, model="gpt-4", temperature=0.7, image_path=None):
    messages = [{"role": "user", "content": prompt}]
    
    if image_path:
        base64_image = encode_image_to_base64(image_path)
        messages[0]["content"] = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }
            }
        ]
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
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

def get_system_description():
    print("\n=== Step 1: System Description ===")
    print("Please provide a description of the biological system you want to model.")
    print("You can either:")
    print("1. Enter a text description")
    print("2. Provide a path to an image file")
    print("3. Provide a path to a PDF file")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice == "1":
        return input("\nEnter your description: ").strip()
    elif choice == "2":
        image_path = input("\nEnter path to image file: ").strip()
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        return image_path
    elif choice == "3":
        pdf_path = input("\nEnter path to PDF file: ").strip()
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        return extract_text_from_pdf(pdf_path)
    else:
        raise ValueError("Invalid choice. Please enter 1, 2, or 3.")

def get_clarification_questions(description, is_image=False):
    prompt = f"""
You are a biomedical modeling assistant. Based on this biological system description, generate clarifying questions to identify:

1. Cell types (using Cell Ontology terms)
2. Biological processes (using Gene Ontology terms)
3. Diseases or physiological context (using MeSH terms)
4. Key physical parameters (e.g., cell adhesion, volume, diffusion rate)

Description:
\"\"\"{description}\"\"\"

Return questions as a numbered list, focusing specifically on ontology terms and parameters.
"""
    return ask_llm(prompt, image_path=description if is_image else None)

def get_user_clarifications(questions):
    print("\n=== Step 2: Clarification Questions ===")
    print("Please provide clarifications for the following questions:")
    print(questions)
    print("\nEnter your clarifications (press Enter twice to finish):")
    
    clarifications = []
    current_input = []
    
    while True:
        line = input()
        if line == "" and current_input:
            clarifications.append("\n".join(current_input))
            current_input = []
            if len(clarifications) >= len(questions.split("\n")):
                break
        elif line:
            current_input.append(line)
    
    return "\n\n".join(clarifications)

def get_ontology_annotations(description, clarifications, is_image=False):
    prompt = f"""
Based on the description and clarifications below, return a JSON object with the following fields:

- cell_types: List of Cell Ontology terms
- processes: List of Gene Ontology terms
- context: List of MeSH terms
- parameters: Dictionary of key physical parameters

Description:
\"\"\"{description}\"\"\"

Clarifications:
\"\"\"{clarifications}\"\"\"
"""
    response = ask_llm(prompt, image_path=description if is_image else None)
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
    try:
        # Get system description
        description = get_system_description()
        is_image = isinstance(description, str) and os.path.isfile(description) and description.lower().endswith(('.png', '.jpg', '.jpeg'))
        
        # Get clarification questions
        questions = get_clarification_questions(description, is_image)
        
        # Get user clarifications
        clarifications = get_user_clarifications(questions)
        
        # Get ontology annotations
        print("\n=== Step 3: Ontology Annotation ===")
        ontology = get_ontology_annotations(description, clarifications, is_image)
        print(json.dumps(ontology, indent=2))
        
        # Generate CC3D code
        print("\n=== Step 4: Generate CC3D Code ===")
        code = generate_cc3d_code(ontology)
        
        # Save output
        output_name = "system_description" if not is_image else os.path.splitext(os.path.basename(description))[0]
        output_path = f"outputs/{output_name}_generated_code.txt"
        save_output(code, output_path)
        print(f"Code saved to {output_path}")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please try again with valid input.")
