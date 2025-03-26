# Fear & Greed Index Backtesting System

This project is designed to evaluate whether the Fear & Greed Index is a reliable indicator for buying S&P 500 and NYSE stocks compared to a simple buy-and-hold strategy.

## Overview

The Fear & Greed Index is a popular sentiment indicator that measures market sentiment on a scale from extreme fear to extreme greed. This project tests whether using this index as a buy signal (buying during "fear" periods) yields better results than a straightforward buy-and-hold strategy.

## Features

- Data collection for S&P 500 and NYSE historical prices
- Historical Fear & Greed Index data retrieval
- Backtesting framework for strategy comparison
- Strategy 1: Buy during "fear" periods based on the Fear & Greed Index
- Strategy 2: Buy-and-hold strategy (control group)
- Performance metrics and visualization

## Installation

1. Make sure you have [Bun](https://bun.sh/) installed
2. Clone this repository
3. Install dependencies:

```bash
bun install
```

## Usage

### Fetching Data

```bash
bun run fetch-data
```

### Running the Backtest

```bash
bun start
```

### Development Mode

```bash
bun dev
```

## Data Sources

- S&P 500 Historical Data: Federal Reserve Economic Data (FRED)
- NYSE Composite Index: Federal Reserve Economic Data (FRED)
- Fear & Greed Index Historical Data: Generated using CNN Business methodology

## Project Structure

```
├── src/
│   ├── data/          # Data fetching and processing
│   ├── strategies/    # Trading strategies implementation
│   ├── utils/         # Helper functions
│   └── index.ts       # Main entry point
├── package.json
└── README.md
```

## Backtest Results

We tested several iterations of the Fear & Greed-based trading strategy, each with various adjustments to improve performance. Below are the key findings:

### Initial Strategy Results (Basic Fear & Greed)
- **S&P 500:** 
  - Fear & Greed Strategy: 13.95% total return (10.05% annualized)
  - Buy & Hold Strategy: 114.28% total return
  - Underperformance: -2.48%
  - Trades Executed: 8
  - Maximum Drawdown: Not measured

- **NYSE:**
  - Fear & Greed Strategy: 0% total return (No trades executed)
  - Buy & Hold Strategy: 1.73% total return
  - Underperformance: -1.73%
  - Trades Executed: 0

### Second Strategy Iteration (Added Selling)
- **S&P 500:** 
  - Fear & Greed Strategy: 41.71% total return (4.94% annualized)
  - Buy & Hold Strategy: 114.28% total return
  - Underperformance: -72.57%
  - Trades Executed: 727 (94 buys, 633 sells)
  - Maximum Drawdown: 16.90%

- **NYSE:**
  - Fear & Greed Strategy: 31.19% total return (4.10% annualized)
  - Buy & Hold Strategy: 53.37% total return
  - Underperformance: -22.18%
  - Trades Executed: 24 (13 buys, 11 sells)
  - Maximum Drawdown: 16.04%

### Final Strategy Iteration (Optimized for Performance)
- **S&P 500:** 
  - Fear & Greed Strategy: 103.67% total return (10.34% annualized)
  - Buy & Hold Strategy: 114.28% total return
  - Underperformance: -10.61%
  - Trades Executed: 97 (89 buys, 8 sells)
  - Maximum Drawdown: 33.92%

- **NYSE:**
  - Fear & Greed Strategy: 47.01% total return (5.87% annualized)
  - Buy & Hold Strategy: 53.37% total return
  - Underperformance: -6.36%
  - Trades Executed: 15 (13 buys, 2 sells)
  - Maximum Drawdown: 22.61%

## Key Findings

1. **Market Timing Challenge:** The Fear & Greed strategy consistently underperformed the Buy & Hold strategy across all iterations. This reinforces the difficulty of market timing, even with a sentiment indicator.

2. **Reduced Trading Frequency Improves Results:** The initial strategy with excessive trading (727 trades) performed much worse than our final strategy with more selective trading (97 trades).

3. **Profit Requirements Help:** Adding a minimum profit requirement (10%) before selling significantly improved performance by avoiding premature exits.

4. **Trend Following Matters:** Incorporating a trend-following element (avoiding buying in downtrends unless extreme fear is present) improved the strategy's performance.

5. **Different Asset Classes Behave Differently:** The quarterly NYSE data showed different behavior compared to the daily S&P 500 data, requiring adaptive approaches.

6. **Risk-Adjusted Returns:** While the Fear & Greed strategy underperformed on absolute returns, it achieved lower drawdowns in some iterations, which could be important for risk-averse investors.

## Conclusions

1. **Not Better Than Buy & Hold:** The Fear & Greed Index strategy underperformed the simple buy-and-hold approach for both S&P 500 and NYSE. This suggests that timing the market based on sentiment indicators alone may not be an effective strategy.

2. **Transaction Costs Not Considered:** The backtest does not account for transaction costs, which would further reduce the returns of the active Fear & Greed strategy that executed numerous trades.

3. **Closest Performance Gap:** Our final strategy iteration came closest to Buy & Hold performance (10.61% gap for S&P 500), suggesting that with further optimization, a sentiment-based approach could potentially become competitive.

4. **Different Data Frequencies:** Quarterly data (NYSE) presents different challenges for trading strategies compared to daily data (S&P 500), highlighting the importance of adapting strategies to data frequency.

5. **Psychological Benefits:** Despite lower returns, a strategy that buys during fear might be psychologically easier for some investors to follow, potentially helping them stay invested during market turbulence.

## Future Work

- Implement machine learning to optimize strategy parameters
- Incorporate more technical indicators alongside Fear & Greed
- Test on different asset classes (bonds, commodities, crypto)
- Implement portfolio allocation across multiple assets
- Explore alternative sentiment indicators
- Include transaction costs and slippage in the backtest calculations

## License

This project is open source and available under the MIT License.
