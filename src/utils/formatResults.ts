import type { StrategyResult } from '../strategies/backtest';

/**
 * Format and display backtest results
 */
export function formatResults(results: StrategyResult, symbol: string): void {
  const variantInfo = results.debugInfo?.strategyVariant || 'default';
  const weeklyContribution = results.debugInfo?.weeklyContribution || 0;
  const useLumpSum = results.debugInfo?.useLumpSum || false;
  const doubleInvestments = results.debugInfo?.doubleInvestments || 0;
  const accumulatedCashInvested = results.debugInfo?.accumulatedCashInvested || 0;
  
  console.log('\n===================================================');
  console.log(`📊 BACKTEST RESULTS FOR ${symbol}`);
  console.log(`📊 STRATEGY VARIANT: ${results.strategyName.toUpperCase()} (${variantInfo})`);
  console.log(`📊 INVESTMENT APPROACH: ${useLumpSum ? 'Lump Sum' : `Weekly $${weeklyContribution} Contributions`}`);
  console.log('===================================================');
  
  // Format numbers for display
  const formatPercent = (value: number): string => `${(value * 100).toFixed(2)}%`;
  const formatCurrency = (value: number): string => `$${value.toFixed(2)}`;
  
  // Display summary
  console.log(`\n🔍 ${results.strategyName.toUpperCase()} STRATEGY:`);
  console.log(`Variant: ${variantInfo}`);
  
  if (useLumpSum) {
    console.log(`Initial Investment: ${formatCurrency(10000)}`);
  } else {
    console.log(`Weekly Contribution: ${formatCurrency(weeklyContribution)}`);
    console.log(`Total Possible Contributions: ${results.totalContributions || 0}`);
    console.log(`Contributions Invested: ${(results.totalContributions || 0) - (results.skippedContributions || 0)}`);
    console.log(`Contributions Skipped: ${results.skippedContributions || 0}`);
    
    if (doubleInvestments > 0) {
      console.log(`Double Investments During Extreme Fear: ${doubleInvestments}`);
    }
    
    if (accumulatedCashInvested > 0) {
      console.log(`Accumulated Cash Invested: ${formatCurrency(accumulatedCashInvested)}`);
    }
    
    console.log(`Total Capital Invested: ${formatCurrency(results.totalInvested || 0)}`);
  }
  
  console.log(`Final Value: ${formatCurrency(results.finalValue)}`);
  console.log(`Total Return: ${formatPercent(results.totalReturn)}`);
  console.log(`Annualized Return: ${formatPercent(results.annualizedReturn)}`);
  console.log(`Maximum Drawdown: ${formatPercent(results.maxDrawdown)}`);
  console.log(`Total Trades: ${results.trades.length}`);
  
  // Count buy and sell trades
  const buyTrades = results.trades.filter(t => t.type === 'buy').length;
  const sellTrades = results.trades.filter(t => t.type === 'sell').length;
  console.log(`Trade Breakdown: ${buyTrades} buys, ${sellTrades} sells`);
  
  console.log(`\n🔍 BUY & HOLD STRATEGY (CONTROL):`);
  if (useLumpSum) {
    console.log(`Initial Investment: ${formatCurrency(10000)}`);
  } else {
    console.log(`Weekly Contribution: ${formatCurrency(weeklyContribution)}`);
    console.log(`Total Invested: ${formatCurrency(results.totalInvested || 0)}`);
  }
  console.log(`Final Value: ${formatCurrency(results.buyAndHoldValue)}`);
  console.log(`Total Return: ${formatPercent(results.buyAndHoldReturn)}`);
  
  // Comparison
  const outperformance = results.totalReturn - results.buyAndHoldReturn;
  console.log(`\n🔍 COMPARISON:`);
  if (outperformance > 0) {
    console.log(`✅ ${results.strategyName} (${variantInfo}) OUTPERFORMED Buy & Hold by ${formatPercent(outperformance)}`);
  } else if (outperformance < 0) {
    console.log(`❌ ${results.strategyName} (${variantInfo}) UNDERPERFORMED Buy & Hold by ${formatPercent(Math.abs(outperformance))}`);
  } else {
    console.log(`⚖️ ${results.strategyName} (${variantInfo}) MATCHED Buy & Hold performance`);
  }
  
  // Trade details
  if (results.trades.length > 0) {
    console.log(`\n🔍 TRADE DETAILS FOR ${variantInfo.toUpperCase()} (first 5):`);
    results.trades.slice(0, 5).forEach((trade, index) => {
      console.log(`Trade #${index + 1}: ${trade.date.toISOString().split('T')[0]} - ${trade.type.toUpperCase()} ${trade.shares} shares @ ${formatCurrency(trade.price)} (${trade.reason})`);
    });
    
    if (results.trades.length > 5) {
      console.log(`... and ${results.trades.length - 5} more trades`);
    }
  } else {
    console.log(`\n❗ No trades executed with ${results.strategyName} (${variantInfo}) strategy`);
  }
  
  console.log('\n===================================================\n');
} 