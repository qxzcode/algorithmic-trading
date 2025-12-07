"""
Example trading strategy using RSI (Relative Strength Index).
"""
import pandas as pd
import pandas_ta as ta
from typing import Dict, Any

from trading_framework.base_strategy import BaseStrategy


class RSIStrategy(BaseStrategy):
    """
    Simple RSI-based trading strategy.
    
    Strategy rules:
    - Buy when RSI crosses below oversold threshold (default: 30)
    - Sell when RSI crosses above overbought threshold (default: 70)
    
    Parameters:
    - rsi_period: Period for RSI calculation (default: 14)
    - oversold: RSI level considered oversold (default: 30)
    - overbought: RSI level considered overbought (default: 70)
    - position_size: Number of shares to trade (default: 10)
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'rsi_period': 14,
            'oversold': 30,
            'overbought': 70,
            'position_size': 10
        }
        if params:
            default_params.update(params)
        super().__init__(default_params)
        
        self.last_rsi = None
        
    def initialize(self):
        """Initialize the strategy."""
        print(f"Initializing {self.get_name()}")
        print(f"Parameters: {self.params}")
        
    def on_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signal based on RSI.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Trading signal dictionary
        """
        if len(data) < self.params['rsi_period'] + 1:
            return {
                'action': 'hold',
                'quantity': 0,
                'reason': 'Insufficient data for RSI calculation'
            }
        
        # Calculate RSI using pandas-ta
        rsi = ta.rsi(data['close'], length=self.params['rsi_period'])
        
        if rsi is None or rsi.empty:
            return {
                'action': 'hold',
                'quantity': 0,
                'reason': 'RSI calculation failed'
            }
        
        current_rsi = rsi.iloc[-1]
        
        # Skip if RSI is NaN
        if pd.isna(current_rsi):
            return {
                'action': 'hold',
                'quantity': 0,
                'reason': 'RSI is NaN'
            }
        
        current_price = data['close'].iloc[-1]
        
        # Generate signal
        signal = {
            'action': 'hold',
            'quantity': 0,
            'reason': f'RSI: {current_rsi:.2f}, Price: ${current_price:.2f}'
        }
        
        # Buy signal: RSI crosses below oversold (only if we have previous RSI to detect crossover)
        if current_rsi < self.params['oversold']:
            if self.last_rsi is not None and self.last_rsi >= self.params['oversold']:
                signal['action'] = 'buy'
                signal['quantity'] = self.params['position_size']
                signal['reason'] = f'RSI oversold crossover: {current_rsi:.2f} < {self.params["oversold"]}'
        
        # Sell signal: RSI crosses above overbought (only if we have previous RSI to detect crossover)
        elif current_rsi > self.params['overbought']:
            if self.last_rsi is not None and self.last_rsi <= self.params['overbought']:
                signal['action'] = 'sell'
                signal['quantity'] = self.params['position_size']
                signal['reason'] = f'RSI overbought crossover: {current_rsi:.2f} > {self.params["overbought"]}'
        
        self.last_rsi = current_rsi
        
        return signal
