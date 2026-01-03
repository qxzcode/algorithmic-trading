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
from trading_framework.strategies import RSIStrategy, MACDCrossover


def fetch_data(symbol: str, days: int = 365) -> pd.DataFrame:
    """
    Fetch historical data for backtesting.

    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        days: Number of days of historical data

    Returns:
        DataFrame with OHLCV data or None if fetch failed / symbol not found
    """
    # Normalize symbol to uppercase
    symbol = symbol.upper()

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

    # If response contains a 'symbol' level in the index (multi-symbol response),
    # ensure the requested symbol is present and select it explicitly.
    if 'symbol' in df.index.names:
        returned = list(pd.Index(df.index.get_level_values('symbol')).unique())
        print(f"Symbols returned by API: {returned}")
        if symbol not in returned:
            print(f"Warning: requested symbol '{symbol}' not present in API response. Returning None.")
            return None
        df = df.xs(symbol, level='symbol')

    # Rename columns to lowercase
    df.columns = [col.lower() for col in df.columns]

    print(f"Fetched {len(df)} bars for {symbol}")
    return df


def plot_bars(df: pd.DataFrame, title: str | None = None, show: bool = True, markers: list[dict] | None = None) -> None:
    """
    Plot OHLC bars for a DataFrame with columns: open, high, low, close, volume.

    Tries the following, in order:
      1. mplfinance (candlesticks + volume)
      2. matplotlib (close line + volume bars)

    Accepts `markers`: list of dicts with keys: 'datetime', 'price', 'action' ('buy'|'sell').
    """
    if df is None or df.empty:
        print("No data available to plot")
        return

    title = title or "Price Bars"

    # Normalize markers. If none provided, check LAST_EXECUTED_TRADES global set after backtest run.
    if markers is None:
        markers = globals().get('LAST_EXECUTED_TRADES', []) or []
    else:
        markers = markers or []

    # 1) Try mplfinance first
    try:
        import mplfinance as mpf
        import numpy as np
    except ImportError:
        mpf = None

    if mpf is not None:
        try:
            mpf_df = df.copy()
            mpf_df = mpf_df.rename(columns={
                'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'
            })

            addplots = []
            if markers:
                # Prepare buy/sell series aligned to index
                buy_series = pd.Series(np.nan, index=mpf_df.index)
                sell_series = pd.Series(np.nan, index=mpf_df.index)
                for m in markers:
                    try:
                        ts = pd.to_datetime(m['datetime'])
                    except Exception:
                        continue

                    # Align timezone between marker timestamp and index to avoid dtype comparison errors
                    try:
                        idx_tz = mpf_df.index.tz
                        if idx_tz is not None:
                            # index is tz-aware: localize naive timestamps or convert aware ones
                            if ts.tzinfo is None:
                                try:
                                    ts = ts.tz_localize(idx_tz)
                                except Exception:
                                    # fallback: assume UTC then convert
                                    ts = ts.tz_localize('UTC').tz_convert(idx_tz)
                            else:
                                ts = ts.tz_convert(idx_tz)
                        else:
                            # index is tz-naive: drop tz from ts if present
                            if ts.tzinfo is not None:
                                try:
                                    ts = ts.tz_convert(None)
                                except Exception:
                                    ts = ts.tz_localize(None)
                    except Exception:
                        # As a last resort, coerce to naive timestamp
                        try:
                            if ts.tzinfo is not None:
                                ts = ts.tz_convert(None)
                        except Exception:
                            pass

                    # find nearest index
                    loc = mpf_df.index.get_indexer([ts], method='nearest')[0]
                    idx = mpf_df.index[loc]
                    if m.get('action') == 'buy':
                        buy_series.at[idx] = m.get('price')
                    elif m.get('action') == 'sell':
                        sell_series.at[idx] = m.get('price')

                    if buy_series.dropna().any():
                        addplots.append(mpf.make_addplot(buy_series, type='scatter', marker='^', markersize=80, color='g'))
                if sell_series.dropna().any():
                    addplots.append(mpf.make_addplot(sell_series, type='scatter', marker='v', markersize=80, color='r'))

            # Pass addplots (empty list is acceptable to mplfinance) instead of None
            mpf.plot(mpf_df, type='candle', volume=True, title=title, addplot=addplots)
            return
        except Exception as e:
            print(f"mplfinance plotting failed: {e}")

    # 2) Fallback to matplotlib
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("Plotting libraries not found. Install 'mplfinance' or 'matplotlib' (e.g., pip install mplfinance matplotlib) to enable plotting.")
        return

    fig, (ax_price, ax_vol) = plt.subplots(2, 1, sharex=True, figsize=(12, 8),
                                          gridspec_kw={'height_ratios': [3, 1]})

    # Find a close column case-insensitively
    close_col = None
    for c in df.columns:
        if c.lower() == 'close':
            close_col = c
            break
    if close_col is None:
        close_col = df.columns[3] if df.shape[1] >= 4 else df.columns[-1]

    ax_price.plot(df.index, df[close_col], label='Close')

    # Plot markers if any
    for m in markers:
        try:
            ts = pd.to_datetime(m['datetime'])
        except Exception:
            continue

        # Align timezone between marker timestamp and index to avoid dtype comparison errors
        try:
            idx_tz = df.index.tz
            if idx_tz is not None:
                if ts.tzinfo is None:
                    try:
                        ts = ts.tz_localize(idx_tz)
                    except Exception:
                        ts = ts.tz_localize('UTC').tz_convert(idx_tz)
                else:
                    ts = ts.tz_convert(idx_tz)
            else:
                if ts.tzinfo is not None:
                    try:
                        ts = ts.tz_convert(None)
                    except Exception:
                        ts = ts.tz_localize(None)
        except Exception:
            try:
                if ts.tzinfo is not None:
                    ts = ts.tz_convert(None)
            except Exception:
                pass

        # nearest bar
        loc = df.index.get_indexer([ts], method='nearest')[0]
        idx = df.index[loc]
        price = m.get('price', df[close_col].loc[idx])
        if m.get('action') == 'buy':
            ax_price.scatter(idx, price, marker='^', color='g', s=100, zorder=5)
        elif m.get('action') == 'sell':
            ax_price.scatter(idx, price, marker='v', color='r', s=100, zorder=5)

    ax_price.set_ylabel('Price')
    ax_price.set_title(title)
    ax_price.legend()

    # Find volume column case-insensitively
    vol_col = None
    for c in df.columns:
        if c.lower() == 'volume':
            vol_col = c
            break

    if vol_col is not None:
        ax_vol.bar(df.index, df[vol_col], width=0.8)
        ax_vol.set_ylabel('Volume')
    else:
        ax_vol.set_visible(False)

    fig.autofmt_xdate()
    plt.tight_layout()
    if show:
        plt.show()


def backtest_rsi_strategy():
    """Backtest the RSI strategy."""
    print("\n" + "="*80)
    print("BACKTESTING RSI STRATEGY")
    print("="*80 + "\n")
    
    # Fetch data
    symbol = 'RIVN'
    data = fetch_data(symbol, days=365)
    
    if data is None or data.empty:
        print("Failed to fetch data")
        return

    
    # Create strategy
    strategy = RSIStrategy(params={
        'rsi_period': 14,
        'oversold': 30,
        'overbought': 70,
        'position_size': 100
    })
    
    # Create backtester
    backtester = Backtester(strategy, initial_cash=10000.0)
    
    # Add data
    backtester.add_data(data)
    
    # Run backtest
    results = backtester.run()
    # Expose executed trades for plotting
    LAST_EXECUTED_TRADES = results.get('trades_detail', [])

    # Plot fetched data (attempt candlesticks with mplfinance, fallback to matplotlib)
    try:
        plot_bars(data, title=f"{symbol} - Price Bars")
    except Exception as e:
        print(f"Plotting failed: {e}")
    
    print("\n" + "="*80)
    print("BACKTEST COMPLETE")
    print("="*80)
    

def backtest_macd_crossover():
    """Backtest the MACD Crossover strategy."""
    print("\n" + "="*80)
    print("BACKTESTING MACD CROSSOVER STRATEGY")
    print("="*80 + "\n")
    
    # Fetch data
    symbol = 'RIVN'
    data = fetch_data(symbol, days=365)
    
    if data is None or data.empty:
        print("Failed to fetch data")
        return

    
    # Create strategy
    strategy = MACDCrossover(params={
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'position_size': 100
    })
    
    # Create backtester
    backtester = Backtester(strategy, initial_cash=10000.0)
    
    # Add data
    backtester.add_data(data)
    
    # Run backtest
    results = backtester.run()
    # Expose executed trades for plotting
    LAST_EXECUTED_TRADES = results.get('trades_detail', [])

    # Plot fetched data with entry/exit markers (if any)
    try:
        plot_bars(data, title=f"{symbol} - Price Bars", markers=results.get('trades_detail', []))
    except Exception as e:
        print(f"Plotting failed: {e}")
    
    print("\n" + "="*80)
    print("BACKTEST COMPLETE")
    print("="*80)


if __name__ == '__main__':
    # Backtest RSI strategy
    backtest_rsi_strategy()
    
    print("\n\n")
    
    # Backtest MACD Crossover strategy
    backtest_macd_crossover()
