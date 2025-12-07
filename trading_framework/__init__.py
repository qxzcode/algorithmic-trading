"""
Trading Framework

A simple framework for experimenting with trading algorithms using Alpaca and backtrader.
"""

__version__ = '0.1.0'

from trading_framework.base_strategy import BaseStrategy
from trading_framework.config import Config
from trading_framework.live_trading.trader import LiveTrader
from trading_framework.backtesting.backtester import Backtester

__all__ = [
    'BaseStrategy',
    'Config',
    'LiveTrader',
    'Backtester',
]
