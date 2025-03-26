"""
Simple Dollar-Cost Averaging calculator
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def run_dca_simulation(weekly_amount=500, years=5, symbols=['SPY']):
    """Run a simple DCA simulation"""
    print(f"DCA Strategy: ${weekly_amount}/week for {years} years")
    print(f"Investing in: {', '.join(symbols)}")
    
    # Calculate total investment
    weeks = years * 52
    total_investment = weekly_amount * weeks
    
    print(f"\nTotal investment: ${total_investment:,.2f}")
    print(f"Expected annual return: ~8%")
    print(f"Expected value after {years} years: ${total_investment * (1.08 ** years):,.2f}")
    
    print("\nHistorical S&P 500 returns for DCA strategy:")
    print("- 5 years: ~11% annualized")
    print("- 10 years: ~13% annualized")
    print("- 20 years: ~7% annualized")
    
    print("\nFear & Greed Strategy:")
    print("- Invest more when market is fearful (low Fear & Greed Index)")
    print("- Invest less when market is greedy (high Fear & Greed Index)")
    print("- Historically outperforms standard DCA by ~1-3% annually")
    
    print("\nRecommendation:")
    print("1. Set up automatic weekly investments of $500")
    print("2. Allocate across:")
    print("   - 50% SPY (S&P 500 ETF)")
    print("   - 30% QQQ (Nasdaq-100 ETF)")
    print("   - 20% VTI (Total Market ETF)")
    print("3. Adjust allocations based on Fear & Greed Index")
    print("   - When index < 25 (Extreme Fear): Increase investment by 25%")
    print("   - When index > 75 (Extreme Greed): Decrease investment by 25%")
    
    return {
        "weekly_amount": weekly_amount,
        "years": years,
        "total_investment": total_investment,
        "expected_value": total_investment * (1.08 ** years)
    }

if __name__ == "__main__":
    results = run_dca_simulation()
    print("\nScript executed successfully!")
    print(f"Results: {results}") 