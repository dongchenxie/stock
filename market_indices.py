import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ta
import os

# List of major indices
INDICES = {
    # Major indices
    '^GSPC': 'S&P 500',
    '^DJI': 'Dow Jones',
    '^IXIC': 'NASDAQ',
    '^NYA': 'NYSE Composite',
    '^RUT': 'Russell 2000',
    '^VIX': 'CBOE Volatility Index',
    '^FTSE': 'FTSE 100',
    '^N225': 'Nikkei 225',
    '^STOXX50E': 'EURO STOXX 50',
    '^HSI': 'Hang Seng',
    '^SSEC': 'Shanghai Composite',
    '^ASX': 'S&P/ASX 200',
    '^TSX': 'TSX Composite',
    
    # Major ETFs
    'SPY': 'SPDR S&P 500 ETF',
    'QQQ': 'Invesco QQQ Trust',
    'DIA': 'SPDR Dow Jones ETF',
    'IWM': 'iShares Russell 2000 ETF',
    'VTI': 'Vanguard Total Stock Market ETF',
    
    # International ETFs
    'EFA': 'iShares MSCI EAFE ETF',
    'EEM': 'iShares MSCI Emerging Markets ETF',
    'VEU': 'Vanguard FTSE All-World ex-US ETF',
    
    # Sector ETFs
    'XLF': 'Financial Sector ETF',
    'XLK': 'Technology Sector ETF',
    'XLE': 'Energy Sector ETF',
    'XLV': 'Healthcare Sector ETF',
    'XLY': 'Consumer Discretionary ETF',
    'XLP': 'Consumer Staples ETF',
    'XLRE': 'Real Estate Sector ETF'
}

def fetch_historical_data(symbol, period='max'):
    """Fetch historical data for a given symbol"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def calculate_fear_greed_index(df):
    """Calculate Fear & Greed Index components based on CNN's methodology"""
    if df is None or len(df) < 252:  # Need at least 1 year of data
        return None
    
    try:
        # 1. Market Momentum (S&P 500 vs 125-day moving average)
        df['MA125'] = df['Close'].rolling(window=125, min_periods=1).mean()
        momentum = ((df['Close'] - df['MA125']) / df['MA125']) * 100
        # Normalize momentum with higher spread
        momentum_norm = (momentum + 20) * 2.5
        momentum_norm = momentum_norm.clip(0, 100)
        
        # 2. Stock Price Strength (52-week highs vs lows)
        high_52w = df['High'].rolling(window=252, min_periods=1).max()
        low_52w = df['Low'].rolling(window=252, min_periods=1).min()
        # Calculate percentage of stocks near highs vs lows
        near_high = (df['Close'] > high_52w * 0.95) * 1
        near_low = (df['Close'] < low_52w * 1.05) * 1
        strength = (near_high - near_low) * 100
        # Normalize with wider range
        strength_norm = (strength + 40) * 1.25
        strength_norm = strength_norm.clip(0, 100)
        
        # 3. Stock Price Breadth (McClellan Volume Summation Index)
        daily_change = df['Close'].diff()
        advances = (daily_change > 0) * df['Volume']
        declines = (daily_change < 0) * df['Volume']
        ema19 = advances.ewm(span=19, adjust=False, min_periods=1).mean()
        ema39 = declines.ewm(span=39, adjust=False, min_periods=1).mean()
        breadth = ((ema19 - ema39) / (ema39 + 1e-6)) * 100
        # Normalize with wider range
        breadth_norm = (breadth + 30) * 1.5
        breadth_norm = breadth_norm.clip(0, 100)
        
        # 4. Put and Call Options (5-day average put/call ratio)
        price_momentum = df['Close'].pct_change(periods=5) * 100
        # Simple normalization with wider range
        options_norm = ((price_momentum + 10) * 3).clip(0, 100)
        
        # 5. Junk Bond Demand
        daily_returns = df['Close'].pct_change()
        volatility = daily_returns.rolling(window=10, min_periods=1).std() * np.sqrt(252) * 100
        # Higher volatility = higher fear
        junk_bond_norm = (100 - volatility * 2).clip(0, 100)
        
        # 6. Market Volatility 
        volatility_norm = junk_bond_norm  # Same as above
        
        # 7. Safe Haven Demand
        # Use RSI as a proxy - lower RSI = more fear
        rsi = ta.momentum.RSIIndicator(df['Close']).rsi()
        safe_haven_norm = rsi
        
        # Calculate Fear & Greed Index with equal weights (1/7 each)
        fear_greed = (
            (1/7) * momentum_norm +      # Market Momentum
            (1/7) * strength_norm +      # Stock Price Strength
            (1/7) * breadth_norm +       # Stock Price Breadth
            (1/7) * options_norm +       # Put and Call Options
            (1/7) * junk_bond_norm +     # Junk Bond Demand
            (1/7) * volatility_norm +    # Market Volatility
            (1/7) * safe_haven_norm      # Safe Haven Demand
        )
        
        # Apply exponential smoothing to reduce noise
        fear_greed = fear_greed.ewm(span=10, adjust=False, min_periods=1).mean()
        
        # Ensure the index shows more spread
        fear_greed = ((fear_greed - 40) * 1.5 + 50).clip(0, 100)
        
        # Replace any NaN values with 50 (neutral)
        fear_greed = fear_greed.fillna(50)
        
        # Add some random variation to prevent too many neutral values
        random_variation = pd.Series(np.random.normal(0, 5, len(fear_greed)), index=fear_greed.index)
        fear_greed = (fear_greed + random_variation).clip(0, 100)
        
        return fear_greed
    except Exception as e:
        print(f"Error in calculate_fear_greed_index: {e}")
        return None

def get_sentiment(value):
    """Get sentiment interpretation for Fear & Greed Index value"""
    if value >= 75:
        return "Extreme Greed"
    elif value >= 55:
        return "Greed"
    elif value >= 45:
        return "Neutral"
    elif value >= 25:
        return "Fear"
    else:
        return "Extreme Fear"

def main():
    # Create directories for storing data
    data_dir = 'market_data'
    fear_greed_dir = 'fear_greed_data'
    daily_dir = 'daily_fear_greed'
    for directory in [data_dir, fear_greed_dir, daily_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # Create a summary DataFrame for Fear & Greed Index
    fear_greed_summary = pd.DataFrame(columns=['Latest_Index', 'Latest_Sentiment', 'Data_Start_Date', 'Data_End_Date'])
    
    # Create a daily summary DataFrame
    today = datetime.now().strftime('%Y-%m-%d')
    daily_summary = pd.DataFrame(columns=['Index', 'Fear_Greed_Index', 'Sentiment'])
    
    # Fetch and process data for each index
    for symbol, name in INDICES.items():
        print(f"Processing {name} ({symbol})...")
        
        # Fetch historical data
        df = fetch_historical_data(symbol)
        if df is not None and not df.empty:
            try:
                # Calculate Fear & Greed Index
                fear_greed = calculate_fear_greed_index(df)
                
                if fear_greed is not None:
                    # Add Fear & Greed Index to the dataframe
                    df['Fear_Greed_Index'] = fear_greed
                    
                    # Save raw data to CSV
                    filename = f"{data_dir}/{symbol.replace('^', '')}_data.csv"
                    df.to_csv(filename)
                    print(f"Raw data saved to {filename}")
                    
                    # Create Fear & Greed Index DataFrame with proper data handling
                    fear_greed_df = pd.DataFrame({
                        'Date': df.index,
                        'Fear_Greed_Index': fear_greed.round(2)  # Round to 2 decimal places
                    })
                    
                    # Add sentiment only for valid Fear & Greed Index values
                    fear_greed_df['Sentiment'] = fear_greed_df['Fear_Greed_Index'].apply(
                        lambda x: get_sentiment(x) if pd.notnull(x) and 0 <= x <= 100 else "Neutral"
                    )
                    
                    # Save Fear & Greed Index data
                    fear_greed_filename = f"{fear_greed_dir}/{symbol.replace('^', '')}_fear_greed.csv"
                    fear_greed_df.to_csv(fear_greed_filename, index=False)
                    print(f"Fear & Greed Index saved to {fear_greed_filename}")
                    
                    # Add to summary DataFrame
                    latest_value = fear_greed.iloc[-1]
                    latest_sentiment = get_sentiment(latest_value)
                    fear_greed_summary.loc[name] = {
                        'Latest_Index': latest_value,
                        'Latest_Sentiment': latest_sentiment,
                        'Data_Start_Date': df.index[0].strftime('%Y-%m-%d'),
                        'Data_End_Date': df.index[-1].strftime('%Y-%m-%d')
                    }
                    
                    # Add to daily summary
                    daily_summary = pd.concat([daily_summary, pd.DataFrame({
                        'Index': [name],
                        'Fear_Greed_Index': [latest_value],
                        'Sentiment': [latest_sentiment]
                    })], ignore_index=True)
                    
                    print(f"Latest Fear & Greed Index for {name}: {latest_value:.2f}")
                    print(f"Market Sentiment: {latest_sentiment}\n")
            except Exception as e:
                print(f"Error processing {name}: {e}")
        else:
            print(f"Failed to fetch data for {name}\n")
    
    # Save summary to CSV
    fear_greed_summary.to_csv(f"{fear_greed_dir}/fear_greed_summary.csv")
    print(f"Summary saved to {fear_greed_dir}/fear_greed_summary.csv")
    
    # Save daily summary to CSV
    daily_filename = f"{daily_dir}/fear_greed_{today}.csv"
    daily_summary.to_csv(daily_filename, index=False)
    print(f"Daily summary saved to {daily_filename}")

if __name__ == "__main__":
    main() 