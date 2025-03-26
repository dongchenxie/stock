import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import json

class SimpleDCAStrategy:
    """
    Simple Dollar-Cost Averaging Strategy
    Invests a fixed amount at regular intervals regardless of price
    """
    def __init__(self, symbols, weekly_investment=500):
        self.symbols = symbols
        self.weekly_investment = weekly_investment
        self.portfolio = {
            'cash': 0,
            'assets': {symbol: 0 for symbol in symbols},
            'history': []
        }
        
    def run_backtest(self, start_date, end_date):
        """Run a backtest of the DCA strategy"""
        print(f"Running DCA backtest from {start_date} to {end_date}")
        
        # Load price data
        price_data = self._load_price_data()
        if price_data.empty:
            print("Error: No price data found.")
            return None
            
        # Convert dates to datetime
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # Get weekly dates (Fridays)
        dates = pd.date_range(start=start, end=end, freq='W-FRI')
        
        # Reset portfolio
        self.portfolio = {
            'cash': 0,
            'assets': {symbol: 0 for symbol in self.symbols},
            'history': []
        }
        
        # Run simulation
        for date in dates:
            # Find the closest trading day
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in price_data.index:
                closest_dates = price_data.index[price_data.index <= date_str]
                if len(closest_dates) == 0:
                    continue
                date_str = closest_dates[-1]
                
            # Add weekly investment
            self.portfolio['cash'] += self.weekly_investment
            
            # Allocate investment equally
            allocation_per_symbol = self.weekly_investment / len(self.symbols)
            
            # Buy assets
            for symbol in self.symbols:
                if symbol not in price_data.columns:
                    continue
                    
                try:
                    price = price_data.loc[date_str, symbol]
                    
                    # Skip if price is NaN
                    if pd.isna(price):
                        continue
                        
                    # Calculate shares to buy
                    shares = allocation_per_symbol / price
                    
                    # Update portfolio
                    self.portfolio['cash'] -= allocation_per_symbol
                    self.portfolio['assets'][symbol] += shares
                
                except Exception as e:
                    print(f"Error buying {symbol} on {date_str}: {e}")
            
            # Update portfolio value
            total_value = self.portfolio['cash']
            for symbol, shares in self.portfolio['assets'].items():
                if symbol in price_data.columns and date_str in price_data.index:
                    price = price_data.loc[date_str, symbol]
                    if not pd.isna(price):
                        total_value += shares * price
            
            # Record history
            self.portfolio['history'].append({
                'date': date_str,
                'cash': self.portfolio['cash'],
                'total_value': total_value,
                'weekly_investment': self.weekly_investment
            })
            
        # Calculate performance metrics
        total_invested = self.weekly_investment * len(dates)
        final_value = self.portfolio['history'][-1]['total_value']
        total_return = (final_value - total_invested) / total_invested * 100
        
        metrics = {
            'start_date': start_date,
            'end_date': end_date,
            'total_weeks': len(dates),
            'total_invested': total_invested,
            'final_value': final_value,
            'total_return': total_return
        }
        
        return metrics
        
    def _load_price_data(self):
        """Load price data for all symbols"""
        price_data = pd.DataFrame()
        
        for symbol in self.symbols:
            try:
                # Try to load from market_data directory
                symbol_file = symbol.replace('^', '')
                file_path = f"market_data/{symbol_file}_data.csv"
                
                if not os.path.exists(file_path):
                    print(f"Warning: No data found for {symbol} at {file_path}")
                    continue
                    
                df = pd.read_csv(file_path)
                
                # Set index to Date
                if 'Date' in df.columns:
                    df.set_index('Date', inplace=True)
                else:
                    df.set_index(df.columns[0], inplace=True)
                
                # Initialize price_data DataFrame with the index if it's empty
                if price_data.empty:
                    price_data = pd.DataFrame(index=df.index)
                
                # Add Close price to price_data
                if 'Close' in df.columns:
                    price_data[symbol] = df['Close']
                
            except Exception as e:
                print(f"Error loading data for {symbol}: {e}")
        
        return price_data
        
    def save_results(self, output_dir='trading_results'):
        """Save the backtest results"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Create timestamp for filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save portfolio history
        history_df = pd.DataFrame(self.portfolio['history'])
        history_df.to_csv(f"{output_dir}/dca_history_{timestamp}.csv", index=False)
        
        # Save final portfolio state
        final_portfolio = {
            'cash': float(self.portfolio['cash']),
            'assets': {k: float(v) for k, v in self.portfolio['assets'].items()},
            'total_value': float(self.portfolio['history'][-1]['total_value'])
        }
        
        with open(f"{output_dir}/dca_final_{timestamp}.json", 'w') as f:
            json.dump(final_portfolio, f, indent=4)
            
        print(f"Results saved to {output_dir} directory")


def run_sample_backtest():
    """Run a sample DCA backtest"""
    # Define symbols to invest in
    symbols = ['SPY', 'QQQ', 'VTI']
    
    # Create DCA strategy with $500 weekly investment
    strategy = SimpleDCAStrategy(symbols, weekly_investment=500)
    
    # Run backtest for the last 5 years
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
    
    # Run backtest
    metrics = strategy.run_backtest(start_date, end_date)
    
    if metrics:
        # Print metrics
        print("\nPerformance Metrics:")
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
        
        # Save results
        strategy.save_results()
        
    return strategy


if __name__ == "__main__":
    print("=== Simple Dollar-Cost Averaging Backtest ===")
    dca_strategy = run_sample_backtest()
    print("\nBacktest completed.") 