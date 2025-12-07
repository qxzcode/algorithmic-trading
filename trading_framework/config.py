"""
Configuration management for the trading framework.
"""
import os
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Configuration class for trading framework."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Load configuration from environment variables.
        
        Args:
            env_file: Path to .env file (optional)
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        # Alpaca credentials
        self.alpaca_api_key = os.getenv('ALPACA_API_KEY', '')
        self.alpaca_secret_key = os.getenv('ALPACA_SECRET_KEY', '')
        self.alpaca_trading_mode = os.getenv('ALPACA_TRADING_MODE', 'paper')
        
    def validate(self) -> bool:
        """
        Validate that required configuration is present.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.alpaca_api_key:
            print("Error: ALPACA_API_KEY not set")
            return False
        if not self.alpaca_secret_key:
            print("Error: ALPACA_SECRET_KEY not set")
            return False
        if self.alpaca_trading_mode not in ['paper', 'live']:
            print("Error: ALPACA_TRADING_MODE must be 'paper' or 'live'")
            return False
        return True
    
    def is_paper_trading(self) -> bool:
        """Check if paper trading mode is enabled."""
        return self.alpaca_trading_mode == 'paper'
