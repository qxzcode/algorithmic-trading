# Algorithmic Trading Framework

A simple, flexible framework for experimenting with trading algorithms using Alpaca for trading and backtrader for backtesting.

## Features

- **Easy Strategy Definition**: Simple interface for creating custom trading strategies
- **Live Trading**: Execute strategies in real-time using Alpaca (paper or live trading)
- **Backtesting**: Test strategies on historical data using backtrader
- **Technical Analysis**: Built-in support for pandas-ta indicators (RSI, MACD, moving averages, etc.)
- **Example Strategies**: Pre-built strategies to get you started quickly

## Installation

1. Clone the repository:
```bash
git clone https://github.com/qxzcode/algorithmic-trading.git
cd algorithmic-trading
```

2. [Install `uv`](https://docs.astral.sh/uv/getting-started/installation/), then install dependencies:
```bash
uv sync
```

3. Set up your Alpaca API credentials:
```bash
cp .env.example .env
# Edit .env and add your Alpaca API credentials
```

Get your API credentials from: https://app.alpaca.markets/paper/dashboard/overview

## Quick Start

### 1. Backtesting a Strategy

```python
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from trading_framework import Backtester, Config
from trading_framework.strategies import RSIStrategy

# Load config and fetch data
config = Config()
data_client = StockHistoricalDataClient(
    api_key=config.alpaca_api_key,
    secret_key=config.alpaca_secret_key
)

# Fetch historical data
end = datetime.now()
start = end - timedelta(days=365)
request = StockBarsRequest(
    symbol_or_symbols='AAPL',
    timeframe=TimeFrame.Day,
    start=start,
    end=end
)
bars = data_client.get_stock_bars(request)
data = bars.df.xs('AAPL', level='symbol')
data.columns = [col.lower() for col in data.columns]

# Create and run backtest
strategy = RSIStrategy(params={
    'rsi_period': 14,
    'oversold': 30,
    'overbought': 70,
    'position_size': 10
})

backtester = Backtester(strategy, initial_cash=10000.0)
backtester.add_data(data)
results = backtester.run()
```

Or use the example script:
```bash
uv run examples/backtest_example.py
```

### 2. Live Trading (Paper Trading)

```python
from trading_framework import LiveTrader, Config
from trading_framework.strategies import RSIStrategy

# Load configuration
config = Config()

# Create strategy
strategy = RSIStrategy(params={
    'rsi_period': 14,
    'oversold': 30,
    'overbought': 70,
    'position_size': 10
})

# Create trader and run
trader = LiveTrader(strategy, 'AAPL', config)
trader.run(interval_minutes=60)  # Check every hour
```

Or use the interactive example script:
```bash
uv run examples/live_trading_example.py
```

### 3. Creating a Custom Strategy

Create a new strategy by inheriting from `BaseStrategy`:

```python
import pandas as pd
import pandas_ta as ta
from typing import Dict, Any
from trading_framework.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        
    def initialize(self):
        """Called once at the start"""
        print(f"Initializing {self.get_name()}")
        
    def on_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Called when new market data is available.
        
        Args:
            data: DataFrame with columns: open, high, low, close, volume
            
        Returns:
            Signal dict with keys: action ('buy'|'sell'|'hold'), quantity, reason
        """
        # Calculate indicators
        rsi = ta.rsi(data['close'], length=14)
        current_rsi = rsi.iloc[-1]
        
        # Generate signal
        if current_rsi < 30:
            return {
                'action': 'buy',
                'quantity': 10,
                'reason': f'RSI oversold: {current_rsi:.2f}'
            }
        elif current_rsi > 70:
            return {
                'action': 'sell',
                'quantity': 10,
                'reason': f'RSI overbought: {current_rsi:.2f}'
            }
        else:
            return {
                'action': 'hold',
                'quantity': 0,
                'reason': f'RSI neutral: {current_rsi:.2f}'
            }
```

See `examples/custom_strategy.py` for a more complete example.

## Project Structure

```
algorithmic-trading/
├── trading_framework/          # Main framework code
│   ├── __init__.py
│   ├── base_strategy.py       # Base strategy interface
│   ├── config.py              # Configuration management
│   ├── live_trading/          # Live trading module
│   │   ├── __init__.py
│   │   └── trader.py          # Alpaca live trading
│   ├── backtesting/           # Backtesting module
│   │   ├── __init__.py
│   │   └── backtester.py      # Backtrader integration
│   ├── strategies/            # Example strategies
│   │   ├── __init__.py
│   │   ├── rsi_strategy.py
│   │   └── ma_crossover.py
│   └── utils/                 # Utilities
├── examples/                   # Example scripts
│   ├── backtest_example.py
│   ├── live_trading_example.py
│   └── custom_strategy.py
├── requirements.txt
├── .env.example
└── README.md
```

## Included Strategies

### RSI Strategy
Trades based on Relative Strength Index:
- **Buy**: When RSI crosses below oversold threshold (default: 30)
- **Sell**: When RSI crosses above overbought threshold (default: 70)

### Moving Average Crossover
Trades based on moving average crossovers:
- **Buy**: When fast MA crosses above slow MA (golden cross)
- **Sell**: When fast MA crosses below slow MA (death cross)

## Technical Indicators

The framework includes pandas-ta, which provides 130+ technical indicators:

- **Momentum**: RSI, Stochastic, CCI, Williams %R
- **Trend**: SMA, EMA, MACD, ADX, Aroon
- **Volatility**: Bollinger Bands, ATR, Keltner Channels
- **Volume**: OBV, Volume Profile, MFI
- And many more!

See https://www.pandas-ta.dev/ for full documentation.

## Configuration

Edit `.env` file:

```bash
# Alpaca API credentials
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here

# Trading mode: 'paper' for paper trading, 'live' for real trading
ALPACA_TRADING_MODE=paper
```

**Important**: Always test strategies in paper trading mode before using real money!

## Resources

- **Alpaca**: https://alpaca.markets/
- **Alpaca Python SDK**: https://alpaca.markets/sdks/python/getting_started.html
- **pandas-ta (Technical Analysis)**: https://www.pandas-ta.dev/
- **backtrader (Backtesting)**: https://github.com/mementum/backtrader

## Safety and Disclaimer

⚠️ **WARNING**: Trading involves significant risk. This framework is for educational purposes only.

- Always test strategies thoroughly with paper trading first
- Never invest more than you can afford to lose
- Past performance does not guarantee future results
- The authors are not responsible for any financial losses

## License

This project is provided as-is for educational purposes.

## Contributing

Feel free to submit issues and pull requests!
