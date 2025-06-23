#!/usr/bin/env python3

import csv
import tempfile
from pathlib import Path
from batch_csv import batch_process_to_csv

def create_test_csv():
    """Create a small test CSV with 2 papers for testing"""
    test_data = [
        ["Lattice-Based Model", "A computational model of ductal carcinoma in situ using cellular automata to simulate epithelial cell growth and division."],
        ["Agent-Based Simulation", "An agent-based model of tumor growth incorporating cell-cell adhesion and migration dynamics in tissue microenvironments."]
    ]
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerows(test_data)
        return f.name

def test_batch_processing():
    """Test the batch processing with the fix"""
    print("Creating test CSV...")
    test_csv = create_test_csv()
    
    print(f"Test CSV created: {test_csv}")
    print("Running batch processing with 2 papers, 2 runs each...")
    
    try:
        # Run batch processing with minimal runs for testing
        output_path = batch_process_to_csv(test_csv, num_runs_per_paper=2, output_csv="test_results.csv")
        print(f"\nTest completed! Results saved to: {output_path}")
        
        # Read and display results
        with open(output_path, 'r') as f:
            lines = f.readlines()
            print(f"\nFirst few lines of results:")
            for i, line in enumerate(lines[:5]):
                print(f"{i+1}: {line.strip()}")
                
        # Clean up
        Path(test_csv).unlink()
        print(f"\nTest CSV cleaned up: {test_csv}")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        # Clean up on error
        Path(test_csv).unlink()

if __name__ == "__main__":
    test_batch_processing() 