# Trading Framework - Additional Documentation

## Strategy Development Guide

### Creating a Strategy

Every strategy should inherit from `BaseStrategy` and implement two methods:

```python
from trading_framework.base_strategy import BaseStrategy
import pandas as pd
from typing import Dict, Any

class MyStrategy(BaseStrategy):
    def initialize(self):
        """Called once when the strategy starts"""
        pass
    
    def on_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Called for each new data point/bar.
        
        Args:
            data: DataFrame with columns: open, high, low, close, volume
                  Index is datetime
        
        Returns:
            dict with keys:
                - action: 'buy', 'sell', or 'hold'
                - quantity: number of shares
                - reason: string explaining the signal
        """
        return {
            'action': 'hold',
            'quantity': 0,
            'reason': 'No signal'
        }
```

### Strategy Parameters

Pass parameters to your strategy via the constructor:

```python
strategy = MyStrategy(params={
    'threshold': 0.02,
    'lookback': 20,
    'position_size': 10
})

# Access parameters in your strategy
def on_data(self, data):
    threshold = self.params['threshold']
    lookback = self.params['lookback']
    # ... use parameters
```

### Using Technical Indicators

The framework includes pandas-ta with 130+ indicators:

```python
import pandas_ta as ta

# In your on_data method:
rsi = ta.rsi(data['close'], length=14)
macd = ta.macd(data['close'])
bbands = ta.bbands(data['close'])
sma = ta.sma(data['close'], length=20)
ema = ta.ema(data['close'], length=20)
```

See https://www.pandas-ta.dev/ for all available indicators.

## Backtesting Guide

### Basic Backtesting

```python
from trading_framework import Backtester
from my_strategy import MyStrategy

# Create strategy
strategy = MyStrategy(params={'param1': value1})

# Create backtester
backtester = Backtester(strategy, initial_cash=10000.0)

# Add historical data
backtester.add_data(historical_data_df)

# Run backtest
results = backtester.run()

print(f"Return: {results['return_pct']:.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']}")
print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
```

### Getting Historical Data

```python
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from trading_framework import Config

config = Config()
data_client = StockHistoricalDataClient(
    api_key=config.alpaca_api_key,
    secret_key=config.alpaca_secret_key
)

# Fetch 1 year of daily data
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
```

## Live Trading Guide

### Paper Trading

Always test with paper trading first:

```python
from trading_framework import LiveTrader, Config
from my_strategy import MyStrategy

# Configure (.env should have ALPACA_TRADING_MODE=paper)
config = Config()

# Create strategy
strategy = MyStrategy(params={'param1': value1})

# Create trader
trader = LiveTrader(strategy, 'AAPL', config)

# Run (checks every hour)
trader.run(interval_minutes=60)
```

### Live Trading

⚠️ **WARNING**: Use with extreme caution!

1. Set `ALPACA_TRADING_MODE=live` in `.env`
2. Test thoroughly in paper trading first
3. Start with small position sizes
4. Monitor closely

```python
# Same as paper trading, but with live mode in .env
config = Config()
if not config.is_paper_trading():
    print("WARNING: Running in LIVE mode!")
    # Add additional confirmations
```

## Tips and Best Practices

### 1. Test Thoroughly
- Start with backtesting on multiple time periods
- Test on different symbols
- Verify edge cases (low volume, gaps, etc.)

### 2. Risk Management
- Always use position sizing
- Implement stop losses if needed
- Never risk more than you can afford to lose

### 3. Avoid Common Pitfalls
- **Look-ahead bias**: Don't use future data in signals
- **Overfitting**: Don't optimize too much on historical data
- **Transaction costs**: Account for commissions and slippage
- **Market impact**: Large orders can move prices

### 4. Strategy Development Workflow
1. Research and hypothesis
2. Implement strategy
3. Backtest on historical data
4. Optimize parameters (careful not to overfit)
5. Walk-forward testing
6. Paper trading
7. Small live positions
8. Scale up gradually

### 5. Monitoring
- Log all trades and signals
- Track performance metrics
- Review regularly
- Be ready to stop if something goes wrong

## Troubleshooting

### "ALPACA_API_KEY not set"
- Copy `.env.example` to `.env`
- Add your API credentials from Alpaca

### "No data available"
- Check your API credentials
- Verify the symbol exists
- Check market hours (if using live data)

### Strategy not generating signals
- Add debug prints in `on_data()`
- Check data has enough history for indicators
- Verify indicator calculations aren't returning NaN

### Backtest results unexpected
- Check strategy logic carefully
- Verify data quality
- Consider transaction costs
- Check for look-ahead bias

## Resources

- **Alpaca Docs**: https://alpaca.markets/docs/
- **pandas-ta**: https://www.pandas-ta.dev/
- **backtrader**: https://www.backtrader.com/docu/
- **pandas**: https://pandas.pydata.org/docs/

## Contributing

Contributions are welcome! Some ideas:
- Additional example strategies
- Support for more brokers
- More technical indicators
- Better risk management
- Portfolio-level strategies
- Improved logging and monitoring
