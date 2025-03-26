import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
from pathlib import Path

class AlgoTradingFramework:
    """
    Framework for algorithmic trading that supports multiple strategies
    """
    def __init__(self, weekly_investment=500, initial_capital=0):
        """
        Initialize the trading framework
        
        Parameters:
        -----------
        weekly_investment : float
            Amount to invest every week
        initial_capital : float
            Initial investment capital
        """
        self.weekly_investment = weekly_investment
        self.initial_capital = initial_capital
        self.portfolio = {
            'cash': initial_capital,
            'assets': {},
            'total_value': initial_capital,
            'history': []
        }
        self.strategy = None
        self.transaction_history = []
        
        # Create directory for trading data
        self.data_dir = 'trading_data'
        os.makedirs(self.data_dir, exist_ok=True)
        
    def set_strategy(self, strategy):
        """Set the trading strategy"""
        self.strategy = strategy
        self.strategy.framework = self
        
    def run_backtest(self, start_date, end_date, symbols):
        """
        Run a backtest of the trading strategy
        
        Parameters:
        -----------
        start_date : str
            Start date in format 'YYYY-MM-DD'
        end_date : str
            End date in format 'YYYY-MM-DD'
        symbols : list
            List of symbols to include in the backtest
        """
        if self.strategy is None:
            raise ValueError("No strategy set. Use set_strategy() first.")
        
        # Initialize portfolio
        self.portfolio = {
            'cash': self.initial_capital,
            'assets': {symbol: 0 for symbol in symbols},
            'total_value': self.initial_capital,
            'history': []
        }
        
        # Get date range for weekly investments
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # Get weekly dates
        dates = pd.date_range(start=start, end=end, freq='W-FRI')
        
        # Load price data
        price_data = self._load_price_data(symbols)
        
        # Run simulation for each week
        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            
            # Skip if date is not in price data
            valid_date = date_str
            while valid_date not in price_data.index and date > start:
                date = date - timedelta(days=1)
                valid_date = date.strftime('%Y-%m-%d')
            
            if valid_date not in price_data.index:
                continue
                
            # Add weekly investment
            self.portfolio['cash'] += self.weekly_investment
            
            # Run strategy for this date
            allocations = self.strategy.generate_allocations(date_str, price_data, self.portfolio)
            
            # Execute trades
            self._execute_trades(date_str, allocations, price_data)
            
            # Update portfolio value
            self._update_portfolio_value(date_str, price_data)
            
        # Calculate performance metrics
        metrics = self._calculate_performance_metrics()
        
        # Save results
        self._save_results()
        
        return metrics
    
    def _load_price_data(self, symbols):
        """Load price data for the symbols"""
        price_data = pd.DataFrame()
        
        for symbol in symbols:
            try:
                # Try to load from market_data directory
                symbol_file = symbol.replace('^', '')
                file_path = f"market_data/{symbol_file}_data.csv"
                
                if not os.path.exists(file_path):
                    print(f"Warning: No data found for {symbol} at {file_path}")
                    continue
                    
                df = pd.read_csv(file_path, index_col=0, parse_dates=True)
                
                if price_data.empty:
                    price_data = pd.DataFrame(index=df.index)
                
                price_data[symbol] = df['Close']
                
            except Exception as e:
                print(f"Error loading data for {symbol}: {e}")
        
        return price_data
    
    def _execute_trades(self, date, allocations, price_data):
        """Execute trades based on allocations"""
        for symbol, allocation in allocations.items():
            if symbol not in price_data.columns:
                continue
                
            if date not in price_data.index:
                continue
                
            price = price_data.loc[date, symbol]
            
            if np.isnan(price):
                continue
                
            # Calculate amount to invest in this symbol
            amount_to_invest = allocation * self.portfolio['cash']
            
            # Skip if amount is too small
            if amount_to_invest < 1:
                continue
                
            # Calculate shares to buy (fractional shares allowed)
            shares = amount_to_invest / price
            
            # Update portfolio
            self.portfolio['cash'] -= amount_to_invest
            self.portfolio['assets'][symbol] = self.portfolio['assets'].get(symbol, 0) + shares
            
            # Record transaction
            transaction = {
                'date': date,
                'symbol': symbol,
                'price': price,
                'shares': shares,
                'amount': amount_to_invest,
                'type': 'buy'
            }
            self.transaction_history.append(transaction)
    
    def _update_portfolio_value(self, date, price_data):
        """Update portfolio value based on current prices"""
        assets_value = 0
        
        for symbol, shares in self.portfolio['assets'].items():
            if symbol not in price_data.columns:
                continue
                
            if date not in price_data.index:
                continue
                
            price = price_data.loc[date, symbol]
            
            if np.isnan(price):
                continue
                
            value = shares * price
            assets_value += value
        
        # Update total portfolio value
        self.portfolio['total_value'] = self.portfolio['cash'] + assets_value
        
        # Record portfolio state
        portfolio_snapshot = {
            'date': date,
            'cash': self.portfolio['cash'],
            'assets_value': assets_value,
            'total_value': self.portfolio['total_value']
        }
        self.portfolio['history'].append(portfolio_snapshot)
    
    def _calculate_performance_metrics(self):
        """Calculate performance metrics"""
        if not self.portfolio['history']:
            return {}
            
        # Convert history to DataFrame
        history_df = pd.DataFrame(self.portfolio['history'])
        history_df['date'] = pd.to_datetime(history_df['date'])
        history_df.set_index('date', inplace=True)
        
        # Calculate returns
        history_df['returns'] = history_df['total_value'].pct_change()
        
        # Calculate metrics
        total_invested = self.initial_capital + self.weekly_investment * (len(history_df) - 1)
        final_value = history_df['total_value'].iloc[-1]
        total_return = (final_value - total_invested) / total_invested * 100
        
        # Calculate annualized return
        days = (history_df.index[-1] - history_df.index[0]).days
        years = days / 365.25
        annualized_return = ((1 + total_return/100) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # Calculate Sharpe Ratio (assuming risk-free rate of 0%)
        sharpe_ratio = np.sqrt(52) * history_df['returns'].mean() / history_df['returns'].std() if history_df['returns'].std() > 0 else 0
        
        # Calculate maximum drawdown
        cumulative_returns = (1 + history_df['returns']).cumprod()
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns / running_max - 1) * 100
        max_drawdown = drawdown.min()
        
        metrics = {
            'total_invested': total_invested,
            'final_value': final_value,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown
        }
        
        return metrics
    
    def _save_results(self):
        """Save trading results"""
        # Create timestamp for filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save portfolio history
        history_df = pd.DataFrame(self.portfolio['history'])
        history_df.to_csv(f"{self.data_dir}/portfolio_history_{timestamp}.csv", index=False)
        
        # Save transaction history
        transactions_df = pd.DataFrame(self.transaction_history)
        transactions_df.to_csv(f"{self.data_dir}/transactions_{timestamp}.csv", index=False)
        
        # Save final portfolio state
        final_portfolio = {
            'cash': float(self.portfolio['cash']),
            'assets': {k: float(v) for k, v in self.portfolio['assets'].items()},
            'total_value': float(self.portfolio['total_value'])
        }
        
        with open(f"{self.data_dir}/final_portfolio_{timestamp}.json", 'w') as f:
            json.dump(final_portfolio, f, indent=4)
            
    def plot_portfolio_performance(self, save_path=None):
        """Plot portfolio performance"""
        if not self.portfolio['history']:
            print("No history to plot.")
            return
            
        # Convert history to DataFrame
        history_df = pd.DataFrame(self.portfolio['history'])
        history_df['date'] = pd.to_datetime(history_df['date'])
        history_df.set_index('date', inplace=True)
        
        # Plot performance
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 1, 1)
        plt.plot(history_df.index, history_df['total_value'], 'b-', label='Portfolio Value')
        plt.plot(history_df.index, history_df['cash'], 'g-', label='Cash')
        plt.plot(history_df.index, history_df['assets_value'], 'r-', label='Assets Value')
        plt.title('Portfolio Performance')
        plt.xlabel('Date')
        plt.ylabel('Value ($)')
        plt.legend()
        plt.grid(True)
        
        # Calculate and plot returns
        history_df['returns'] = history_df['total_value'].pct_change()
        history_df['cumulative_returns'] = (1 + history_df['returns']).cumprod() - 1
        
        plt.subplot(2, 1, 2)
        plt.plot(history_df.index, history_df['cumulative_returns'] * 100, 'b-')
        plt.title('Cumulative Returns')
        plt.xlabel('Date')
        plt.ylabel('Return (%)')
        plt.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()


class DCAStrategy:
    """
    Dollar-Cost Averaging Strategy - Baseline
    """
    def __init__(self, allocation_weights=None):
        """
        Initialize the DCA strategy
        
        Parameters:
        -----------
        allocation_weights : dict
            Dictionary of {symbol: weight} for fixed allocations
            If None, equal weight will be used
        """
        self.allocation_weights = allocation_weights
        self.framework = None
        
    def generate_allocations(self, date, price_data, portfolio):
        """
        Generate allocations for the given date
        
        Returns:
        --------
        dict
            Dictionary of {symbol: allocation} where allocation is a percentage of available cash
        """
        symbols = [col for col in price_data.columns if col in portfolio['assets']]
        
        # If no allocation weights provided, use equal weights
        if self.allocation_weights is None:
            # Equal weight for all symbols
            weight = 1.0 / len(symbols)
            return {symbol: weight for symbol in symbols}
        else:
            # Normalize weights to sum to 1
            total_weight = sum(self.allocation_weights.values())
            return {symbol: weight/total_weight for symbol, weight in self.allocation_weights.items()}


class FearGreedStrategy:
    """
    Strategy based on Fear & Greed Index
    """
    def __init__(self, allocation_weights=None, fear_greed_dir='fear_greed_data'):
        """
        Initialize the Fear & Greed strategy
        
        Parameters:
        -----------
        allocation_weights : dict
            Dictionary of {symbol: weight} for baseline allocations
            If None, equal weight will be used
        fear_greed_dir : str
            Directory containing Fear & Greed Index data
        """
        self.allocation_weights = allocation_weights
        self.fear_greed_dir = fear_greed_dir
        self.framework = None
        self.fear_greed_data = self._load_fear_greed_data()
        
    def _load_fear_greed_data(self):
        """Load Fear & Greed Index data"""
        fear_greed_data = {}
        
        # Load data for each symbol
        for file in os.listdir(self.fear_greed_dir):
            if not file.endswith('_fear_greed.csv'):
                continue
                
            symbol = file.replace('_fear_greed.csv', '')
            if symbol == 'fear_greed_summary':
                continue
                
            try:
                file_path = os.path.join(self.fear_greed_dir, file)
                df = pd.read_csv(file_path)
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
                
                # Handle case where ^ was removed from symbol
                if '^' in symbol:
                    fear_greed_data[symbol] = df
                else:
                    potential_symbols = [symbol, f'^{symbol}']
                    for sym in potential_symbols:
                        fear_greed_data[sym] = df
                        
            except Exception as e:
                print(f"Error loading Fear & Greed data for {symbol}: {e}")
        
        return fear_greed_data
        
    def generate_allocations(self, date, price_data, portfolio):
        """
        Generate allocations for the given date based on Fear & Greed Index
        
        Returns:
        --------
        dict
            Dictionary of {symbol: allocation} where allocation is a percentage of available cash
        """
        symbols = [col for col in price_data.columns if col in portfolio['assets']]
        
        # Get baseline allocations
        if self.allocation_weights is None:
            # Equal weight for all symbols
            baseline_allocations = {symbol: 1.0/len(symbols) for symbol in symbols}
        else:
            # Normalize weights to sum to 1
            total_weight = sum(self.allocation_weights.values())
            baseline_allocations = {symbol: weight/total_weight for symbol, weight in self.allocation_weights.items()}
        
        # Adjust allocations based on Fear & Greed Index
        adjusted_allocations = {}
        
        for symbol in symbols:
            # Get Fear & Greed Index for this symbol
            df = self.fear_greed_data.get(symbol)
            
            if df is None:
                # No Fear & Greed data, use baseline allocation
                adjusted_allocations[symbol] = baseline_allocations[symbol]
                continue
            
            # Convert date string to datetime
            date_dt = pd.to_datetime(date)
            
            # Find the closest date in Fear & Greed data
            if date_dt not in df.index:
                closest_date = df.index[df.index.get_indexer([date_dt], method='nearest')[0]]
            else:
                closest_date = date_dt
            
            # Get Fear & Greed Index
            fear_greed_value = df.loc[closest_date, 'Fear_Greed_Index']
            
            # Adjust allocation based on Fear & Greed Index
            # When Fear is high (low index), increase allocation
            # When Greed is high (high index), decrease allocation
            adjustment_factor = (50 - fear_greed_value) / 50  # -1 to 1
            
            # Apply a dampened adjustment
            allocation_adjustment = adjustment_factor * 0.2  # Adjust by up to 20%
            
            # Apply adjustment to baseline allocation
            adjusted_allocation = baseline_allocations[symbol] * (1 + allocation_adjustment)
            
            adjusted_allocations[symbol] = adjusted_allocation
        
        # Normalize adjusted allocations to sum to 1
        total_adjusted = sum(adjusted_allocations.values())
        normalized_allocations = {symbol: alloc/total_adjusted for symbol, alloc in adjusted_allocations.items()}
        
        return normalized_allocations


def run_sample_dca_backtest():
    """Run a sample backtest using DCA strategy"""
    # Initialize the framework
    framework = AlgoTradingFramework(weekly_investment=500, initial_capital=0)
    
    # Set DCA strategy with equal weights
    strategy = DCAStrategy()
    framework.set_strategy(strategy)
    
    # Define symbols for the backtest
    symbols = ['SPY', 'QQQ', 'VTI']
    
    # Run backtest for last 5 years
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
    
    print(f"Running DCA backtest from {start_date} to {end_date}")
    metrics = framework.run_backtest(start_date, end_date, symbols)
    
    # Print metrics
    print("\nPerformance Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value:.2f}")
    
    # Plot results
    plot_path = f"{framework.data_dir}/dca_performance_plot.png"
    framework.plot_portfolio_performance(save_path=plot_path)
    print(f"\nPerformance plot saved to: {plot_path}")
    
    return framework


def run_sample_fear_greed_backtest():
    """Run a sample backtest using Fear & Greed strategy"""
    # Initialize the framework
    framework = AlgoTradingFramework(weekly_investment=500, initial_capital=0)
    
    # Set Fear & Greed strategy with equal weights
    strategy = FearGreedStrategy()
    framework.set_strategy(strategy)
    
    # Define symbols for the backtest
    symbols = ['SPY', 'QQQ', 'VTI']
    
    # Run backtest for last 5 years
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
    
    print(f"Running Fear & Greed backtest from {start_date} to {end_date}")
    metrics = framework.run_backtest(start_date, end_date, symbols)
    
    # Print metrics
    print("\nPerformance Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value:.2f}")
    
    # Plot results
    plot_path = f"{framework.data_dir}/fear_greed_performance_plot.png"
    framework.plot_portfolio_performance(save_path=plot_path)
    print(f"\nPerformance plot saved to: {plot_path}")
    
    return framework


if __name__ == "__main__":
    # Run the sample backtests
    print("=== Running Dollar-Cost Averaging (DCA) Strategy ===")
    dca_framework = run_sample_dca_backtest()
    
    print("\n=== Running Fear & Greed Strategy ===")
    fg_framework = run_sample_fear_greed_backtest()
    
    print("\nBacktests completed. Check trading_data directory for results.") 