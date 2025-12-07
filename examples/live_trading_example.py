"""
Example script demonstrating how to run a strategy in live/paper trading mode.

This example shows how to:
1. Load configuration
2. Create a strategy instance
3. Start live trading
"""

from trading_framework import LiveTrader, Config
from trading_framework.strategies import RSIStrategy, MovingAverageCrossover


def run_live_trading():
    """Run a strategy in live/paper trading mode."""
    
    # Load configuration
    config = Config()
    
    if not config.validate():
        print("Please configure your Alpaca API credentials in .env file")
        print("Copy .env.example to .env and add your credentials")
        return
    
    # Display trading mode
    mode = "Paper Trading" if config.is_paper_trading() else "LIVE Trading"
    print(f"\n{'='*80}")
    print(f"Running in {mode} mode")
    print(f"{'='*80}\n")
    
    if not config.is_paper_trading():
        print("WARNING: You are in LIVE trading mode!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Exiting...")
            return
    
    # Choose a strategy
    print("\nAvailable strategies:")
    print("1. RSI Strategy")
    print("2. Moving Average Crossover")
    
    choice = input("\nSelect a strategy (1 or 2): ")
    
    if choice == '1':
        # RSI Strategy
        strategy = RSIStrategy(params={
            'rsi_period': 14,
            'oversold': 30,
            'overbought': 70,
            'position_size': 10
        })
    elif choice == '2':
        # Moving Average Crossover
        strategy = MovingAverageCrossover(params={
            'fast_period': 10,
            'slow_period': 30,
            'ma_type': 'SMA',
            'position_size': 10
        })
    else:
        print("Invalid choice")
        return
    
    # Choose symbol
    symbol = input("\nEnter stock symbol (e.g., AAPL): ").upper()
    
    if not symbol:
        print("Invalid symbol")
        return
    
    # Choose interval
    interval = input("\nEnter check interval in minutes (default: 60): ")
    try:
        interval = int(interval) if interval else 60
    except ValueError:
        interval = 60
    
    # Create trader
    trader = LiveTrader(strategy, symbol, config)
    
    # Run trading
    print(f"\n{'='*80}")
    print("Starting trading bot...")
    print("Press Ctrl+C to stop")
    print(f"{'='*80}\n")
    
    try:
        trader.run(interval_minutes=interval)
    except KeyboardInterrupt:
        print("\nStopping...")
    
    print("\nTrading bot stopped.")


if __name__ == '__main__':
    run_live_trading()
