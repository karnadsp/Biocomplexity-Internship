import openai
openai.api_key = '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'
import json

# Function to prompt user for a natural-language description
def get_user_input():
    description = input("Describe the biological system you wish to model: ")
    return description

# Function to call LLM API to generate ontology-focused clarification questions
def generate_clarification_questions(description):
    prompt = f"Given the biological system description: '{description}', generate ontology-focused clarification questions covering Cell Ontology, GO terms, MeSH terms, and key parameters."
    
    response = openai.ChatCompletion.create(
        model="gpt-4.1",
        messages=[{"role": "system", "content": "You are an assistant helping to annotate biological models."},
                  {"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

# Function to capture user responses to clarification questions
def get_clarifications(questions):
    print("\nPlease answer the following ontology-based clarification questions:")
    responses = {}
    for i, q in enumerate(questions.split("\n")):
        responses[f"Q{i+1}"] = input(f"{q}\nYour answer: ")
    return responses

# Function to generate structured ontology-based annotations
def generate_annotations(clarifications):
    prompt = f"Convert the following responses into structured ontology-based annotations in JSON format: {json.dumps(clarifications)}"
    
    response = openai.ChatCompletion.create(
        model="gpt-4.1",
        messages=[{"role": "system", "content": "You are an assistant structuring biological ontology-based annotations."},
                  {"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

# Function to generate starter CC3D scaffold code
def generate_cc3d_code(annotations):
    prompt = f"Generate CC3D starter code (XML/Python) based on the following structured ontology annotations: {annotations}"
    
    response = openai.ChatCompletion.create(
        model="gpt-4.1",
        messages=[{"role": "system", "content": "You are an assistant generating CC3D simulation code."},
                  {"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

# Main workflow
description = get_user_input()
questions = generate_clarification_questions(description)
clarifications = get_clarifications(questions)
annotations = generate_annotations(clarifications)
cc3d_code = generate_cc3d_code(annotations)

# Display results
print("\nGenerated Ontology-Based Annotations:\n", annotations)
print("\nGenerated CC3D Starter Code:\n", cc3d_code)