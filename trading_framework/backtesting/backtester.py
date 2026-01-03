"""
Backtesting module using backtrader library.
"""
import backtrader as bt
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

from trading_framework.base_strategy import BaseStrategy


class BacktraderStrategyWrapper(bt.Strategy):
    """
    Wrapper to adapt our BaseStrategy to backtrader's Strategy interface.
    """
    
    params = (
        ('custom_strategy', None),
    )
    
    def __init__(self):
        self.custom_strategy = self.params.custom_strategy
        if self.custom_strategy:
            self.custom_strategy.initialize()
        
        self.dataclose = self.datas[0].close
        self.order = None
        # Record executed trades for later inspection/plotting
        self.executed_trades = []  # list of dicts: {'datetime': datetime, 'price': float, 'action': 'buy'|'sell', 'size': int}
        
    def notify_order(self, order):
        """Called when order status changes."""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            # Capture execution details for plotting/analysis
            exec_dt = self.datas[0].datetime.datetime(0)
            exec_price = order.executed.price
            exec_size = getattr(order.executed, 'size', None)
            if order.isbuy():
                print(f'BUY EXECUTED: Price: {exec_price:.2f}, '
                      f'Cost: {order.executed.value:.2f}, '
                      f'Comm: {order.executed.comm:.2f}')
                self.executed_trades.append({'datetime': exec_dt, 'price': exec_price, 'action': 'buy', 'size': exec_size})
            elif order.issell():
                print(f'SELL EXECUTED: Price: {exec_price:.2f}, '
                      f'Cost: {order.executed.value:.2f}, '
                      f'Comm: {order.executed.comm:.2f}')
                self.executed_trades.append({'datetime': exec_dt, 'price': exec_price, 'action': 'sell', 'size': exec_size})
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print('Order Canceled/Margin/Rejected')
        
        self.order = None
    
    def notify_trade(self, trade):
        """Called when trade is closed."""
        if not trade.isclosed:
            return
        
        print(f'TRADE PROFIT: Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')
    
    def next(self):
        """Called for each bar in the data."""
        if self.order:
            return  # Wait for pending order
        
        if not self.custom_strategy:
            return
        
        # Convert backtrader data to pandas DataFrame
        data = self._get_dataframe()
        
        # Get signal from custom strategy
        signal = self.custom_strategy.on_data(data)
        
        action = signal.get('action', 'hold')
        quantity = signal.get('quantity', 0)
        
        # Note: This implementation supports long-only strategies (no short selling)
        if action == 'buy' and quantity > 0:
            if not self.position:  # Only buy if we don't have a position
                self.order = self.buy(size=quantity)
        elif action == 'sell' and quantity > 0:
            if self.position:  # Only sell if we have a long position
                self.order = self.sell(size=quantity)
    
    def _get_dataframe(self, lookback: int = 100) -> pd.DataFrame:
        """
        Convert backtrader data to pandas DataFrame.
        
        Args:
            lookback: Number of bars to include
            
        Returns:
            DataFrame with OHLCV data
        """
        # Get the data feed
        data_feed = self.datas[0]
        
        # Create lists for each column
        dates = []
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []
        
        # Get the available data
        available_bars = min(lookback, len(data_feed))
        
        for i in range(-available_bars + 1, 1):
            dates.append(data_feed.datetime.datetime(i))
            opens.append(data_feed.open[i])
            highs.append(data_feed.high[i])
            lows.append(data_feed.low[i])
            closes.append(data_feed.close[i])
            volumes.append(data_feed.volume[i])
        
        # Create DataFrame
        df = pd.DataFrame({
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes
        }, index=dates)
        
        return df


class Backtester:
    """
    Backtesting engine using backtrader.
    """
    
    def __init__(self, strategy: BaseStrategy, initial_cash: float = 10000.0):
        """
        Initialize the backtester.
        
        Args:
            strategy: Trading strategy instance
            initial_cash: Initial cash for backtesting
        """
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.cerebro = bt.Cerebro()
        
        # Set initial cash
        self.cerebro.broker.setcash(initial_cash)
        
        # Set commission (0.1% per trade, typical for stocks)
        self.cerebro.broker.setcommission(commission=0.001)
        
    def add_data(self, data: pd.DataFrame, name: str = 'data'):
        """
        Add data to the backtester.
        
        Args:
            data: DataFrame with OHLCV data (columns: open, high, low, close, volume)
                  Index should be datetime
            name: Name for the data feed
        """
        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in data.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Create backtrader data feed
        bt_data = bt.feeds.PandasData(
            dataname=data,
            openinterest=None
        )
        
        self.cerebro.adddata(bt_data, name=name)
    
    def run(self) -> Dict[str, Any]:
        """
        Run the backtest.
        
        Returns:
            Dictionary with backtest results
        """
        print(f'Starting Portfolio Value: ${self.initial_cash:.2f}')
        print(f'Strategy: {self.strategy.get_name()}')
        print('-' * 60)
        
        # Add strategy with wrapper
        self.cerebro.addstrategy(
            BacktraderStrategyWrapper,
            custom_strategy=self.strategy
        )
        
        # Add analyzers
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # Run backtest
        results = self.cerebro.run()
        strat = results[0]
        
        # Get final value
        final_value = self.cerebro.broker.getvalue()
        
        # Extract analyzer results
        sharpe = strat.analyzers.sharpe.get_analysis()
        returns = strat.analyzers.returns.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        trades = strat.analyzers.trades.get_analysis()
        
        # Extract executed trades recorded by the wrapper (if any)
        trades_detail = getattr(strat, 'executed_trades', [])
        
        # Print results
        print('-' * 60)
        print(f'Final Portfolio Value: ${final_value:.2f}')
        print(f'Total Return: {((final_value - self.initial_cash) / self.initial_cash * 100):.2f}%')
        
        if 'sharperatio' in sharpe and sharpe['sharperatio'] is not None:
            print(f'Sharpe Ratio: {sharpe["sharperatio"]:.2f}')
        
        if 'max' in drawdown and drawdown['max'].get('drawdown') is not None:
            print(f'Max Drawdown: {drawdown["max"]["drawdown"]:.2f}%')
        
        if 'total' in trades:
            total_trades = trades['total']['total']
            print(f'Total Trades: {total_trades}')
            if total_trades > 0:
                won = trades['won']['total'] if 'won' in trades else 0
                print(f'Win Rate: {(won / total_trades * 100):.2f}%')
        
        return {
            'initial_value': self.initial_cash,
            'final_value': final_value,
            'return_pct': (final_value - self.initial_cash) / self.initial_cash * 100,
            'sharpe_ratio': sharpe.get('sharperatio'),
            'max_drawdown': drawdown.get('max', {}).get('drawdown'),
            'total_trades': trades.get('total', {}).get('total', 0),
            'won_trades': trades.get('won', {}).get('total', 0),
            'trades_detail': trades_detail,
        }
    
    def plot(self):
        """Plot the backtest results."""
        self.cerebro.plot()
