#!/usr/bin/env python3
"""
Simple script to run week4papers with DeepSeek R1 (reasoning model)
This script assumes week4papers.csv exists in the current directory
"""

from batch_csv import batch_process_to_csv
import os

def main():
    # Check if week4papers.csv exists
    csv_file = "week4papers.csv"
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found in current directory")
        print("Please make sure week4papers.csv is in the same directory as this script")
        return
    
    print("Running week4papers with DeepSeek R1 (reasoning model)")
    print("=" * 60)
    print(f"Input file: {csv_file}")
    
    # Get number of runs
    num_runs = int(input("Enter number of runs per paper (default 3): ") or "3")
    
    # Set output filename to include R1 in the name
    output_name = f"week4papers_r1_results_{num_runs}runs.csv"
    
    print(f"Output file: {output_name}")
    print(f"Model: DeepSeek R1 (reasoning)")
    print(f"Runs per paper: {num_runs}")
    print("=" * 60)
    
    # Confirm before starting
    confirm = input("Start batch processing? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("Cancelled.")
        return
    
    # Run batch processing with R1 model
    try:
        output_path = batch_process_to_csv(
            input_csv=csv_file,
            num_runs_per_paper=num_runs,
            output_csv=output_name,
            model_type="reasoning"  # Use DeepSeek R1
        )
        
        print("\n" + "=" * 60)
        print("BATCH PROCESSING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Results saved to: {output_path}")
        print("\nThe reasoning model (R1) provides:")
        print("• Step-by-step thinking processes")
        print("• Detailed reasoning for each decision")
        print("• Thinking processes logged in metadata")
        print("• More thorough biological analysis")
        
    except Exception as e:
        print(f"\nError during batch processing: {e}")
        print("Please check the error message above and try again.")

if __name__ == "__main__":
    main() 