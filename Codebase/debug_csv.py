#!/usr/bin/env python3
"""
Debug script to check CSV loading
"""

import csv
from batch_csv import load_abstracts_csv

def debug_csv_loading(csv_file="week4papers.csv"):
    """Debug CSV loading to see what's happening"""
    
    print("=" * 60)
    print("CSV LOADING DEBUG")
    print("=" * 60)
    
    # First, let's manually read the CSV
    print("Manual CSV reading:")
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i >= 3:  # Only show first 3 rows
                    break
                print(f"Row {i+1}: {len(row)} columns")
                if len(row) >= 1:
                    print(f"  Column 1 (title): '{row[0][:80]}...'")
                if len(row) >= 2:
                    print(f"  Column 2 (abstract): '{row[1][:80]}...'")
                    print(f"  Abstract length: {len(row[1])}")
                print()
    
    except Exception as e:
        print(f"Error reading CSV manually: {str(e)}")
        return
    
    print("-" * 60)
    
    # Now let's use our function
    print("Using load_abstracts_csv function:")
    try:
        abstracts = load_abstracts_csv(csv_file)
        print(f"Loaded {len(abstracts)} papers")
        
        for i, paper in enumerate(abstracts[:3]):  # Show first 3
            print(f"Paper {i+1}:")
            print(f"  Title: '{paper['name'][:80]}...'")
            print(f"  Abstract: '{paper['abstract'][:80]}...'")
            print(f"  Abstract length: {len(paper['abstract'])}")
            print()
            
    except Exception as e:
        print(f"Error using load_abstracts_csv: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_csv_loading() 