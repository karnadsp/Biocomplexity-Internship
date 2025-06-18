import openai
import os
import re

openai.api_key = ''

# Function to parse LLM-generated file into sections
def extract_generated_files(generated_file_path):
    with open(generated_file_path, "r") as f:
        content = f.read()

    files = {}
    files['cc3d'] = re.search(r"---START CC3D---(.*?)---END CC3D---", content, re.DOTALL).group(1).strip()
    files['xml'] = re.search(r"---START XML---(.*?)---END XML---", content, re.DOTALL).group(1).strip()
    files['main'] = re.search(r"---START PYTHON MAIN---(.*?)---END PYTHON MAIN---", content, re.DOTALL).group(1).strip()
    files['steppables'] = re.search(r"---START PYTHON STEPPABLE---(.*?)---END PYTHON STEPPABLE---", content, re.DOTALL).group(1).strip()

    return files

def ask_code_consistency(file_type, real_code, generated_code):
    prompt = f"""
You are a CompuCell3D code comparison assistant. Compare the human-written "{file_type}" file against the LLM-generated version.

- Evaluate consistency in structure, logic, and implementation.
- Minor differences in comments, print statements or variable names are acceptable.
- Large differences in structure, biological logic, or simulation behavior are more serious.

Return ONLY:
1. Consistency Rating: 1 (very inconsistent) to 5 (fully consistent)
2. Very brief explanation (max 1-2 sentences)

Real {file_type} code:
\"\"\"{real_code}\"\"\"

LLM-generated {file_type} code:
\"\"\"{generated_code}\"\"\"
    """

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()

if __name__ == "__main__":

    generated_file = input("Enter LLM-generated file name (e.g. paper1_generated_code_1.txt): ").strip()
    real_xml = input("Enter real XML filename (e.g. real_model.xml): ").strip()
    real_main = input("Enter real Python Main filename (e.g. real_model.py): ").strip()
    real_steppables = input("Enter real Python Steppables filename (e.g. real_model_steppables.py): ").strip()

    generated = extract_generated_files(generated_file)

    # Load real files
    with open(real_xml, "r") as f: real_xml_content = f.read()
    with open(real_main, "r") as f: real_main_content = f.read()
    with open(real_steppables, "r") as f: real_steppables_content = f.read()

    # Open output file
    with open("compare_with_real_output.txt", "w") as output_file:

        for file_type, real_code, generated_code in [
            ("XML", real_xml_content, generated['xml']),
            ("Python Main", real_main_content, generated['main']),
            ("Python Steppables", real_steppables_content, generated['steppables'])
        ]:
            print(f"\nComparing {file_type}...")

            result = ask_code_consistency(file_type, real_code, generated_code)
            output_file.write(f"{file_type} Comparison:\n{result}\n{'-'*50}\n")

    print("\n✅ Comparison complete! Results saved to compare_with_real_output.txt")
