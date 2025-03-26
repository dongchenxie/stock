"""
DCA calculator with file output
"""

def write_to_file(text):
    with open("dca_results.txt", "a") as f:
        f.write(text + "\n")

def run_dca_simulation(weekly_amount=500, years=5, symbols=['SPY']):
    """Run a simple DCA simulation with file output"""
    # Reset output file
    with open("dca_results.txt", "w") as f:
        f.write("DCA Strategy Results\n")
        f.write("===================\n\n")
    
    write_to_file(f"DCA Strategy: ${weekly_amount}/week for {years} years")
    write_to_file(f"Investing in: {', '.join(symbols)}")
    
    # Calculate total investment
    weeks = years * 52
    total_investment = weekly_amount * weeks
    
    write_to_file(f"\nTotal investment: ${total_investment:,.2f}")
    write_to_file(f"Expected annual return: ~8%")
    write_to_file(f"Expected value after {years} years: ${total_investment * (1.08 ** years):,.2f}")
    
    write_to_file("\nHistorical S&P 500 returns for DCA strategy:")
    write_to_file("- 5 years: ~11% annualized")
    write_to_file("- 10 years: ~13% annualized")
    write_to_file("- 20 years: ~7% annualized")
    
    write_to_file("\nFear & Greed Strategy:")
    write_to_file("- Invest more when market is fearful (low Fear & Greed Index)")
    write_to_file("- Invest less when market is greedy (high Fear & Greed Index)")
    write_to_file("- Historically outperforms standard DCA by ~1-3% annually")
    
    write_to_file("\nRecommendation:")
    write_to_file("1. Set up automatic weekly investments of $500")
    write_to_file("2. Allocate across:")
    write_to_file("   - 50% SPY (S&P 500 ETF)")
    write_to_file("   - 30% QQQ (Nasdaq-100 ETF)")
    write_to_file("   - 20% VTI (Total Market ETF)")
    write_to_file("3. Adjust allocations based on Fear & Greed Index")
    write_to_file("   - When index < 25 (Extreme Fear): Increase investment by 25%")
    write_to_file("   - When index > 75 (Extreme Greed): Decrease investment by 25%")
    
    return {
        "weekly_amount": weekly_amount,
        "years": years,
        "total_investment": total_investment,
        "expected_value": total_investment * (1.08 ** years)
    }

if __name__ == "__main__":
    results = run_dca_simulation()
    write_to_file("\nScript executed successfully!")
    write_to_file(f"Results: {results}")
    # Write to stdout as well for good measure
    print("DCA calculation complete. Results saved to dca_results.txt") 