"""
Example trading strategy using Moving Average Crossover.
"""
import pandas as pd
import pandas_ta as ta
from typing import Dict, Any

from trading_framework.base_strategy import BaseStrategy


class MovingAverageCrossover(BaseStrategy):
    """
    Moving Average Crossover strategy.
    
    Strategy rules:
    - Buy when fast MA crosses above slow MA (golden cross)
    - Sell when fast MA crosses below slow MA (death cross)
    
    Parameters:
    - fast_period: Period for fast moving average (default: 10)
    - slow_period: Period for slow moving average (default: 30)
    - ma_type: Type of moving average ('SMA' or 'EMA', default: 'SMA')
    - position_size: Number of shares to trade (default: 10)
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'fast_period': 10,
            'slow_period': 30,
            'ma_type': 'SMA',
            'position_size': 10
        }
        if params:
            default_params.update(params)
        super().__init__(default_params)
        
        self.last_fast_ma = None
        self.last_slow_ma = None
        
    def initialize(self):
        """Initialize the strategy."""
        print(f"Initializing {self.get_name()}")
        print(f"Parameters: {self.params}")
        
    def on_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signal based on MA crossover.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Trading signal dictionary
        """
        if len(data) < self.params['slow_period'] + 1:
            return {
                'action': 'hold',
                'quantity': 0,
                'reason': 'Insufficient data for MA calculation'
            }
        
        # Calculate moving averages
        if self.params['ma_type'].upper() == 'EMA':
            fast_ma = ta.ema(data['close'], length=self.params['fast_period'])
            slow_ma = ta.ema(data['close'], length=self.params['slow_period'])
        else:  # SMA
            fast_ma = ta.sma(data['close'], length=self.params['fast_period'])
            slow_ma = ta.sma(data['close'], length=self.params['slow_period'])
        
        if fast_ma is None or slow_ma is None or fast_ma.empty or slow_ma.empty:
            return {
                'action': 'hold',
                'quantity': 0,
                'reason': 'MA calculation failed'
            }
        
        current_fast_ma = fast_ma.iloc[-1]
        current_slow_ma = slow_ma.iloc[-1]
        
        # Skip if any MA is NaN
        if pd.isna(current_fast_ma) or pd.isna(current_slow_ma):
            return {
                'action': 'hold',
                'quantity': 0,
                'reason': 'MA is NaN'
            }
        
        current_price = data['close'].iloc[-1]
        
        # Generate signal
        signal = {
            'action': 'hold',
            'quantity': 0,
            'reason': f'Fast MA: {current_fast_ma:.2f}, Slow MA: {current_slow_ma:.2f}, Price: ${current_price:.2f}'
        }
        
        # Check for crossover only if we have previous values
        if self.last_fast_ma is not None and self.last_slow_ma is not None:
            # Golden cross: fast MA crosses above slow MA
            if self.last_fast_ma <= self.last_slow_ma and current_fast_ma > current_slow_ma:
                signal['action'] = 'buy'
                signal['quantity'] = self.params['position_size']
                signal['reason'] = f'Golden cross: Fast MA ({current_fast_ma:.2f}) > Slow MA ({current_slow_ma:.2f})'
            
            # Death cross: fast MA crosses below slow MA
            elif self.last_fast_ma >= self.last_slow_ma and current_fast_ma < current_slow_ma:
                signal['action'] = 'sell'
                signal['quantity'] = self.params['position_size']
                signal['reason'] = f'Death cross: Fast MA ({current_fast_ma:.2f}) < Slow MA ({current_slow_ma:.2f})'
        
        self.last_fast_ma = current_fast_ma
        self.last_slow_ma = current_slow_ma
        
        return signal
