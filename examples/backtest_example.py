"""
Example script demonstrating how to backtest a trading strategy.

This example shows how to:
1. Load historical data
2. Create a strategy instance
3. Run a backtest
4. View results
"""

from datetime import datetime, timedelta
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from trading_framework import Backtester, Config
from trading_framework.strategies import RSIStrategy, MovingAverageCrossover


def fetch_data(symbol: str, days: int = 365) -> pd.DataFrame:
    """
    Fetch historical data for backtesting.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        days: Number of days of historical data
        
    Returns:
        DataFrame with OHLCV data
    """
    # Load configuration
    config = Config()
    
    if not config.validate():
        print("Please configure your Alpaca API credentials in .env file")
        print("Copy .env.example to .env and add your credentials")
        return None
    
    # Initialize data client
    data_client = StockHistoricalDataClient(
        api_key=config.alpaca_api_key,
        secret_key=config.alpaca_secret_key
    )
    
    # Fetch data
    end = datetime.now()
    start = end - timedelta(days=days)
    
    print(f"Fetching data for {symbol} from {start.date()} to {end.date()}...")
    
    request_params = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end
    )
    
    bars = data_client.get_stock_bars(request_params)
    df = bars.df
    
    if symbol in df.index.get_level_values('symbol'):
        df = df.xs(symbol, level='symbol')
    
    # Rename columns to lowercase
    df.columns = [col.lower() for col in df.columns]
    
    print(f"Fetched {len(df)} bars")
    return df


def backtest_rsi_strategy():
    """Backtest the RSI strategy."""
    print("\n" + "="*80)
    print("BACKTESTING RSI STRATEGY")
    print("="*80 + "\n")
    
    # Fetch data
    symbol = 'AAPL'
    data = fetch_data(symbol, days=365)
    
    if data is None or data.empty:
        print("Failed to fetch data")
        return
    
    # Create strategy
    strategy = RSIStrategy(params={
        'rsi_period': 14,
        'oversold': 30,
        'overbought': 70,
        'position_size': 10
    })
    
    # Create backtester
    backtester = Backtester(strategy, initial_cash=10000.0)
    
    # Add data
    backtester.add_data(data)
    
    # Run backtest
    results = backtester.run()
    
    print("\n" + "="*80)
    print("BACKTEST COMPLETE")
    print("="*80)
    

def backtest_ma_crossover():
    """Backtest the Moving Average Crossover strategy."""
    print("\n" + "="*80)
    print("BACKTESTING MOVING AVERAGE CROSSOVER STRATEGY")
    print("="*80 + "\n")
    
    # Fetch data
    symbol = 'AAPL'
    data = fetch_data(symbol, days=365)
    
    if data is None or data.empty:
        print("Failed to fetch data")
        return
    
    # Create strategy
    strategy = MovingAverageCrossover(params={
        'fast_period': 10,
        'slow_period': 30,
        'ma_type': 'SMA',
        'position_size': 10
    })
    
    # Create backtester
    backtester = Backtester(strategy, initial_cash=10000.0)
    
    # Add data
    backtester.add_data(data)
    
    # Run backtest
    results = backtester.run()
    
    print("\n" + "="*80)
    print("BACKTEST COMPLETE")
    print("="*80)


if __name__ == '__main__':
    # Backtest RSI strategy
    backtest_rsi_strategy()
    
    print("\n\n")
    
    # Backtest MA Crossover strategy
    backtest_ma_crossover()
