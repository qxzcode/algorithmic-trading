"""
MACD Crossover strategy.

Logic:
- Buy when MACD line crosses above signal line
- Sell when MACD line crosses below signal line

Uses pandas_ta.macd which returns columns with names like:
- MACD_<fast>_<slow>_<signal>
- MACDs_<fast>_<slow>_<signal>  (signal line)
"""
import pandas as pd
import pandas_ta as ta
from typing import Dict, Any

from trading_framework.base_strategy import BaseStrategy


class MACDCrossover(BaseStrategy):
    """
    MACD Crossover strategy.
    """

    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'position_size': 10
        }
        if params:
            default_params.update(params)
        super().__init__(default_params)

        self.last_macd = None
        self.last_signal = None

    def initialize(self):
        print(f"Initializing {self.get_name()}")
        print(f"Parameters: {self.params}")

    def on_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        if len(data) < max(self.params['macd_slow'], 30):
            return {'action': 'hold', 'quantity': 0, 'reason': 'Insufficient data for MACD'}

        macd_res = ta.macd(
            data['close'],
            fast=self.params['macd_fast'],
            slow=self.params['macd_slow'],
            signal=self.params['macd_signal']
        )

        if macd_res is None or macd_res.empty:
            return {'action': 'hold', 'quantity': 0, 'reason': 'MACD calculation failed'}

        macd_col = f'MACD_{self.params["macd_fast"]}_{self.params["macd_slow"]}_{self.params["macd_signal"]}'
        sig_col = f'MACDs_{self.params["macd_fast"]}_{self.params["macd_slow"]}_{self.params["macd_signal"]}'

        if macd_col not in macd_res.columns or sig_col not in macd_res.columns:
            return {'action': 'hold', 'quantity': 0, 'reason': 'MACD columns missing'}

        current_macd = macd_res[macd_col].iloc[-1]
        current_sig = macd_res[sig_col].iloc[-1]

        if pd.isna(current_macd) or pd.isna(current_sig):
            return {'action': 'hold', 'quantity': 0, 'reason': 'MACD or signal is NaN'}

        signal = {'action': 'hold', 'quantity': 0, 'reason': f'MACD: {current_macd:.5f}, Signal: {current_sig:.5f}'}

        if self.last_macd is not None and self.last_signal is not None:
            # Bullish crossover
            if self.last_macd <= self.last_signal and current_macd > current_sig:
                signal['action'] = 'buy'
                signal['quantity'] = self.params['position_size']
                signal['reason'] = f'MACD bullish crossover: {current_macd:.5f} > {current_sig:.5f}'
            # Bearish crossover
            elif self.last_macd >= self.last_signal and current_macd < current_sig:
                signal['action'] = 'sell'
                signal['quantity'] = self.params['position_size']
                signal['reason'] = f'MACD bearish crossover: {current_macd:.5f} < {current_sig:.5f}'

        self.last_macd = current_macd
        self.last_signal = current_sig

        return signal
