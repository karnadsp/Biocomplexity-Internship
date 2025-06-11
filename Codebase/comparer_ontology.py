import openai
import os

openai.api_key = ''

def ask_ontology_consistency(reference, comparison):
    prompt = f"""
You are a biomedical ontology comparison assistant. Two ontology extraction outputs are provided: Reference Ontology and Comparison Ontology.

- Evaluate how consistent the Comparison Ontology is relative to the Reference Ontology.
- Focus on:
  - Are the same cell types, biological processes, diseases/context, and parameters extracted?
  - Are any key ontology fields missing or added?
  - Minor differences in exact wording or synonyms are acceptable.
  - Large differences in concept extraction (e.g. missing cell types or wrong processes) are more serious.

Return ONLY:
1. Consistency Rating: 1 (very inconsistent) to 5 (fully consistent)
2. Brief explanation (max 1-2 sentences)

Reference Ontology:
\"\"\"{reference}\"\"\"

Comparison Ontology:
\"\"\"{comparison}\"\"\"
    """

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    folder = "."
    ref_file = os.path.join(folder, "paper1_ontology_1.txt")

    with open(ref_file, "r") as f:
        reference = f.read()

    # open output file for writing
    with open("ontology_consistency_comparison_output.txt", "w") as output_file:

        for i in range(2, 11):
            comp_file = os.path.join(folder, f"paper1_ontology_{i}.txt")

            if not os.path.isfile(comp_file):
                output_file.write(f"Run {i} comparison:\nFile not found: {comp_file}\n{'-'*50}\n")
                continue

            with open(comp_file, "r") as f:
                comparison = f.read()

            result = ask_ontology_consistency(reference, comparison)

            output_file.write(f"Run {i} comparison:\n{result}\n{'-'*50}\n")

    print("✅ All ontology comparisons completed. Results saved to 'ontology_consistency_comparison_output.txt'")
