"""
Base strategy interface for trading algorithms.
All custom strategies should inherit from BaseStrategy.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    
    Inherit from this class and implement the required methods to create
    your own trading strategy.
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        Initialize the strategy with optional parameters.
        
        Args:
            params: Dictionary of strategy parameters
        """
        self.params = params or {}
        self.position = 0  # Current position size
        
    @abstractmethod
    def initialize(self):
        """
        Initialize the strategy. Called once at the start.
        Use this to set up any indicators or variables.
        """
        pass
    
    @abstractmethod
    def on_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Called when new market data is available.
        
        Args:
            data: DataFrame with OHLCV data (Open, High, Low, Close, Volume)
                  Index should be timestamp
        
        Returns:
            Dictionary with trading signal:
            {
                'action': 'buy' | 'sell' | 'hold',
                'quantity': int or float,
                'reason': str (optional)
            }
        """
        pass
    
    def get_name(self) -> str:
        """Return the name of the strategy."""
        return self.__class__.__name__
    
    def get_params(self) -> Dict[str, Any]:
        """Return the strategy parameters."""
        return self.params
