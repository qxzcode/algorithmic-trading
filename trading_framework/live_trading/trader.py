"""
Live trading module using Alpaca API.
"""
from typing import Dict, Any
from datetime import datetime, timedelta
import time
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from trading_framework.base_strategy import BaseStrategy
from trading_framework.config import Config


class LiveTrader:
    """
    Live trading engine using Alpaca API.
    """
    
    def __init__(self, strategy: BaseStrategy, symbol: str, config: Config):
        """
        Initialize the live trader.
        
        Args:
            strategy: Trading strategy instance
            symbol: Stock symbol to trade (e.g., 'AAPL')
            config: Configuration object
        """
        self.strategy = strategy
        self.symbol = symbol.upper()
        self.config = config
        
        # Initialize Alpaca clients
        self.trading_client = TradingClient(
            api_key=config.alpaca_api_key,
            secret_key=config.alpaca_secret_key,
            paper=config.is_paper_trading()
        )
        
        self.data_client = StockHistoricalDataClient(
            api_key=config.alpaca_api_key,
            secret_key=config.alpaca_secret_key
        )
        
        self.running = False
        
    def get_historical_data(self, days: int = 30) -> pd.DataFrame:
        """
        Fetch historical data for the symbol.
        
        Args:
            days: Number of days of historical data to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        end = datetime.now()
        start = end - timedelta(days=days)
        
        request_params = StockBarsRequest(
            symbol_or_symbols=self.symbol,
            timeframe=TimeFrame.Day,
            start=start,
            end=end
        )
        
        bars = self.data_client.get_stock_bars(request_params)
        df = bars.df
        
        if self.symbol in df.index.get_level_values('symbol'):
            df = df.xs(self.symbol, level='symbol')
        
        # Rename columns to standard names
        df.columns = [col.lower() for col in df.columns]
        
        return df
    
    def get_current_position(self) -> float:
        """
        Get current position size for the symbol.
        
        Returns:
            Number of shares held (0 if no position)
        """
        try:
            position = self.trading_client.get_open_position(self.symbol)
            return float(position.qty)
        except Exception:
            return 0.0
    
    def place_market_order(self, side: str, quantity: float) -> bool:
        """
        Place a market order.
        
        Args:
            side: 'buy' or 'sell'
            quantity: Number of shares
            
        Returns:
            True if order was placed successfully
        """
        try:
            order_side = OrderSide.BUY if side == 'buy' else OrderSide.SELL
            
            market_order_data = MarketOrderRequest(
                symbol=self.symbol,
                qty=quantity,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )
            
            order = self.trading_client.submit_order(order_data=market_order_data)
            print(f"Order placed: {side} {quantity} shares of {self.symbol}")
            print(f"Order ID: {order.id}")
            return True
        except Exception as e:
            print(f"Error placing order: {e}")
            return False
    
    def execute_signal(self, signal: Dict[str, Any]) -> bool:
        """
        Execute a trading signal.
        
        Args:
            signal: Signal dictionary from strategy
            
        Returns:
            True if signal was executed successfully
        """
        action = signal.get('action', 'hold')
        quantity = signal.get('quantity', 0)
        reason = signal.get('reason', '')
        
        if action == 'hold' or quantity == 0:
            print(f"No action taken. Reason: {reason}")
            return True
        
        current_position = self.get_current_position()
        
        if action == 'buy':
            if current_position >= 0:
                print(f"Executing BUY: {quantity} shares. Reason: {reason}")
                return self.place_market_order('buy', quantity)
            else:
                print(f"Cannot buy: Current position is short ({current_position})")
                return False
                
        elif action == 'sell':
            if current_position > 0:
                sell_qty = min(quantity, current_position)
                print(f"Executing SELL: {sell_qty} shares. Reason: {reason}")
                return self.place_market_order('sell', sell_qty)
            else:
                print(f"Cannot sell: No long position (current: {current_position})")
                return False
        
        return False
    
    def run_once(self):
        """Execute one iteration of the strategy."""
        print(f"\n--- Strategy iteration at {datetime.now()} ---")
        
        # Get historical data
        data = self.get_historical_data()
        
        if data.empty:
            print("No data available")
            return
        
        # Get signal from strategy
        signal = self.strategy.on_data(data)
        
        # Execute signal
        self.execute_signal(signal)
    
    def run(self, interval_minutes: int = 60):
        """
        Run the trading strategy continuously.
        
        Args:
            interval_minutes: Minutes between strategy executions
        """
        print(f"Starting live trading for {self.symbol}")
        print(f"Strategy: {self.strategy.get_name()}")
        print(f"Mode: {'Paper Trading' if self.config.is_paper_trading() else 'Live Trading'}")
        print(f"Interval: {interval_minutes} minutes")
        
        # Initialize strategy
        self.strategy.initialize()
        
        self.running = True
        
        try:
            while self.running:
                self.run_once()
                
                # Wait for next iteration
                print(f"\nWaiting {interval_minutes} minutes until next iteration...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\nStopping live trading...")
            self.running = False
