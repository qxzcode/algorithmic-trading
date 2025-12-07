"""
Example of creating a custom trading strategy.

This demonstrates how to create your own strategy by inheriting from BaseStrategy.
"""

import pandas as pd
import pandas_ta as ta
from typing import Dict, Any

from trading_framework.base_strategy import BaseStrategy


class MyCustomStrategy(BaseStrategy):
    """
    Custom strategy combining multiple indicators.
    
    This example uses:
    - RSI for momentum
    - MACD for trend
    - Volume for confirmation
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'volume_threshold': 1.5,  # Volume should be 1.5x average
            'position_size': 10
        }
        if params:
            default_params.update(params)
        super().__init__(default_params)
        
    def initialize(self):
        """Initialize the strategy."""
        print(f"Initializing {self.get_name()}")
        print(f"Parameters: {self.params}")
        
    def on_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signal based on multiple indicators.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Trading signal dictionary
        """
        if len(data) < 50:
            return {
                'action': 'hold',
                'quantity': 0,
                'reason': 'Insufficient data'
            }
        
        # Calculate indicators
        rsi = ta.rsi(data['close'], length=self.params['rsi_period'])
        macd_result = ta.macd(
            data['close'],
            fast=self.params['macd_fast'],
            slow=self.params['macd_slow'],
            signal=self.params['macd_signal']
        )
        
        if rsi is None or macd_result is None or rsi.empty or macd_result.empty:
            return {
                'action': 'hold',
                'quantity': 0,
                'reason': 'Indicator calculation failed'
            }
        
        # Get current values
        current_rsi = rsi.iloc[-1]
        current_macd = macd_result[f'MACD_{self.params["macd_fast"]}_{self.params["macd_slow"]}_{self.params["macd_signal"]}'].iloc[-1]
        current_signal = macd_result[f'MACDs_{self.params["macd_fast"]}_{self.params["macd_slow"]}_{self.params["macd_signal"]}'].iloc[-1]
        current_volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].iloc[-20:].mean()
        
        # Skip if any value is NaN
        if pd.isna(current_rsi) or pd.isna(current_macd) or pd.isna(current_signal):
            return {
                'action': 'hold',
                'quantity': 0,
                'reason': 'Indicator is NaN'
            }
        
        current_price = data['close'].iloc[-1]
        
        # Check conditions for buy signal
        buy_conditions = [
            current_rsi < self.params['rsi_oversold'],  # Oversold
            current_macd > current_signal,  # MACD bullish
            current_volume > avg_volume * self.params['volume_threshold']  # High volume
        ]
        
        # Check conditions for sell signal
        sell_conditions = [
            current_rsi > self.params['rsi_overbought'],  # Overbought
            current_macd < current_signal,  # MACD bearish
            current_volume > avg_volume * self.params['volume_threshold']  # High volume
        ]
        
        # Generate signal
        if all(buy_conditions):
            return {
                'action': 'buy',
                'quantity': self.params['position_size'],
                'reason': f'All buy conditions met: RSI={current_rsi:.2f}, MACD bullish, Volume high'
            }
        elif all(sell_conditions):
            return {
                'action': 'sell',
                'quantity': self.params['position_size'],
                'reason': f'All sell conditions met: RSI={current_rsi:.2f}, MACD bearish, Volume high'
            }
        else:
            return {
                'action': 'hold',
                'quantity': 0,
                'reason': f'No clear signal. RSI={current_rsi:.2f}, Price=${current_price:.2f}'
            }


# Example usage
if __name__ == '__main__':
    from trading_framework import Backtester
    from datetime import datetime, timedelta
    import pandas as pd
    
    print("This is an example custom strategy.")
    print("To use it, import it in your backtest or live trading script.")
    print("\nExample:")
    print("  from custom_strategy import MyCustomStrategy")
    print("  strategy = MyCustomStrategy()")
    print("  # Use with Backtester or LiveTrader")
