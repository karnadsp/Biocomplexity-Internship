import json
import os
import zipfile
import tempfile
from datetime import datetime
from pathlib import Path
import replicate
from dotenv import load_dotenv
import statistics
from difflib import SequenceMatcher
import re
import httpx
import httpcore
import time

# Load environment variables from .env file
load_dotenv("project.env")

# Debug prints
print("Current working directory:", os.getcwd())
print("Environment file exists:", os.path.exists("project.env"))
print("REPLICATE_API_TOKEN value:", os.getenv('REPLICATE_API_TOKEN'))

# Initialize the Replicate client with explicit token
api_token = os.getenv('REPLICATE_API_TOKEN')
if not api_token:
    raise ValueError("REPLICATE_API_TOKEN not found in environment variables")

client = replicate.Client(api_token=api_token)

class ExperimentLogger:
    def __init__(self, experiment_name, run_number=1):
        self.experiment_name = experiment_name
        self.run_number = run_number
        self.timestamp = datetime.now().strftime("%m%d_%H%M")
        self.experiment_dir = Path(f"experiments/{experiment_name}_{self.timestamp}_run{run_number}")
        self.experiment_dir.mkdir(parents=True, exist_ok=True)
        self.interaction_log = []
        
    def log_interaction(self, step_name, input_data, output_data):
        """Log an interaction with timestamps and metadata"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "input": input_data,
            "output": output_data
        }
        self.interaction_log.append(interaction)
        
        # Save individual interaction to file
        interaction_file = self.experiment_dir / f"{step_name}_{len(self.interaction_log)}.json"
        with open(interaction_file, 'w') as f:
            json.dump(interaction, f, indent=2)
            
    def save_experiment_summary(self):
        """Save complete experiment log"""
        summary_file = self.experiment_dir / "experiment_summary.json"
        with open(summary_file, 'w') as f:
            json.dump({
                "experiment_name": self.experiment_name,
                "timestamp": self.timestamp,
                "run_number": self.run_number,
                "interactions": self.interaction_log
            }, f, indent=2)

def get_llm_response(prompt, system_message, logger):
    """Helper function to get response from Replicate API"""
    # Format the prompt with system message
    full_prompt = f"{system_message}\n\n{prompt}"
    
    print(f"\nSending request to API...")
    
    # Get the specific deployment
    deployment = replicate.deployments.get("umsi-amadaman/cc3d-deepseekr1")
    
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            # Create and wait for prediction
            prediction = deployment.predictions.create(
                input={
                    "prompt": full_prompt,
                    "temperature": 0.3,  # Lower temperature for more consistent outputs
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            )
            
            print("Waiting for response...")
            prediction.wait()
            print("Received response!")
            
            # Get the response and handle list output
            result = prediction.output
            if isinstance(result, list):
                result = "".join(result)
            
            # Log the full response
            logger.log_interaction("llm_response", 
                                {"prompt": prompt, "system_message": system_message},
                                {"response": result})
            
            # Remove thinking process if present
            if "</think>" in result:
                result = result.split("</think>")[-1].strip()
            
            # For ontology responses, we expect JSON
            if "Return ONLY a JSON object" in system_message:
                # Extract JSON block if present
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0].strip()
                return result
            
            # For code responses, extract Python code
            elif "Return ONLY the Python code" in system_message:
                if "```python" in result:
                    result = result.split("```python")[1].split("```")[0].strip()
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0].strip()
                return result
            
            return result
            
        except (httpx.ConnectError, httpcore.ConnectError) as e:
            if attempt < max_retries - 1:
                print(f"Connection error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"Failed to connect after {max_retries} attempts")
                raise
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise
    
    return result

def generate_clarification_questions(description, logger):
    """Generate ontology-focused clarification questions based on the description"""
    system_message = """You are a biological modeling expert. Generate specific clarification questions 
    focusing on Cell Ontology, Gene Ontology (GO), and MeSH terms that would help understand the system better.
    Format your response as a numbered list of questions."""
    
    prompt = f"Based on this biological system description, what clarification questions would help identify relevant ontologies?\n\nDescription: {description}"
    return get_llm_response(prompt, system_message, logger)

def generate_ontology_annotations(description, clarifications, logger):
    """Generate structured ontology-based annotations from the clarifications"""
    system_message = """You are a biological modeling expert. Create structured ontology annotations based on the provided information. 
    Include relevant Cell Ontology, GO, and MeSH terms where applicable.
    Return ONLY a JSON object with categories for different ontology types.
    
    Format requirements:
    1. Category names must be exact:
       - "CellOntology" (not "Cell Ontology" or "Cell  Ontology")
       - "GeneOntology" (not "Gene Ontology" or "Gene  Ontology")
       - "MeSH" (not "MeSH Terms" or "MeSH  Terms")
    
    2. Ontology IDs must be exact without spaces:
       - Cell Ontology: "CL:0000000" (not "CL : 000 000 0")
       - Gene Ontology: "GO:0000000" (not "GO : 000 000 0")
       - MeSH: "D000000" (not "D 000 000")
    
    3. Term names must be exact without extra spaces:
       - "Epithelial" (not "Ep ith elial")
       - "Mesenchymal" (not "Mes ench ym al")
    
    Example format:
    {
        "CellOntology": [
            {
                "id": "CL:0000000",
                "term": "Epithelial"
            }
        ],
        "GeneOntology": [
            {
                "id": "GO:0000000",
                "term": "Cell Division"
            }
        ],
        "MeSH": [
            {
                "id": "D000000",
                "term": "Cell Proliferation"
            }
        ]
    }
    
    Do not include any explanations or thinking process."""
    
    prompt = f"""Original description: {description}\n\nClarifications provided: {clarifications}\n\n
    Return ONLY a JSON object with ontology annotations. Format all IDs and terms exactly as specified in the system message."""
    
    response = get_llm_response(prompt, system_message, logger)
    return extract_ontologies_from_response(response)

def generate_cc3d_starter_code(annotations, logger):
    """Generate CC3D starter code based on the ontology annotations"""
    system_message = """You are a CompuCell3D expert. Generate a valid CompuCell3D simulation file.
    Return ONLY the Python code without any additional text, explanations, or thinking process.
    The code must include:
    1. Required imports (CompuCellSetup, steppables)
    2. A proper simulation class that inherits from steppables.SteppableBasePy
    3. Required methods (__init__, start, step)
    4. Basic cell types and parameters based on the ontology annotations"""
    
    prompt = f"""Generate a valid CompuCell3D simulation file based on these ontology annotations.
    Return ONLY the Python code:\n\n{annotations}"""
    
    return get_llm_response(prompt, system_message, logger)

def create_cc3d_file(python_code, logger):
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
        
        # Create the .cc3d zip file in the experiment directory
        output_file = os.path.join(logger.experiment_dir, "generated_cc3d_model.cc3d")
        with zipfile.ZipFile(output_file, 'w') as zipf:
            zipf.write(sim_file, "Simulation.py")
            zipf.write(config_file, "Simulation.cc3d")
        
        logger.log_interaction("cc3d_file_creation", 
                             {"python_code": python_code},
                             {"output_file": output_file})
        
        return output_file

def run_experiment(experiment_name, description, run_number, num_runs):
    """Run a single experiment with the given parameters"""
    print(f"\nStarting experiment run {run_number} of {num_runs}...")
    logger = ExperimentLogger(experiment_name, run_number)
    
    # Log initial description
    print("Generating ontology annotations...")
    logger.log_interaction("initial_description", {}, {"description": description})
    
    # Generate and log ontology annotations directly from description
    annotations = generate_ontology_annotations(description, "", logger)
    print("Ontology annotations generated.")
    
    # Generate and log CC3D code
    print("Generating CC3D code...")
    cc3d_code = generate_cc3d_starter_code(annotations, logger)
    if isinstance(cc3d_code, str):
        cc3d_code = cc3d_code.replace("```python", "").replace("```", "").strip()
    
    if "from cc3d.core.PySteppables import *" not in cc3d_code:
        cc3d_code = "from cc3d.core.PySteppables import *\n\n" + cc3d_code
    
    print("Creating CC3D file...")
    # Create and save the .cc3d file
    output_file = create_cc3d_file(cc3d_code, logger)
    
    # Save complete experiment summary
    print("Saving experiment summary...")
    logger.save_experiment_summary()
    
    print(f"Experiment run {run_number} completed.")
    return logger.experiment_dir

def extract_ontologies_from_response(response):
    """Extract ontology terms from LLM response"""
    ontologies = {
        'CellOntology': set(),
        'GeneOntology': set(),
        'MeSH': set()
    }
    
    try:
        print("\nExtracting ontologies from response:")
        print(f"Raw response: {response[:200]}...")  # Print first 200 chars
        
        # Parse JSON
        data = json.loads(response)
        print(f"Parsed JSON data: {data}")
        
        # Process each category
        for category, items in data.items():
            print(f"\nProcessing category: {category}")
            # Determine ontology type
            ontology_type = None
            if 'CellOntology' in category:
                ontology_type = 'CellOntology'
            elif 'GeneOntology' in category:
                ontology_type = 'GeneOntology'
            elif 'MeSH' in category:
                ontology_type = 'MeSH'
            
            if ontology_type and isinstance(items, list):
                print(f"Found {len(items)} items in {ontology_type}")
                for item in items:
                    if isinstance(item, dict) and 'id' in item and 'term' in item:
                        term = f"{item['term']} ({item['id']})"
                        ontologies[ontology_type].add(term)
                        print(f"Added term: {term}")
    
    except Exception as e:
        print(f"Error extracting ontologies: {str(e)}")
        print(f"Response that caused error: {response}")
    
    print(f"\nFinal ontologies: {ontologies}")
    return ontologies

def extract_code_from_response(response):
    """Extract Python code from LLM response"""
    # Remove thinking process if present
    if "</think>" in response:
        response = response.split("</think>")[-1].strip()
    
    # Extract code block if present
    if "```python" in response:
        response = response.split("```python")[1].split("```")[0].strip()
    
    return response

def calculate_similarity(str1, str2):
    """Calculate similarity ratio between two objects"""
    # Convert both inputs to strings and ensure they're not None
    str1 = str(str1) if str1 is not None else ""
    str2 = str(str2) if str2 is not None else ""
    
    # If either string is empty, return 0 similarity
    if not str1 or not str2:
        return 0.0
    
    # Ensure strings are not empty and contain valid characters
    if not str1.strip() or not str2.strip():
        return 0.0
        
    try:
        # Create a new SequenceMatcher instance
        matcher = SequenceMatcher(None, str1, str2)
        # Get the ratio, defaulting to 0.0 if there's an error
        return matcher.ratio() if matcher else 0.0
    except Exception as e:
        print(f"Error calculating similarity: {str(e)}")
        return 0.0

def analyze_run_consistency(experiment_dirs):
    """Analyze consistency of ontologies and code across runs"""
    # Track results for each stage
    stage_results = {
        'natural_to_ontology': [],  # Natural language to ontology conversion
        'ontology_to_code': [],     # Ontology to CC3D code conversion
        'natural_to_code': []       # End-to-end conversion
    }
    
    print("\nAnalyzing run consistency...")
    print(f"Number of experiment directories: {len(experiment_dirs)}")
    
    # Extract results from each run
    for run_dir in experiment_dirs:
        try:
            print(f"\nProcessing directory: {run_dir}")
            with open(Path(run_dir) / "experiment_summary.json", 'r') as f:
                data = json.load(f)
            
            # Get all LLM responses in order
            llm_responses = []
            for interaction in data['interactions']:
                if interaction['step'] == 'llm_response':
                    llm_responses.append(interaction)
            
            print(f"Found {len(llm_responses)} LLM responses")
            
            # Process responses in order
            ontologies = None
            code = None
            
            if len(llm_responses) >= 1:
                # First response should be ontologies
                print("Processing first response as ontologies...")
                raw_response = llm_responses[0]['output']['response']
                
                # Process the response to extract JSON
                processed_response = raw_response
                if "</think>" in processed_response:
                    processed_response = processed_response.split("</think>")[-1].strip()
                if "```json" in processed_response:
                    processed_response = processed_response.split("```json")[1].split("```")[0].strip()
                elif "```" in processed_response:
                    processed_response = processed_response.split("```")[1].split("```")[0].strip()
                
                ontologies = extract_ontologies_from_response(processed_response)
                print(f"Extracted ontologies: {ontologies}")
                stage_results['natural_to_ontology'].append(ontologies)
            
            if len(llm_responses) >= 2:
                # Second response should be code
                print("Processing second response as code...")
                code = extract_code_from_response(llm_responses[1]['output']['response'])
                print(f"Extracted code length: {len(code) if code else 0}")
                stage_results['ontology_to_code'].append(code)
            
            # If we have both, add end-to-end data
            if ontologies and code:
                stage_results['natural_to_code'].append({
                    'ontology': ontologies,
                    'code': code
                })
                print("Added end-to-end data")
        
        except Exception as e:
            print(f"Error processing run directory {run_dir}: {str(e)}")
            continue
    
    print("\nStage results summary:")
    for stage, results in stage_results.items():
        print(f"{stage}: {len(results)} results")
    
    # Calculate consistency metrics for each stage
    consistency_metrics = {
        'natural_to_ontology': {
            'ontology_consistency': {},
            'stage_name': 'Natural Language to Ontology'
        },
        'ontology_to_code': {
            'code_similarity': [],
            'stage_name': 'Ontology to CC3D Code'
        },
        'natural_to_code': {
            'ontology_consistency': {},
            'code_similarity': [],
            'stage_name': 'Natural Language to CC3D Code (End-to-End)'
        }
    }
    
    # Calculate ontology consistency for natural_to_ontology stage
    if stage_results['natural_to_ontology']:
        print("\nCalculating ontology consistency...")
        for category in ['CellOntology', 'GeneOntology', 'MeSH']:
            all_terms = set()
            for result in stage_results['natural_to_ontology']:
                if result and category in result:
                    all_terms.update(result[category])
            
            print(f"\nCategory {category}:")
            print(f"All terms found: {all_terms}")
            
            term_frequencies = {}
            for term in all_terms:
                count = sum(1 for result in stage_results['natural_to_ontology'] 
                          if result and category in result and term in result[category])
                term_frequencies[term] = count / len(stage_results['natural_to_ontology'])
            
            print(f"Term frequencies: {term_frequencies}")
            consistency_metrics['natural_to_ontology']['ontology_consistency'][category] = term_frequencies
    
    # Calculate code similarity for ontology_to_code stage
    if len(stage_results['ontology_to_code']) > 1:
        print("\nCalculating code similarity...")
        for i in range(len(stage_results['ontology_to_code'])):
            for j in range(i + 1, len(stage_results['ontology_to_code'])):
                try:
                    similarity = calculate_similarity(stage_results['ontology_to_code'][i], 
                                                   stage_results['ontology_to_code'][j])
                    consistency_metrics['ontology_to_code']['code_similarity'].append({
                        'run_pair': f"{i+1}-{j+1}",
                        'similarity': similarity
                    })
                    print(f"Code similarity {i+1}-{j+1}: {similarity:.2%}")
                except Exception as e:
                    print(f"Error calculating code similarity between runs {i+1} and {j+1}: {str(e)}")
    
    # Calculate end-to-end consistency
    if stage_results['natural_to_code']:
        print("\nCalculating end-to-end consistency...")
        # Calculate ontology consistency
        for category in ['CellOntology', 'GeneOntology', 'MeSH']:
            all_terms = set()
            for result in stage_results['natural_to_code']:
                if result and 'ontology' in result and category in result['ontology']:
                    all_terms.update(result['ontology'][category])
            
            term_frequencies = {}
            for term in all_terms:
                count = sum(1 for result in stage_results['natural_to_code']
                          if result and 'ontology' in result and category in result['ontology']
                          and term in result['ontology'][category])
                term_frequencies[term] = count / len(stage_results['natural_to_code'])
            
            consistency_metrics['natural_to_code']['ontology_consistency'][category] = term_frequencies
        
        # Calculate code similarity
        if len(stage_results['natural_to_code']) > 1:
            for i in range(len(stage_results['natural_to_code'])):
                for j in range(i + 1, len(stage_results['natural_to_code'])):
                    try:
                        similarity = calculate_similarity(stage_results['natural_to_code'][i]['code'],
                                                       stage_results['natural_to_code'][j]['code'])
                        consistency_metrics['natural_to_code']['code_similarity'].append({
                            'run_pair': f"{i+1}-{j+1}",
                            'similarity': similarity
                        })
                        print(f"End-to-end code similarity {i+1}-{j+1}: {similarity:.2%}")
                    except Exception as e:
                        print(f"Error calculating end-to-end code similarity between runs {i+1} and {j+1}: {str(e)}")
    
    return consistency_metrics

def format_consistency_analysis(metrics):
    """Format consistency analysis results for presentation"""
    output = []
    output.append("=" * 80)
    output.append("BIOLOGICAL MODELING PIPELINE CONSISTENCY ANALYSIS")
    output.append("=" * 80)
    output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("")
    
    # Executive Summary
    output.append("EXECUTIVE SUMMARY")
    output.append("-" * 80)
    
    # Calculate overall metrics
    total_runs = 0
    successful_stages = 0
    
    for stage_key, stage_metrics in metrics.items():
        if 'ontology_consistency' in stage_metrics:
            for category, terms in stage_metrics['ontology_consistency'].items():
                if terms:
                    total_runs = max(total_runs, len([t for t in terms.values() if t > 0]))
        if 'code_similarity' in stage_metrics and stage_metrics['code_similarity']:
            successful_stages += 1
    
    output.append(f"• Total experiment runs analyzed: {total_runs}")
    output.append(f"• Pipeline stages with data: {len([m for m in metrics.values() if any(v for k, v in m.items() if k != 'stage_name' and v)])}")
    output.append("")
    
    # Detailed Analysis by Stage
    for stage_key, stage_metrics in metrics.items():
        output.append(f"{stage_metrics['stage_name'].upper()} STAGE")
        output.append("=" * len(stage_metrics['stage_name']) + "=" * 7)
        output.append("")
        
        stage_has_data = False
        
        # Ontology Analysis
        if 'ontology_consistency' in stage_metrics:
            ontology_data = stage_metrics['ontology_consistency']
            
            for category in ['CellOntology', 'GeneOntology', 'MeSH']:
                if category in ontology_data and ontology_data[category]:
                    stage_has_data = True
                    term_frequencies = ontology_data[category]
                    
                    output.append(f"{category} Terms:")
                    output.append("-" * (len(category) + 7))
                    
                    # Sort terms by consistency (highest first)
                    sorted_terms = sorted(term_frequencies.items(), key=lambda x: x[1], reverse=True)
                    
                    if sorted_terms:
                        # Statistics
                        frequencies = list(term_frequencies.values())
                        avg_consistency = sum(frequencies) / len(frequencies)
                        max_consistency = max(frequencies)
                        perfect_terms = sum(1 for f in frequencies if f == 1.0)
                        
                        output.append(f"  STATISTICS:")
                        output.append(f"     • Total unique terms: {len(sorted_terms)}")
                        output.append(f"     • Average consistency: {avg_consistency:.1%}")
                        output.append(f"     • Maximum consistency: {max_consistency:.1%}")
                        output.append(f"     • Terms with 100% consistency: {perfect_terms}")
                        output.append("")
                        
                        output.append(f"  TOP CONSISTENT TERMS:")
                        # Show top 5 most consistent terms
                        for term, frequency in sorted_terms[:5]:
                            consistency_bar = "█" * int(frequency * 10) + "░" * (10 - int(frequency * 10))
                            output.append(f"     {frequency:.1%} [{consistency_bar}] {term}")
                        
                        if len(sorted_terms) > 5:
                            output.append(f"     ... and {len(sorted_terms) - 5} more terms")
                        
                        output.append("")
                        
                        # Show problematic terms (low consistency)
                        low_consistency_terms = [(t, f) for t, f in sorted_terms if f < 0.5]
                        if low_consistency_terms:
                            output.append(f"  INCONSISTENT TERMS (< 50%):")
                            for term, frequency in low_consistency_terms[:3]:
                                output.append(f"     {frequency:.1%} {term}")
                            if len(low_consistency_terms) > 3:
                                output.append(f"     ... and {len(low_consistency_terms) - 3} more")
                            output.append("")
                    else:
                        output.append(f"  No {category} terms found")
                        output.append("")
        
        # Code Similarity Analysis
        if 'code_similarity' in stage_metrics and stage_metrics['code_similarity']:
            stage_has_data = True
            similarities = stage_metrics['code_similarity']
            
            output.append("Code Similarity Analysis:")
            output.append("-" * 25)
            
            # Calculate statistics
            similarity_values = [pair['similarity'] for pair in similarities]
            avg_similarity = sum(similarity_values) / len(similarity_values)
            min_similarity = min(similarity_values)
            max_similarity = max(similarity_values)
            
            output.append(f"  STATISTICS:")
            output.append(f"     • Number of comparisons: {len(similarities)}")
            output.append(f"     • Average similarity: {avg_similarity:.1%}")
            output.append(f"     • Minimum similarity: {min_similarity:.1%}")
            output.append(f"     • Maximum similarity: {max_similarity:.1%}")
            output.append("")
            
            # Similarity grade
            if avg_similarity >= 0.8:
                grade = "EXCELLENT"
            elif avg_similarity >= 0.6:
                grade = "GOOD"
            elif avg_similarity >= 0.4:
                grade = "MODERATE"
            else:
                grade = "POOR"
            
            output.append(f"  OVERALL CODE CONSISTENCY: {grade}")
            output.append("")
            
            # Show individual comparisons
            output.append(f"  PAIRWISE COMPARISONS:")
            for pair in similarities:
                similarity_bar = "█" * int(pair['similarity'] * 10) + "░" * (10 - int(pair['similarity'] * 10))
                output.append(f"     Runs {pair['run_pair']}: {pair['similarity']:.1%} [{similarity_bar}]")
            output.append("")
        
        if not stage_has_data:
            output.append("  No data available for this stage")
            output.append("")
        
        output.append("-" * 80)
        output.append("")
    
    # Recommendations Section
    output.append("RECOMMENDATIONS & INSIGHTS")
    output.append("=" * 80)
    
    # Analyze overall pipeline health
    recommendations = []
    
    # Check ontology consistency
    low_consistency_categories = []
    for stage_key, stage_metrics in metrics.items():
        if 'ontology_consistency' in stage_metrics:
            for category, terms in stage_metrics['ontology_consistency'].items():
                if terms:
                    avg_consistency = sum(terms.values()) / len(terms.values())
                    if avg_consistency < 0.5:
                        low_consistency_categories.append((category, avg_consistency, stage_key))
    
    if low_consistency_categories:
        recommendations.append("ONTOLOGY CONSISTENCY ISSUES:")
        for category, avg_cons, stage in low_consistency_categories:
            recommendations.append(f"   • {category} shows low consistency ({avg_cons:.1%}) in {stage}")
            recommendations.append(f"     → Consider refining prompts for {category} term extraction")
        recommendations.append("")
    
    # Check code similarity
    code_issues = []
    for stage_key, stage_metrics in metrics.items():
        if 'code_similarity' in stage_metrics and stage_metrics['code_similarity']:
            similarities = [pair['similarity'] for pair in stage_metrics['code_similarity']]
            avg_sim = sum(similarities) / len(similarities)
            if avg_sim < 0.4:
                code_issues.append((stage_key, avg_sim))
    
    if code_issues:
        recommendations.append("CODE GENERATION CONSISTENCY ISSUES:")
        for stage, avg_sim in code_issues:
            recommendations.append(f"   • {stage} shows low code similarity ({avg_sim:.1%})")
            recommendations.append(f"     → Consider using lower temperature or more specific prompts")
        recommendations.append("")
    
    # General recommendations
    recommendations.append("GENERAL RECOMMENDATIONS:")
    recommendations.append("   • Run more experiments (5+ runs) for better statistical significance")
    recommendations.append("   • Monitor consistency trends over time")
    recommendations.append("   • Consider prompt engineering if consistency is below 70%")
    recommendations.append("   • Archive low-performing experiment configurations")
    recommendations.append("")
    
    # Add recommendations to output
    if recommendations:
        output.extend(recommendations)
    else:
        output.append("No major issues detected. Pipeline appears to be performing well.")
        output.append("")
    
    # Footer
    output.append("=" * 80)
    output.append("End of Analysis Report")
    output.append("=" * 80)
    
    return "\n".join(output)

def generate_detailed_summary(experiment_dirs, experiment_name, description):
    """Generate a comprehensive summary of the experiment batch"""
    summary_content = []
    
    # Header
    summary_content.append("=" * 80)
    summary_content.append("BIOLOGICAL MODELING EXPERIMENT SUMMARY")
    summary_content.append("=" * 80)
    summary_content.append(f"Experiment Name: {experiment_name}")
    summary_content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary_content.append(f"Total Runs: {len(experiment_dirs)}")
    summary_content.append("")
    
    # Original Description
    summary_content.append("ORIGINAL BIOLOGICAL SYSTEM DESCRIPTION")
    summary_content.append("-" * 80)
    summary_content.append(description)
    summary_content.append("")
    
    # Run Details
    summary_content.append("EXPERIMENT RUN DETAILS")
    summary_content.append("-" * 80)
    
    for i, exp_dir in enumerate(experiment_dirs, 1):
        try:
            with open(Path(exp_dir) / "experiment_summary.json", 'r') as f:
                data = json.load(f)
            
            summary_content.append(f"Run {i}: {exp_dir.name}")
            summary_content.append(f"  Directory: {exp_dir}")
            summary_content.append(f"  Timestamp: {data.get('timestamp', 'Unknown')}")
            summary_content.append(f"  Interactions: {len(data.get('interactions', []))}")
            
            # Check for generated files
            cc3d_file = exp_dir / "generated_cc3d_model.cc3d"
            if cc3d_file.exists():
                file_size = cc3d_file.stat().st_size
                summary_content.append(f"  CC3D Model: {file_size} bytes")
            else:
                summary_content.append(f"  CC3D Model: Not generated")
            
            summary_content.append("")
            
        except Exception as e:
            summary_content.append(f"Run {i}: {exp_dir.name} (Error reading summary: {str(e)})")
            summary_content.append("")
    
    return "\n".join(summary_content)

def main():
    print("Welcome to the Biological System Modeling Assistant!")
    
    # Get experiment parameters
    experiment_name = input("Enter a name for this experiment: ")
    num_runs = int(input("Enter the number of runs for reproducibility assessment (default: 3): ") or "3")
    
    print("\nPlease provide a description of the biological system you wish to model:")
    description = input("> ")
    
    # Run multiple experiments
    experiment_dirs = []
    for run in range(1, num_runs + 1):
        print(f"\nRunning experiment {run} of {num_runs}...")
        experiment_dir = run_experiment(experiment_name, description, run, num_runs)
        experiment_dirs.append(experiment_dir)
        print(f"Completed run {run}. Results saved in {experiment_dir}")
    
    # Create a summary of all runs
    summary_dir = Path(f"experiments/{experiment_name}_summary_{datetime.now().strftime('%m%d_%H%M')}")
    summary_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nGenerating comprehensive summary...")
    
    # Generate detailed experiment summary
    detailed_summary = generate_detailed_summary(experiment_dirs, experiment_name, description)
    with open(summary_dir / "experiment_summary.txt", 'w', encoding='utf-8') as f:
        f.write(detailed_summary)
    
    # Perform and save consistency analysis
    consistency_metrics = analyze_run_consistency(experiment_dirs)
    consistency_analysis = format_consistency_analysis(consistency_metrics)
    
    with open(summary_dir / "consistency_analysis.txt", 'w', encoding='utf-8') as f:
        f.write(consistency_analysis)
    
    # Generate a combined report
    combined_report = detailed_summary + "\n\n" + consistency_analysis
    with open(summary_dir / "complete_analysis_report.txt", 'w', encoding='utf-8') as f:
        f.write(combined_report)
    
    print(f"\n{'='*60}")
    print(f"ALL RUNS COMPLETED SUCCESSFULLY!")
    print(f"{'='*60}")
    print(f"Summary files generated:")
    print(f"   • experiment_summary.txt - Detailed run information")
    print(f"   • consistency_analysis.txt - Pipeline consistency analysis")
    print(f"   • complete_analysis_report.txt - Combined comprehensive report")
    print(f"All files saved in: {summary_dir}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 