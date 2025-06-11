import openai
import os

openai.api_key = ''

def ask_consistency(reference, comparison):
    prompt = f"""
You are a biomedical code comparison assistant. Two CompuCell3D code outputs are provided: Reference Code and Comparison Code.

- Evaluate how consistent the Comparison Code is relative to the Reference Code.
- Focus on:
  - File structure and correct generation of four files (CC3D, XML, PYTHON MAIN, PYTHON STEPPABLE)
  - Whether key biological logic is preserved
  - Whether major sections are missing or incorrect
  - Parameter differences are allowed, but large structural differences are more severe

Return ONLY:
1. Consistency Rating: 1 (very inconsistent) to 5 (fully consistent)
2. Brief explanation (max 1-2 sentences)

Reference Code:
\"\"\"{reference}\"\"\"

Comparison Code:
\"\"\"{comparison}\"\"\"
    """

    response = openai.chat.completions.create(
        model="gpt-4o",  # or gpt-4
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    folder = "."  # adjust as needed
ref_file = os.path.join(folder, "paper1_generated_code_1.txt")
with open(ref_file, "r") as f:
    reference = f.read()

for i in range(2, 11):
    comp_file = os.path.join(folder, f"paper1_generated_code_{i}.txt")
    with open(comp_file, "r") as f:
        comparison = f.read()

    result = ask_consistency(reference, comparison)
    print(f"Run {i} comparison:\n{result}\n{'-'*50}\n")

