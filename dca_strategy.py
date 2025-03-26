import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

class DCAStrategy:
    """
    Dollar-Cost Averaging Strategy
    Invests a fixed amount weekly regardless of price
    """
    def __init__(self, weekly_investment=500, symbols=None):
        self.weekly_investment = weekly_investment
        self.symbols = symbols or ['SPY', 'QQQ', 'VTI']
        
        # Initialize portfolio
        self.portfolio = {
            'cash': 0,
            'assets': {symbol: 0 for symbol in self.symbols},
            'history': []
        }
        
    def run_backtest(self, years=5):
        """Run backtest for specified number of years"""
        # Set date range
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365*years)).strftime('%Y-%m-%d')
        
        print(f"Running DCA backtest from {start_date} to {end_date}")
        
        # Load price data
        price_data = self._load_price_data()
        
        if price_data.empty:
            print("Error: Failed to load price data")
            return
            
        # Get weekly investment dates (every Friday)
        all_dates = pd.date_range(start=start_date, end=end_date, freq='W-FRI')
        
        # Filter dates to match available price data
        valid_dates = [date.strftime('%Y-%m-%d') for date in all_dates 
                      if date.strftime('%Y-%m-%d') in price_data.index]
        
        print(f"Found {len(valid_dates)} valid investment dates")
        
        # Reset portfolio
        self.portfolio = {
            'cash': 0,
            'assets': {symbol: 0 for symbol in self.symbols},
            'history': []
        }
        
        # Process each investment date
        for date in valid_dates:
            # Add weekly investment
            self.portfolio['cash'] += self.weekly_investment
            
            # Invest equally across symbols
            amount_per_symbol = self.weekly_investment / len(self.symbols)
            
            # Buy assets
            for symbol in self.symbols:
                if symbol not in price_data.columns:
                    continue
                    
                # Get price for this date
                price = price_data.loc[date, symbol]
                
                # Skip if price is NaN
                if pd.isna(price):
                    continue
                
                # Calculate shares to buy
                shares = amount_per_symbol / price
                
                # Update portfolio
                self.portfolio['cash'] -= amount_per_symbol
                self.portfolio['assets'][symbol] += shares
            
            # Calculate portfolio value
            assets_value = sum(
                self.portfolio['assets'][symbol] * price_data.loc[date, symbol]
                for symbol in self.symbols
                if symbol in price_data.columns and not pd.isna(price_data.loc[date, symbol])
            )
            total_value = self.portfolio['cash'] + assets_value
            
            # Save portfolio state
            self.portfolio['history'].append({
                'date': date,
                'cash': self.portfolio['cash'],
                'assets_value': assets_value,
                'total_value': total_value
            })
            
        # Calculate results
        self._calculate_results()
        
    def _load_price_data(self):
        """Load Close price data for symbols"""
        # Create empty DataFrame
        price_data = pd.DataFrame()
        
        # Load data for each symbol
        for symbol in self.symbols:
            file_path = f"market_data/{symbol}_data.csv"
            
            if not os.path.exists(file_path):
                print(f"Warning: No data found for {symbol}")
                continue
                
            try:
                # Load data
                df = pd.read_csv(file_path)
                
                # Convert date to datetime and set as index
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
                
                # Convert dates to YYYY-MM-DD format
                df.index = df.index.strftime('%Y-%m-%d')
                
                # Add Close price to price_data
                if price_data.empty:
                    price_data = pd.DataFrame(index=df.index)
                    
                price_data[symbol] = df['Close']
                
            except Exception as e:
                print(f"Error loading data for {symbol}: {e}")
                
        return price_data
        
    def _calculate_results(self):
        """Calculate and print performance results"""
        if not self.portfolio['history']:
            print("No history to calculate results")
            return
            
        # Get first and last entries
        first_entry = self.portfolio['history'][0]
        last_entry = self.portfolio['history'][-1]
        
        # Calculate metrics
        num_weeks = len(self.portfolio['history'])
        total_invested = self.weekly_investment * num_weeks
        final_value = last_entry['total_value']
        total_return = (final_value - total_invested) / total_invested * 100
        
        # Calculate annualized return
        years = num_weeks / 52
        annualized_return = ((1 + total_return/100) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # Print results
        print("\nDCA Strategy Results:")
        print(f"Investment period: {first_entry['date']} to {last_entry['date']} ({num_weeks} weeks)")
        print(f"Weekly investment: ${self.weekly_investment:.2f}")
        print(f"Total invested: ${total_invested:.2f}")
        print(f"Final portfolio value: ${final_value:.2f}")
        print(f"Total return: {total_return:.2f}%")
        print(f"Annualized return: {annualized_return:.2f}%")
        
        # Print final portfolio allocation
        print("\nFinal Portfolio Allocation:")
        print(f"Cash: ${self.portfolio['cash']:.2f}")
        
        total_assets = sum(self.portfolio['assets'].values())
        for symbol, shares in self.portfolio['assets'].items():
            percentage = (shares / total_assets * 100) if total_assets > 0 else 0
            print(f"{symbol}: {shares:.2f} shares ({percentage:.2f}%)")
            
    def save_results(self):
        """Save backtest results to file"""
        if not self.portfolio['history']:
            print("No results to save")
            return
            
        # Create output directory
        output_dir = 'trading_results'
        os.makedirs(output_dir, exist_ok=True)
        
        # Create timestamp for filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save history to CSV
        history_df = pd.DataFrame(self.portfolio['history'])
        history_file = f"{output_dir}/dca_history_{timestamp}.csv"
        history_df.to_csv(history_file, index=False)
        
        # Save final portfolio state to JSON
        portfolio_state = {
            'cash': float(self.portfolio['cash']),
            'assets': {k: float(v) for k, v in self.portfolio['assets'].items()},
            'total_invested': float(self.weekly_investment * len(self.portfolio['history'])),
            'final_value': float(self.portfolio['history'][-1]['total_value'])
        }
        
        portfolio_file = f"{output_dir}/dca_portfolio_{timestamp}.json"
        with open(portfolio_file, 'w') as f:
            json.dump(portfolio_state, f, indent=4)
            
        print(f"\nResults saved to:")
        print(f"- {history_file}")
        print(f"- {portfolio_file}")


class FearGreedBasedStrategy(DCAStrategy):
    """
    Strategy that adjusts DCA based on Fear & Greed Index
    Invests more during fear, less during greed
    """
    def __init__(self, weekly_investment=500, symbols=None):
        super().__init__(weekly_investment, symbols)
        
    def run_backtest(self, years=5):
        """Run backtest with Fear & Greed adjustments"""
        # Set date range
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365*years)).strftime('%Y-%m-%d')
        
        print(f"Running Fear & Greed-based backtest from {start_date} to {end_date}")
        
        # Load price data with Fear & Greed indices
        price_data, fear_greed_data = self._load_price_and_fg_data()
        
        if price_data.empty:
            print("Error: Failed to load price data")
            return
            
        # Get weekly investment dates (every Friday)
        all_dates = pd.date_range(start=start_date, end=end_date, freq='W-FRI')
        
        # Filter dates to match available price data
        valid_dates = [date.strftime('%Y-%m-%d') for date in all_dates 
                      if date.strftime('%Y-%m-%d') in price_data.index]
        
        print(f"Found {len(valid_dates)} valid investment dates")
        
        # Reset portfolio
        self.portfolio = {
            'cash': 0,
            'assets': {symbol: 0 for symbol in self.symbols},
            'history': []
        }
        
        # Base weekly investment amount
        base_investment = self.weekly_investment
        
        # Process each investment date
        for date in valid_dates:
            # Get Fear & Greed Index for SPY as market indicator
            fg_index = 50  # Default neutral value
            
            if 'SPY' in fear_greed_data and date in fear_greed_data['SPY'].index:
                fg_index = fear_greed_data['SPY'].loc[date, 'Fear_Greed_Index']
            
            # Adjust investment based on Fear & Greed Index
            # More investment during fear (low index), less during greed (high index)
            adjustment_factor = 1 + (50 - fg_index) / 100  # Range: 0.5 to 1.5
            adjusted_investment = base_investment * adjustment_factor
            
            # Add adjusted weekly investment
            self.portfolio['cash'] += adjusted_investment
            
            # Invest equally across symbols
            amount_per_symbol = adjusted_investment / len(self.symbols)
            
            # Buy assets
            for symbol in self.symbols:
                if symbol not in price_data.columns:
                    continue
                    
                # Get price for this date
                price = price_data.loc[date, symbol]
                
                # Skip if price is NaN
                if pd.isna(price):
                    continue
                
                # Calculate shares to buy
                shares = amount_per_symbol / price
                
                # Update portfolio
                self.portfolio['cash'] -= amount_per_symbol
                self.portfolio['assets'][symbol] += shares
            
            # Calculate portfolio value
            assets_value = sum(
                self.portfolio['assets'][symbol] * price_data.loc[date, symbol]
                for symbol in self.symbols
                if symbol in price_data.columns and not pd.isna(price_data.loc[date, symbol])
            )
            total_value = self.portfolio['cash'] + assets_value
            
            # Save portfolio state
            self.portfolio['history'].append({
                'date': date,
                'fear_greed_index': fg_index,
                'investment': adjusted_investment,
                'cash': self.portfolio['cash'],
                'assets_value': assets_value,
                'total_value': total_value
            })
            
        # Calculate results
        self._calculate_fg_results()
        
    def _load_price_and_fg_data(self):
        """Load price data and Fear & Greed indices"""
        # Create empty DataFrames
        price_data = pd.DataFrame()
        fear_greed_data = {}
        
        # Load data for each symbol
        for symbol in self.symbols:
            file_path = f"market_data/{symbol}_data.csv"
            
            if not os.path.exists(file_path):
                print(f"Warning: No data found for {symbol}")
                continue
                
            try:
                # Load data
                df = pd.read_csv(file_path)
                
                # Convert date to datetime and set as index
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
                
                # Convert dates to YYYY-MM-DD format
                df.index = df.index.strftime('%Y-%m-%d')
                
                # Add Close price to price_data
                if price_data.empty:
                    price_data = pd.DataFrame(index=df.index)
                    
                price_data[symbol] = df['Close']
                
                # Store Fear & Greed data if available
                if 'Fear_Greed_Index' in df.columns:
                    fear_greed_df = pd.DataFrame(index=df.index)
                    fear_greed_df['Fear_Greed_Index'] = df['Fear_Greed_Index']
                    fear_greed_data[symbol] = fear_greed_df
                
            except Exception as e:
                print(f"Error loading data for {symbol}: {e}")
                
        return price_data, fear_greed_data
        
    def _calculate_fg_results(self):
        """Calculate and print performance results for Fear & Greed strategy"""
        if not self.portfolio['history']:
            print("No history to calculate results")
            return
            
        # Get first and last entries
        first_entry = self.portfolio['history'][0]
        last_entry = self.portfolio['history'][-1]
        
        # Calculate metrics
        num_weeks = len(self.portfolio['history'])
        total_invested = sum(entry['investment'] for entry in self.portfolio['history'])
        final_value = last_entry['total_value']
        total_return = (final_value - total_invested) / total_invested * 100
        
        # Calculate annualized return
        years = num_weeks / 52
        annualized_return = ((1 + total_return/100) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # Print results
        print("\nFear & Greed-based Strategy Results:")
        print(f"Investment period: {first_entry['date']} to {last_entry['date']} ({num_weeks} weeks)")
        print(f"Base weekly investment: ${self.weekly_investment:.2f}")
        print(f"Total invested: ${total_invested:.2f}")
        print(f"Final portfolio value: ${final_value:.2f}")
        print(f"Total return: {total_return:.2f}%")
        print(f"Annualized return: {annualized_return:.2f}%")
        
        # Print final portfolio allocation
        print("\nFinal Portfolio Allocation:")
        print(f"Cash: ${self.portfolio['cash']:.2f}")
        
        total_assets = sum(self.portfolio['assets'].values())
        for symbol, shares in self.portfolio['assets'].items():
            percentage = (shares / total_assets * 100) if total_assets > 0 else 0
            print(f"{symbol}: {shares:.2f} shares ({percentage:.2f}%)")
            
    def save_results(self):
        """Save backtest results to file"""
        if not self.portfolio['history']:
            print("No results to save")
            return
            
        # Create output directory
        output_dir = 'trading_results'
        os.makedirs(output_dir, exist_ok=True)
        
        # Create timestamp for filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save history to CSV
        history_df = pd.DataFrame(self.portfolio['history'])
        history_file = f"{output_dir}/fear_greed_history_{timestamp}.csv"
        history_df.to_csv(history_file, index=False)
        
        # Save final portfolio state to JSON
        portfolio_state = {
            'cash': float(self.portfolio['cash']),
            'assets': {k: float(v) for k, v in self.portfolio['assets'].items()},
            'total_invested': float(sum(entry['investment'] for entry in self.portfolio['history'])),
            'final_value': float(self.portfolio['history'][-1]['total_value'])
        }
        
        portfolio_file = f"{output_dir}/fear_greed_portfolio_{timestamp}.json"
        with open(portfolio_file, 'w') as f:
            json.dump(portfolio_state, f, indent=4)
            
        print(f"\nResults saved to:")
        print(f"- {history_file}")
        print(f"- {portfolio_file}")


if __name__ == "__main__":
    print("=== Dollar-Cost Averaging Backtest ===\n")
    
    # Test DCA Strategy
    dca = DCAStrategy(weekly_investment=500, symbols=['SPY', 'QQQ', 'VTI'])
    dca.run_backtest(years=5)
    dca.save_results()
    
    print("\n=== Fear & Greed-based Strategy Backtest ===\n")
    
    # Test Fear & Greed Strategy
    fg_strategy = FearGreedBasedStrategy(weekly_investment=500, symbols=['SPY', 'QQQ', 'VTI'])
    fg_strategy.run_backtest(years=5)
    fg_strategy.save_results()
    
    print("\nBacktest completed.") 