#!/usr/bin/env python3

import json
import os
from pathlib import Path
from datetime import datetime
import re

def clean_response_text(response):
    """Clean up LLM response for presentation"""
    # Remove thinking process tags and content
    if "</think>" in response:
        response = response.split("</think>")[-1].strip()
    
    # Remove code blocks for cleaner text
    if "```json" in response:
        response = response.split("```json")[1].split("```")[0].strip()
    elif "```python" in response:
        response = response.split("```python")[1].split("```")[0].strip()
    elif "```" in response:
        response = response.split("```")[1].split("```")[0].strip()
    
    # Clean up spacing issues
    response = re.sub(r'\s+', ' ', response)  # Multiple spaces to single space
    response = re.sub(r'\n\s*\n', '\n\n', response)  # Clean up line breaks
    
    return response.strip()

def format_system_message(system_msg):
    """Format system message for presentation"""
    # Extract key requirements
    lines = system_msg.split('\n')
    clean_lines = []
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('    '):  # Skip indented examples
            clean_lines.append(line)
    
    return '\n'.join(clean_lines)

def extract_experiment_content(experiment_dir):
    """Extract prompts and responses from an experiment directory"""
    experiment_data_file = Path(experiment_dir) / "experiment_data.json"
    
    if not experiment_data_file.exists():
        return None
    
    try:
        with open(experiment_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract experiment info
        exp_info = data.get('experiment_info', {})
        experiment_name = exp_info.get('experiment_name', 'Unknown')
        run_number = exp_info.get('run_number', 1)
        
        # Extract input description
        initial_desc = data.get('inputs', {}).get('initial_description', {})
        description = initial_desc.get('data', {}).get('description', 'No description available')
        
        # Extract LLM interactions
        interactions = []
        llm_responses = data.get('llm_responses', [])
        
        for i, interaction in enumerate(llm_responses, 1):
            step_name = f"Step {i}"
            prompt = interaction.get('prompt', '')
            system_message = interaction.get('system_message', '')
            response = interaction.get('response', '')
            
            # Determine the step type
            if "ontology annotations" in system_message.lower():
                step_name = "Ontology Extraction"
            elif "compucell3d" in system_message.lower():
                step_name = "Code Generation"
            
            interactions.append({
                'step_name': step_name,
                'prompt': prompt,
                'system_message': format_system_message(system_message),
                'response': clean_response_text(response)
            })
        
        return {
            'experiment_name': experiment_name,
            'run_number': run_number,
            'description': description,
            'interactions': interactions
        }
        
    except Exception as e:
        print(f"Error processing {experiment_dir}: {str(e)}")
        return None

def generate_presentation_markdown(experiments_data, output_file="presentation_content.md"):
    """Generate a markdown file suitable for presentations"""
    
    content = []
    content.append("# Biological Modeling Assistant - Experiment Results")
    content.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    content.append("")
    content.append("---")
    content.append("")
    
    for exp_data in experiments_data:
        if not exp_data:
            continue
            
        # Experiment header
        content.append(f"## {exp_data['experiment_name']} (Run {exp_data['run_number']})")
        content.append("")
        
        # Original description
        content.append("### Original Description")
        content.append(f"> {exp_data['description']}")
        content.append("")
        
        # Process each interaction
        for interaction in exp_data['interactions']:
            content.append(f"### {interaction['step_name']}")
            content.append("")
            
            # System prompt (simplified)
            content.append("**System Instructions:**")
            system_lines = interaction['system_message'].split('\n')[:3]  # First 3 lines
            for line in system_lines:
                if line.strip():
                    content.append(f"- {line.strip()}")
            content.append("")
            
            # User prompt (simplified)
            if interaction['prompt']:
                content.append("**User Request:**")
                prompt_preview = interaction['prompt'][:200] + "..." if len(interaction['prompt']) > 200 else interaction['prompt']
                content.append(f"> {prompt_preview}")
                content.append("")
            
            # Response (cleaned)
            content.append("**AI Response:**")
            content.append("```")
            response_preview = interaction['response'][:500] + "..." if len(interaction['response']) > 500 else interaction['response']
            content.append(response_preview)
            content.append("```")
            content.append("")
        
        content.append("---")
        content.append("")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    print(f"Presentation content saved to: {output_file}")
    return output_file

def create_slide_ready_excerpts(experiments_data, output_file="slide_excerpts.txt"):
    """Create bite-sized excerpts perfect for slides"""
    
    content = []
    content.append("SLIDE-READY EXCERPTS FOR BIOLOGICAL MODELING ASSISTANT")
    content.append("=" * 60)
    content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    content.append("")
    
    for exp_data in experiments_data:
        if not exp_data:
            continue
            
        content.append(f"EXPERIMENT: {exp_data['experiment_name']}")
        content.append("-" * 40)
        
        # Short description for slide
        desc_words = exp_data['description'].split()[:25]  # First 25 words
        short_desc = ' '.join(desc_words) + "..." if len(exp_data['description'].split()) > 25 else exp_data['description']
        content.append(f"DESCRIPTION: {short_desc}")
        content.append("")
        
        for i, interaction in enumerate(exp_data['interactions'], 1):
            content.append(f"SLIDE {i}: {interaction['step_name']}")
            content.append("")
            
            # Key points for slide
            content.append("KEY POINTS:")
            if "ontology" in interaction['step_name'].lower():
                content.append("• AI extracts biological ontology terms")
                content.append("• Identifies Cell Ontology, Gene Ontology, and MeSH terms")
                content.append("• Structures biological knowledge")
            elif "code" in interaction['step_name'].lower():
                content.append("• AI generates CompuCell3D simulation code")
                content.append("• Creates executable biological models")
                content.append("• Translates ontologies into simulations")
            
            content.append("")
            
            # Sample response (very short)
            response_lines = interaction['response'].split('\n')[:3]  # First 3 lines
            content.append("SAMPLE OUTPUT:")
            for line in response_lines:
                if line.strip():
                    content.append(f"  {line.strip()[:80]}...")  # Max 80 chars per line
            
            content.append("")
            content.append("-" * 40)
            content.append("")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    print(f"Slide excerpts saved to: {output_file}")
    return output_file

def main():
    print("Biological Modeling Assistant - Presentation Content Extractor")
    print("=" * 60)
    
    # Get experiment directories
    experiments_dir = Path("experiments")
    if not experiments_dir.exists():
        print("Error: experiments directory not found")
        return
    
    # Find experiment directories
    experiment_dirs = []
    for item in experiments_dir.iterdir():
        if item.is_dir() and not item.name.startswith("archive") and not item.name.startswith("batch"):
            # Look for run subdirectories
            run_dirs = [d for d in item.iterdir() if d.is_dir() and d.name.startswith("run_")]
            if run_dirs:
                experiment_dirs.extend(run_dirs)
            else:
                # Check if this directory itself has experiment data
                if (item / "experiment_data.json").exists():
                    experiment_dirs.append(item)
    
    if not experiment_dirs:
        print("No experiment directories found")
        return
    
    print(f"Found {len(experiment_dirs)} experiment directories")
    
    # Extract content from experiments
    experiments_data = []
    for exp_dir in experiment_dirs[:10]:  # Limit to first 10 for demo
        print(f"Processing: {exp_dir}")
        exp_data = extract_experiment_content(exp_dir)
        if exp_data:
            experiments_data.append(exp_data)
    
    if not experiments_data:
        print("No valid experiment data found")
        return
    
    print(f"Successfully processed {len(experiments_data)} experiments")
    
    # Generate different output formats
    print("\nGenerating presentation materials...")
    
    # 1. Markdown for general documentation
    markdown_file = generate_presentation_markdown(experiments_data)
    
    # 2. Slide-ready excerpts
    excerpts_file = create_slide_ready_excerpts(experiments_data)
    
    print(f"\nGenerated 2 presentation formats:")
    print(f"1. Markdown: {markdown_file}")
    print(f"2. Slide excerpts: {excerpts_file}")
    print("\nThese files are ready for use in presentations!")

if __name__ == "__main__":
    main() 