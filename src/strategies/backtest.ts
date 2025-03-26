import type { MarketDataPoint, FearGreedDataPoint } from '../data/fetchData';

// Types
export interface BacktestParams {
  marketData: MarketDataPoint[];
  fearGreedData: FearGreedDataPoint[];
  symbol: string;
  initialCapital: number;
  strategyVariant?: 'default' | 'extreme-only' | 'extreme-fear-hold' | 'combined';
  weeklyContribution?: number; // Added weekly contribution parameter
  useLumpSum?: boolean; // Flag to determine if we use lump sum or periodic investing
}

export interface Trade {
  date: Date;
  type: 'buy' | 'sell';
  price: number;
  shares: number;
  value: number;
  reason: string;
}

export interface StrategyResult {
  symbol: string;
  strategyName: string;
  trades: Trade[];
  finalValue: number;
  totalReturn: number;
  annualizedReturn: number;
  maxDrawdown: number;
  buyAndHoldValue: number;
  buyAndHoldReturn: number;
  skippedContributions: number; // Track skipped contributions
  totalContributions: number; // Track total possible contributions
  totalInvested: number; // Track how much was actually invested
  debugInfo?: any; // Add debug info field
}

// Constants for Fear & Greed strategy
const DEFAULT_FEAR_THRESHOLD = 40; // Default threshold if not set in .env
const DEFAULT_GREED_THRESHOLD = 85; // Threshold for considering the market extremely greedy
const EXTREME_FEAR_THRESHOLD = 20; // Threshold for extreme fear
const EXTREME_GREED_THRESHOLD = 80; // Threshold for extreme greed
const FEAR_THRESHOLD = parseInt(process.env.FEAR_THRESHOLD || `${DEFAULT_FEAR_THRESHOLD}`);
const GREED_THRESHOLD = parseInt(process.env.GREED_THRESHOLD || `${DEFAULT_GREED_THRESHOLD}`);
console.log(`Using Fear Threshold: ${FEAR_THRESHOLD}, Greed Threshold: ${GREED_THRESHOLD}`);
console.log(`Extreme Fear Threshold: ${EXTREME_FEAR_THRESHOLD}, Extreme Greed Threshold: ${EXTREME_GREED_THRESHOLD}`);

// Percentage of capital to allocate on each buy signal
const ALLOCATION_PERCENTAGE = 0.4; // 40% of remaining capital

// Percentage of positions to sell on each sell signal
const SELL_PERCENTAGE = 0.3; // Sell 30% of position when greed is detected

// Minimum profit percentage required before selling
const MIN_PROFIT_PERCENT = 0.10; // Only sell if price is at least 10% higher than buy price

// Moving average periods for trend detection
const TREND_MA_PERIOD = 50; // Use a 50-day moving average for trend detection

// Enable fractional shares - this allows buying partial shares of expensive assets like NYSE
const ENABLE_FRACTIONAL_SHARES = true;

// Default weekly contribution amount
const DEFAULT_WEEKLY_CONTRIBUTION = 500;

// Days in a week for calculating weekly contributions
const DAYS_IN_WEEK = 7;

/**
 * Find the closest Fear & Greed data point for a given market date
 */
function findClosestFearGreedData(date: Date, fearGreedData: FearGreedDataPoint[]): FearGreedDataPoint | null {
  if (fearGreedData.length === 0) {
    return null;
  }

  // Get the date string in YYYY-MM-DD format for comparison
  const dateStr = date.toISOString().split('T')[0];
  
  // Try to find an exact match first
  const exactMatch = fearGreedData.find(item => {
    return item.date.toISOString().split('T')[0] === dateStr;
  });
  
  if (exactMatch) {
    return exactMatch;
  }
  
  // If no exact match, find the closest previous data point
  const timestamp = date.getTime();
  let closestIndex = -1;
  let minDiff = Infinity;
  
  for (let i = 0; i < fearGreedData.length; i++) {
    const item = fearGreedData[i];
    if (!item) continue; // Skip if item is undefined
    
    const diff = Math.abs(item.date.getTime() - timestamp);
    if (diff < minDiff) {
      minDiff = diff;
      closestIndex = i;
    }
  }
  
  if (closestIndex >= 0) {
    const closestItem = fearGreedData[closestIndex];
    if (closestItem) {
      return closestItem;
    }
  }
  
  return null;
}

/**
 * Calculate the maximum drawdown percentage
 */
function calculateMaxDrawdown(equityCurve: number[]): number {
  if (equityCurve.length === 0) {
    return 0;
  }
  
  const firstValue = equityCurve[0];
  if (firstValue === undefined) {
    return 0;
  }
  
  let maxDrawdown = 0;
  let peak = firstValue;
  
  for (let i = 0; i < equityCurve.length; i++) {
    const value = equityCurve[i];
    if (value === undefined) continue;
    
    if (value > peak) {
      peak = value;
    } else if (peak > 0) { // Protect against division by zero
      const drawdown = (peak - value) / peak;
      maxDrawdown = Math.max(maxDrawdown, drawdown);
    }
  }
  
  return maxDrawdown;
}

/**
 * Calculate a simple moving average of price data
 */
function calculateMovingAverage(data: MarketDataPoint[], periods: number, endIndex: number): number | null {
  if (endIndex < periods - 1 || periods <= 0) {
    return null;
  }
  
  let sum = 0;
  let count = 0;
  
  for (let i = Math.max(0, endIndex - periods + 1); i <= endIndex; i++) {
    const item = data[i];
    if (!item) continue;
    sum += item.close;
    count++;
  }
  
  return count > 0 ? sum / count : null;
}

/**
 * Determine if the market is in a downtrend
 * Returns true if current price is below the moving average
 */
function isInDowntrend(data: MarketDataPoint[], currentIndex: number): boolean {
  if (currentIndex < TREND_MA_PERIOD) {
    return false; // Not enough data to determine trend
  }
  
  const ma = calculateMovingAverage(data, TREND_MA_PERIOD, currentIndex);
  if (!ma) return false;
  
  const currentPrice = data[currentIndex]?.close;
  if (!currentPrice) return false;
  
  return currentPrice < ma;
}

/**
 * Determine the appropriate cooldown period based on data frequency
 */
function determineCooldownPeriod(marketData: MarketDataPoint[]): number {
  if (marketData.length < 2) return 20; // Default for insufficient data
  
  // Calculate average days between data points
  const dateDiffs: number[] = [];
  for (let i = 1; i < Math.min(10, marketData.length); i++) {
    const current = marketData[i];
    const previous = marketData[i-1];
    if (!current || !previous || !current.date || !previous.date) continue;
    
    const diff = current.date.getTime() - previous.date.getTime();
    dateDiffs.push(diff / (1000 * 60 * 60 * 24)); // Convert to days
  }
  
  const avgDaysBetweenPoints = dateDiffs.reduce((sum, val) => sum + val, 0) / dateDiffs.length;
  
  // If data is less frequent (e.g., quarterly), use shorter cooldown
  if (avgDaysBetweenPoints > 20) {
    return 1; // Just 1 period cooldown for quarterly data
  } else if (avgDaysBetweenPoints > 5) {
    return 3; // 3 periods for weekly/monthly data
  } else {
    return 15; // 15 days for daily data (shorter than previous 20)
  }
}

/**
 * Determine if it's a good time to invest based on fear & greed and strategy variant
 */
function shouldInvestWeeklyAmount(
  fearGreedValue: number | undefined, 
  inDowntrend: boolean,
  strategyVariant: string
): boolean {
  if (fearGreedValue === undefined) return false;
  
  // Default strategy - invest during fear
  if (strategyVariant === 'default' && fearGreedValue <= FEAR_THRESHOLD) {
    return true;
  }
  
  // Extreme-only strategy - only invest during extreme fear
  if (strategyVariant === 'extreme-only' && fearGreedValue <= EXTREME_FEAR_THRESHOLD) {
    return true;
  }
  
  // Extreme-fear-hold strategy - invest during extreme fear even in downtrend
  if (strategyVariant === 'extreme-fear-hold' && fearGreedValue <= EXTREME_FEAR_THRESHOLD) {
    return true;
  }
  
  // Combined strategy - invest in regular fear or extreme fear
  if (strategyVariant === 'combined' && 
     (fearGreedValue <= FEAR_THRESHOLD || fearGreedValue <= EXTREME_FEAR_THRESHOLD)) {
    return true;
  }
  
  // Additional consideration - avoid investing in downtrends unless in extreme fear
  if (inDowntrend && fearGreedValue > EXTREME_FEAR_THRESHOLD) {
    return false;
  }
  
  return false;
}

/**
 * Determine if we should invest double the amount due to extreme fear
 */
function shouldInvestDouble(fearGreedValue: number | undefined): boolean {
  return fearGreedValue !== undefined && fearGreedValue <= EXTREME_FEAR_THRESHOLD;
}

/**
 * Run backtest comparing Fear & Greed strategy vs. Buy and Hold
 */
export async function runBacktest(params: BacktestParams): Promise<StrategyResult> {
  const { 
    marketData, 
    fearGreedData, 
    symbol, 
    initialCapital, 
    strategyVariant = 'default',
    weeklyContribution = DEFAULT_WEEKLY_CONTRIBUTION,
    useLumpSum = false
  } = params;
  
  let strategyName = "Fear & Greed";
  switch(strategyVariant) {
    case 'extreme-only':
      strategyName = "Extreme Fear & Greed Only";
      break;
    case 'extreme-fear-hold':
      strategyName = "Extreme Fear Buy & Hold";
      break;
    case 'combined':
      strategyName = "Combined Approach";
      break;
  }
  
  // Debug information to capture why trades aren't generated
  const debugInfo = {
    totalPossibleTrades: 0,
    noFearGreedData: 0,
    fearGreedAboveThreshold: 0,
    noCash: 0,
    inCooldown: 0,
    zeroShares: 0,
    executedBuys: 0,
    executedSells: 0,
    sellOpportunities: 0,
    insufficientProfit: 0,
    inDowntrend: 0,
    notExtremeFear: 0,
    notExtremeGreed: 0,
    strategyVariant,
    weeklyContribution,
    useLumpSum,
    weeklyContributionsSkipped: 0,
    weeklyContributionsInvested: 0,
    doubleInvestments: 0,
    cashAccumulated: 0,
    accumulatedCashInvested: 0,
    dataFrequency: "unknown",
    samplePrice: symbol === 'NYSE' ? marketData.slice(0, 5).map(d => d.close) : null,
    sampleFearGreed: fearGreedData.slice(0, 5).map(d => ({ date: d.date.toISOString(), value: d.value })),
    firstFewDays: marketData.slice(0, 5).map(d => ({ 
      date: d.date.toISOString(),
      price: d.close,
      fearGreed: findClosestFearGreedData(d.date, fearGreedData)?.value || null
    })),
  };
  
  // Ensure we have market data
  if (marketData.length === 0) {
    throw new Error(`No market data available for ${symbol}`);
  }
  
  // Get first day data safely
  const firstDayData = marketData[0];
  if (!firstDayData) {
    throw new Error(`Invalid market data for ${symbol}`);
  }
  
  // Determine the cooldown period based on data frequency
  const cooldownPeriods = determineCooldownPeriod(marketData);
  
  // Calculate average days between data points to understand data frequency
  if (marketData.length >= 2) {
    const dateDiffs: number[] = [];
    for (let i = 1; i < Math.min(10, marketData.length); i++) {
      const current = marketData[i];
      const previous = marketData[i-1];
      if (!current || !previous || !current.date || !previous.date) continue;
      
      const diff = current.date.getTime() - previous.date.getTime();
      dateDiffs.push(diff / (1000 * 60 * 60 * 24)); // Convert to days
    }
    
    const avgDaysBetweenPoints = dateDiffs.reduce((sum, val) => sum + val, 0) / dateDiffs.length;
    
    if (avgDaysBetweenPoints > 60) {
      debugInfo.dataFrequency = "quarterly";
    } else if (avgDaysBetweenPoints > 25) {
      debugInfo.dataFrequency = "monthly";
    } else if (avgDaysBetweenPoints > 5) {
      debugInfo.dataFrequency = "weekly";
    } else {
      debugInfo.dataFrequency = "daily";
    }
  }
  
  // Keep track of trades and portfolio for Fear & Greed strategy
  const trades: Trade[] = [];
  let cash = useLumpSum ? initialCapital : 0; // Start with 0 if using weekly contributions
  let shares = 0;
  let equityCurve: number[] = [useLumpSum ? initialCapital : 0];
  let lastBuyDate: Date | null = null;
  let lastBuyPrice: number | null = null;
  let lastSellDate: Date | null = null;
  let totalInvested = useLumpSum ? initialCapital : 0; // Track total invested amount
  let skippedContributions = 0;
  let totalContributions = 0;
  
  // For the improved weekly strategy
  let accumulatedCash = 0; // Cash that was skipped but will be invested during extreme fear
  
  // Buy and Hold comparison strategy
  let buyAndHoldCash = useLumpSum ? initialCapital : 0;
  let buyAndHoldShares = 0;
  
  if (useLumpSum) {
    // For lump sum, buy on the first day
    buyAndHoldShares = initialCapital / firstDayData.close;
    console.log(`${symbol} First Day Price: ${firstDayData.close}, Buy and Hold Shares: ${buyAndHoldShares}`);
  }
  
  // Store the starting date to track weekly contributions
  const contributionStartDate = new Date(firstDayData.date);
  let lastContributionDate = new Date(contributionStartDate);
  
  // Loop through each trading day
  for (let i = 0; i < marketData.length; i++) {
    const currentDay = marketData[i];
    // Skip if we have invalid day data
    if (!currentDay) continue;
    
    debugInfo.totalPossibleTrades++;
    
    const fearGreedToday = findClosestFearGreedData(currentDay.date, fearGreedData);
    
    // Check if it's time for a weekly contribution
    if (!useLumpSum) {
      const daysSinceLastContribution = (currentDay.date.getTime() - lastContributionDate.getTime()) / (1000 * 60 * 60 * 24);
      
      if (daysSinceLastContribution >= DAYS_IN_WEEK) {
        // Time for a new weekly contribution
        totalContributions++;
        lastContributionDate = new Date(currentDay.date);
        
        // Add to buy and hold strategy unconditionally
        buyAndHoldCash += weeklyContribution;
        const newBuyAndHoldShares = buyAndHoldCash / currentDay.close;
        buyAndHoldShares += newBuyAndHoldShares;
        buyAndHoldCash = 0;
        
        // For our strategic approach, decide whether to invest based on market conditions
        const inDowntrend = isInDowntrend(marketData, i);
        if (shouldInvestWeeklyAmount(fearGreedToday?.value, inDowntrend, strategyVariant)) {
          // Good time to invest the weekly contribution
          // Check if we should double the investment during extreme fear
          const doubleInvestment = shouldInvestDouble(fearGreedToday?.value);
          
          // Calculate how much to invest
          let amountToInvest = weeklyContribution;
          
          if (doubleInvestment) {
            amountToInvest *= 2; // Double the contribution
            debugInfo.doubleInvestments++;
          }
          
          // Adjust for accumulated cash during extreme fear
          if (fearGreedToday?.value !== undefined && fearGreedToday.value <= EXTREME_FEAR_THRESHOLD && accumulatedCash > 0) {
            // Also invest any accumulated cash during extreme fear
            amountToInvest += accumulatedCash;
            debugInfo.accumulatedCashInvested += accumulatedCash;
            debugInfo.cashAccumulated -= accumulatedCash;
            totalInvested += accumulatedCash;
            accumulatedCash = 0;
          }
          
          cash += amountToInvest;
          totalInvested += weeklyContribution; // Track the regular investment amount
          debugInfo.weeklyContributionsInvested++;
          
          // Buy shares immediately with the new contribution
          if (cash > 0) {
            let sharesToBuy;
            if (ENABLE_FRACTIONAL_SHARES) {
              sharesToBuy = cash / currentDay.close;
            } else {
              sharesToBuy = Math.floor(cash / currentDay.close);
            }
            
            if (sharesToBuy > 0) {
              const cost = sharesToBuy * currentDay.close;
              shares += sharesToBuy;
              cash -= cost;
              lastBuyDate = currentDay.date;
              lastBuyPrice = currentDay.close;
              debugInfo.executedBuys++;
              
              let reason = `Weekly contribution invested - Fear & Greed Index at ${fearGreedToday?.value} (${fearGreedToday?.classification})`;
              
              if (doubleInvestment) {
                reason += " - DOUBLED due to extreme fear";
              }
              
              if (amountToInvest > weeklyContribution * 2) {
                reason += ` - Including ${(amountToInvest - (doubleInvestment ? weeklyContribution * 2 : weeklyContribution)).toFixed(2)} accumulated cash`;
              }
              
              trades.push({
                date: currentDay.date,
                type: 'buy',
                price: currentDay.close,
                shares: sharesToBuy,
                value: cost,
                reason,
              });
            }
          }
        } else {
          // Not a good time to invest, accumulate cash for later
          accumulatedCash += weeklyContribution;
          debugInfo.cashAccumulated += weeklyContribution;
          skippedContributions++;
          debugInfo.weeklyContributionsSkipped++;
        }
      }
    }
    
    // Calculate current portfolio value
    const portfolioValue = cash + (shares * currentDay.close);
    equityCurve.push(portfolioValue);
    
    // Check if we're in the cooldown period after a buy or sell
    const inBuyCooldown = lastBuyDate && 
      (currentDay.date.getTime() - lastBuyDate.getTime()) < (cooldownPeriods * 24 * 60 * 60 * 1000);
    
    const inSellCooldown = lastSellDate && 
      (currentDay.date.getTime() - lastSellDate.getTime()) < (Math.ceil(cooldownPeriods / 2) * 24 * 60 * 60 * 1000);
    
    const inCooldown = inBuyCooldown || inSellCooldown;
    
    // Debug checks
    if (!fearGreedToday) {
      debugInfo.noFearGreedData++;
      continue;
    }
    
    // Check for downtrend - avoid buying in downtrends
    const inDowntrend = isInDowntrend(marketData, i);
    if (inDowntrend) {
      debugInfo.inDowntrend++;
    }
    
    // SELL STRATEGY: Only apply if we're not in extreme-fear-hold mode (which doesn't sell)
    if (strategyVariant !== 'extreme-fear-hold' && shares > 0 && lastBuyPrice !== null) {
      let shouldSell = false;
      
      // Determine if we should sell based on strategy variant
      if (strategyVariant === 'default' && fearGreedToday.value >= GREED_THRESHOLD) {
        shouldSell = true;
      } else if (strategyVariant === 'extreme-only' && fearGreedToday.value >= EXTREME_GREED_THRESHOLD) {
        shouldSell = true;
      } else if (strategyVariant === 'combined' && 
                ((fearGreedToday.value >= GREED_THRESHOLD) || 
                 (fearGreedToday.value >= EXTREME_GREED_THRESHOLD))) {
        shouldSell = true;
      }
      
      if (shouldSell) {
        debugInfo.sellOpportunities++;
        
        // Only sell if we have a minimum profit
        const currentProfit = (currentDay.close - lastBuyPrice) / lastBuyPrice;
        
        if (currentProfit >= MIN_PROFIT_PERCENT) {
          // Sell a portion of current position
          const sharesToSell = shares * SELL_PERCENTAGE;
          const sellValue = sharesToSell * currentDay.close;
          
          if (sharesToSell > 0) {
            shares -= sharesToSell;
            cash += sellValue;
            lastSellDate = currentDay.date;
            debugInfo.executedSells++;
            
            trades.push({
              date: currentDay.date,
              type: 'sell',
              price: currentDay.close,
              shares: sharesToSell,
              value: sellValue,
              reason: `Fear & Greed Index at ${fearGreedToday.value} (${fearGreedToday.classification}) - Taking ${(currentProfit * 100).toFixed(1)}% profit`,
            });
          }
        } else {
          debugInfo.insufficientProfit++;
        }
      } else if (fearGreedToday.value < EXTREME_GREED_THRESHOLD) {
        debugInfo.notExtremeGreed++;
      }
    }
    
    // Special case: Check if we have accumulated cash during extreme fear (even if it's not a weekly contribution day)
    if (!useLumpSum && 
        accumulatedCash > 0 && 
        fearGreedToday?.value !== undefined && 
        fearGreedToday.value <= EXTREME_FEAR_THRESHOLD && 
        !inCooldown) {
      
      // Invest accumulated cash during extreme fear periods
      const cashToInvest = accumulatedCash;
      cash += cashToInvest;
      accumulatedCash = 0;
      debugInfo.accumulatedCashInvested += cashToInvest;
      totalInvested += cashToInvest;
      
      // Buy shares immediately with the accumulated cash
      if (cash > 0) {
        let sharesToBuy;
        if (ENABLE_FRACTIONAL_SHARES) {
          sharesToBuy = cash / currentDay.close;
        } else {
          sharesToBuy = Math.floor(cash / currentDay.close);
        }
        
        if (sharesToBuy > 0) {
          const cost = sharesToBuy * currentDay.close;
          shares += sharesToBuy;
          cash -= cost;
          lastBuyDate = currentDay.date;
          lastBuyPrice = currentDay.close;
          debugInfo.executedBuys++;
          
          trades.push({
            date: currentDay.date,
            type: 'buy',
            price: currentDay.close,
            shares: sharesToBuy,
            value: cost,
            reason: `Accumulated cash invested - Fear & Greed Index at ${fearGreedToday?.value} (${fearGreedToday?.classification}) - EXTREME FEAR opportunity`,
          });
        }
      }
    }
    
    // BUY STRATEGY: For lump sum only (weekly contributions are handled separately)
    if (useLumpSum) {
      let shouldBuy = false;
      
      if (strategyVariant === 'default' && fearGreedToday.value <= FEAR_THRESHOLD) {
        shouldBuy = true;
      } else if (strategyVariant === 'extreme-only' && fearGreedToday.value <= EXTREME_FEAR_THRESHOLD) {
        shouldBuy = true;
      } else if (strategyVariant === 'extreme-fear-hold' && fearGreedToday.value <= EXTREME_FEAR_THRESHOLD) {
        shouldBuy = true;
      } else if (strategyVariant === 'combined' && 
                ((fearGreedToday.value <= FEAR_THRESHOLD) || 
                 (fearGreedToday.value <= EXTREME_FEAR_THRESHOLD))) {
        shouldBuy = true;
      } else {
        debugInfo.notExtremeFear++;
      }
      
      if (shouldBuy && cash > 0 && !inCooldown && 
          (strategyVariant === 'extreme-fear-hold' || !inDowntrend || fearGreedToday.value <= EXTREME_FEAR_THRESHOLD)) {
        
        // Buy with a portion of available cash based on how fearful the market is
        // More fear = larger allocation
        const fearLevel = Math.max(0, FEAR_THRESHOLD - fearGreedToday.value) / FEAR_THRESHOLD;
        
        // Extra aggressive buying for extreme fear (below 20)
        let allocationMultiplier;
        if (fearGreedToday.value <= EXTREME_FEAR_THRESHOLD) {
          // Extreme fear: allocate between 50% and 70% based on severity
          allocationMultiplier = ALLOCATION_PERCENTAGE + (fearLevel * 0.3); 
        } else {
          // Regular fear: allocate between 40% and 50% based on severity
          allocationMultiplier = ALLOCATION_PERCENTAGE + (fearLevel * 0.1);
        }
        
        const cashToSpend = cash * allocationMultiplier;
        
        // Calculate shares to buy - support fractional shares for high-priced assets like NYSE
        let sharesToBuy;
        if (ENABLE_FRACTIONAL_SHARES) {
          sharesToBuy = cashToSpend / currentDay.close;
        } else {
          sharesToBuy = Math.floor(cashToSpend / currentDay.close);
        }
        
        // Debug - print details for NYSE to understand share purchases
        if (symbol === 'NYSE' && i < 10) {
          console.log(`${symbol} [${strategyVariant}] Day ${i}: Price=${currentDay.close}, Cash=${cash}, FearLevel=${fearLevel}, Allocation=${allocationMultiplier}, CashToSpend=${cashToSpend}, SharesToBuy=${sharesToBuy}`);
        }
        
        if (sharesToBuy > 0) {
          const cost = sharesToBuy * currentDay.close;
          shares += sharesToBuy;
          cash -= cost;
          lastBuyDate = currentDay.date;
          lastBuyPrice = currentDay.close; // Record the buy price for profit tracking
          debugInfo.executedBuys++;
          
          trades.push({
            date: currentDay.date,
            type: 'buy',
            price: currentDay.close,
            shares: sharesToBuy,
            value: cost,
            reason: `Fear & Greed Index at ${fearGreedToday.value} (${fearGreedToday.classification})${inDowntrend ? ' despite downtrend' : ''}`,
          });
        } else {
          debugInfo.zeroShares++;
        }
      }
    }
  }
  
  // Get final day data safely
  const finalDay = marketData[marketData.length - 1];
  if (!finalDay) {
    throw new Error(`Invalid final market data for ${symbol}`);
  }
  
  // If we still have cash at the end, make one final purchase
  if (cash > 0) {
    // Allow fractional shares for the final purchase as well
    let finalSharesToBuy;
    if (ENABLE_FRACTIONAL_SHARES) {
      finalSharesToBuy = cash / finalDay.close;
    } else {
      finalSharesToBuy = Math.floor(cash / finalDay.close);
    }
    
    if (finalSharesToBuy > 0) {
      const cost = finalSharesToBuy * finalDay.close;
      shares += finalSharesToBuy;
      cash -= cost;
      debugInfo.executedBuys++;
      
      trades.push({
        date: finalDay.date,
        type: 'buy',
        price: finalDay.close,
        shares: finalSharesToBuy,
        value: cost,
        reason: 'Final cash allocation at end of backtest period',
      });
    } else {
      // Can't buy any shares with remaining cash
      debugInfo.zeroShares++;
    }
  }
  
  // Calculate final values
  const finalValue = cash + (shares * finalDay.close) + accumulatedCash;
  
  // For weekly contributions, calculate total investment differently
  if (!useLumpSum) {
    // Add any accumulated cash to the final value (it's already part of totalInvested)
    totalInvested += accumulatedCash;
  }
  
  // Calculate return based on actual invested amount
  const totalReturn = (finalValue / totalInvested) - 1;
  
  // Calculate annualized return
  const startDateForAnnualized = firstDayData.date;
  const endDate = finalDay.date;
  const yearFraction = (endDate.getTime() - startDateForAnnualized.getTime()) / (1000 * 60 * 60 * 24 * 365);
  const annualizedReturn = Math.pow(1 + totalReturn, 1 / yearFraction) - 1;
  
  // Calculate Buy and Hold results
  const buyAndHoldValue = buyAndHoldShares * finalDay.close;
  const buyAndHoldReturn = (buyAndHoldValue / totalInvested) - 1;
  
  // Calculate maximum drawdown
  const maxDrawdown = calculateMaxDrawdown(equityCurve);
  
  console.log(`${symbol} [${strategyVariant}] Weekly contribution: $${weeklyContribution}, Strategy: ${useLumpSum ? 'Lump Sum' : 'Periodic Investing'}`);
  console.log(`Total contributions: ${totalContributions}, Invested: ${totalContributions - skippedContributions}, Skipped: ${skippedContributions}, Double contributions: ${debugInfo.doubleInvestments}`);
  console.log(`Accumulated cash invested during extreme fear: $${debugInfo.accumulatedCashInvested.toFixed(2)}`);
  
  return {
    symbol,
    strategyName,
    trades,
    finalValue,
    totalReturn,
    annualizedReturn,
    maxDrawdown,
    buyAndHoldValue,
    buyAndHoldReturn,
    skippedContributions,
    totalContributions,
    totalInvested,
    debugInfo
  };
}

/**
 * Run all strategy variations and return the results
 */
export async function runAllStrategyVariations(params: Omit<BacktestParams, 'strategyVariant'>): Promise<StrategyResult[]> {
  const strategyVariants: ('default' | 'extreme-only' | 'extreme-fear-hold' | 'combined')[] = [
    'default',
    'extreme-only',
    'extreme-fear-hold',
    'combined'
  ];
  
  const results: StrategyResult[] = [];
  
  for (const variant of strategyVariants) {
    console.log(`\n🔄 Running ${variant} strategy for ${params.symbol}...`);
    const result = await runBacktest({
      ...params,
      strategyVariant: variant,
      useLumpSum: false, // Set to use weekly contributions by default
      weeklyContribution: 500 // $500 weekly contribution
    });
    
    results.push(result);
  }
  
  return results;
} 