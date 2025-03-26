import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import traceback

def check_data_availability():
    """Check if market data is available"""
    print("Checking data availability...")
    
    if not os.path.exists('market_data'):
        print("Error: 'market_data' directory not found.")
        return False
        
    files = os.listdir('market_data')
    if not files:
        print("Error: No files found in 'market_data' directory.")
        return False
        
    print(f"Found {len(files)} files in 'market_data' directory:")
    for f in files[:5]:
        print(f"  - {f}")
    if len(files) > 5:
        print(f"  - ... and {len(files) - 5} more")
        
    # Check if SPY data exists
    spy_files = [f for f in files if 'SPY' in f]
    if not spy_files:
        print("Error: No SPY data found.")
    else:
        print(f"Found SPY data: {spy_files}")
        
    return True
    
def check_fear_greed_data():
    """Check if fear & greed data is available"""
    print("\nChecking fear & greed data availability...")
    
    if not os.path.exists('fear_greed_data'):
        print("Error: 'fear_greed_data' directory not found.")
        return False
        
    files = os.listdir('fear_greed_data')
    if not files:
        print("Error: No files found in 'fear_greed_data' directory.")
        return False
        
    print(f"Found {len(files)} files in 'fear_greed_data' directory:")
    for f in files[:5]:
        print(f"  - {f}")
    if len(files) > 5:
        print(f"  - ... and {len(files) - 5} more")
        
    return True

def try_load_price_data():
    """Try to load price data for common symbols"""
    print("\nTrying to load price data...")
    
    symbols = ['SPY', 'QQQ', 'VTI']
    
    for symbol in symbols:
        try:
            # Try to load from market_data directory
            symbol_file = symbol.replace('^', '')
            file_path = f"market_data/{symbol_file}_data.csv"
            
            if not os.path.exists(file_path):
                print(f"Warning: No data found for {symbol} at {file_path}")
                continue
                
            df = pd.read_csv(file_path)
            print(f"Successfully loaded {symbol} data with {len(df)} rows")
            print(f"First date: {df.iloc[0]['Date'] if 'Date' in df else df.iloc[0][0]}")
            print(f"Last date: {df.iloc[-1]['Date'] if 'Date' in df else df.iloc[-1][0]}")
            print(f"Columns: {df.columns.tolist()}")
            print()
            
        except Exception as e:
            print(f"Error loading data for {symbol}: {e}")
            traceback.print_exc()

def main():
    """Run all checks"""
    print("=== Algorithmic Trading Framework Debug ===")
    print(f"Current directory: {os.getcwd()}")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if directories and files exist
    check_data_availability()
    check_fear_greed_data()
    
    # Try to load price data
    try_load_price_data()
    
    print("\nDebug completed.")

if __name__ == "__main__":
    main() 