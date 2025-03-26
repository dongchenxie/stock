import os
import sys
import traceback

def main():
    print("Starting debug...")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    
    # Check if market_data exists
    if os.path.exists('market_data'):
        print("market_data directory exists")
        print(f"Contents: {os.listdir('market_data')}")
    else:
        print("market_data directory does not exist")
    
    # Try importing pandas
    try:
        import pandas as pd
        print(f"Pandas version: {pd.__version__}")
    except Exception as e:
        print(f"Error importing pandas: {e}")
        traceback.print_exc()
    
    # Try a simple file operation
    try:
        with open('debug_test.txt', 'w') as f:
            f.write('Debug test')
        print("Successfully wrote to debug_test.txt")
    except Exception as e:
        print(f"Error writing to file: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
        print("Debug completed successfully")
    except Exception as e:
        print(f"Error during debugging: {e}")
        traceback.print_exc() 