import { config } from 'dotenv';
import { runAllStrategyVariations } from './strategies/backtest';
import type { StrategyResult } from './strategies/backtest';
import { loadSP500Data, loadNYSEData, generateExtendedFearGreedData } from './data/customDataLoader';
import { formatResults } from './utils/formatResults';

// Load environment variables
config();

console.log("🚀 Starting Stock Backtesting System with Custom Data");

async function main() {
  try {
    console.log("📊 Loading custom market data files...");
    
    // Load the custom data files
    const spyData = await loadSP500Data();
    const nyseData = await loadNYSEData();
    
    // Find the earliest and latest dates from both datasets
    const allDates = [...spyData.map(d => d.date), ...nyseData.map(d => d.date)];
    const startDate = new Date(Math.min(...allDates.map(d => d.getTime())));
    const endDate = new Date(Math.max(...allDates.map(d => d.getTime())));
    
    console.log(`Data spans from ${startDate.toISOString().split('T')[0]} to ${endDate.toISOString().split('T')[0]}`);
    
    // Generate extended fear/greed data for the entire time period
    const fearGreedData = await generateExtendedFearGreedData(startDate, endDate);
    
    console.log("⚙️ Running backtests with all strategy variants...");
    
    // Run backtest for S&P 500
    const initialCapital = parseInt(process.env.INITIAL_CAPITAL || '10000');
    console.log(`Using initial capital: $${initialCapital}`);
    
    // Get configuration from .env
    const startDateStr = process.env.START_DATE || '1990-01-01';
    const startBacktestDate = new Date(startDateStr);
    
    // Filter data to start from the configured start date
    const filteredSpyData = spyData.filter(d => d.date >= startBacktestDate);
    const filteredNyseData = nyseData.filter(d => d.date >= startBacktestDate);
    
    console.log(`Filtered data to start from ${startDateStr}. S&P 500: ${filteredSpyData.length} points, NYSE: ${filteredNyseData.length} points`);
    
    // Run all strategy variations for S&P 500
    console.log("\n🔄 Running all strategy variants for S&P 500...");
    const spyResults = await runAllStrategyVariations({
      marketData: filteredSpyData,
      fearGreedData,
      symbol: 'S&P 500',
      initialCapital,
    });
    
    // Run all strategy variations for NYSE
    console.log("\n🔄 Running all strategy variants for NYSE...");
    const nyseResults = await runAllStrategyVariations({
      marketData: filteredNyseData,
      fearGreedData,
      symbol: 'NYSE',
      initialCapital,
    });
    
    console.log("📈 Formatting and displaying results for all strategy variants...");
    
    // Display results for all strategy variants
    spyResults.forEach(result => {
      formatResults(result, 'S&P 500');
    });
    
    nyseResults.forEach(result => {
      formatResults(result, 'NYSE');
    });
    
    // Show summary of best performing strategies
    console.log("\n📊 SUMMARY OF BEST PERFORMING STRATEGIES 📊");
    console.log("===========================================");
    
    // Display best strategies if there are any results
    if (spyResults.length > 0) {
      // Find the best S&P 500 strategy
      let bestSpyIndex = 0;
      let bestSpyReturn = spyResults[0].totalReturn;
      
      for (let i = 1; i < spyResults.length; i++) {
        if (spyResults[i].totalReturn > bestSpyReturn) {
          bestSpyReturn = spyResults[i].totalReturn;
          bestSpyIndex = i;
        }
      }
      
      const bestSpy = spyResults[bestSpyIndex];
      const spyVariant = bestSpy.debugInfo?.strategyVariant || 'default';
      console.log(`S&P 500 Best Strategy: ${bestSpy.strategyName} (${spyVariant}) with ${(bestSpy.totalReturn * 100).toFixed(2)}% return`);
    } else {
      console.log("No S&P 500 strategy results available");
    }
    
    if (nyseResults.length > 0) {
      // Find the best NYSE strategy
      let bestNyseIndex = 0;
      let bestNyseReturn = nyseResults[0].totalReturn;
      
      for (let i = 1; i < nyseResults.length; i++) {
        if (nyseResults[i].totalReturn > bestNyseReturn) {
          bestNyseReturn = nyseResults[i].totalReturn;
          bestNyseIndex = i;
        }
      }
      
      const bestNyse = nyseResults[bestNyseIndex];
      const nyseVariant = bestNyse.debugInfo?.strategyVariant || 'default';
      console.log(`NYSE Best Strategy: ${bestNyse.strategyName} (${nyseVariant}) with ${(bestNyse.totalReturn * 100).toFixed(2)}% return`);
    } else {
      console.log("No NYSE strategy results available");
    }
    
    console.log("\n✅ Backtest completed successfully!");
  } catch (error) {
    console.error("❌ Error running backtest:", error);
  }
}

main(); 