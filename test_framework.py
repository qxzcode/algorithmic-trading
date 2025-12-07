"""
Simple test to validate the framework structure works correctly.
This test doesn't require API credentials.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from trading_framework import BaseStrategy, Config, LiveTrader, Backtester
        print("✓ Main framework imports successful")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    try:
        from trading_framework.strategies import RSIStrategy, MovingAverageCrossover
        print("✓ Strategy imports successful")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    return True


def test_base_strategy():
    """Test creating a basic strategy."""
    print("\nTesting BaseStrategy...")
    
    from trading_framework import BaseStrategy
    
    class TestStrategy(BaseStrategy):
        def initialize(self):
            pass
        
        def on_data(self, data):
            return {'action': 'hold', 'quantity': 0, 'reason': 'test'}
    
    strategy = TestStrategy({'test_param': 123})
    assert strategy.get_name() == 'TestStrategy'
    assert strategy.get_params()['test_param'] == 123
    
    print("✓ BaseStrategy works correctly")
    return True


def test_rsi_strategy():
    """Test RSI strategy with mock data."""
    print("\nTesting RSI Strategy...")
    
    from trading_framework.strategies import RSIStrategy
    
    # Create mock data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100) * 2)
    
    data = pd.DataFrame({
        'open': prices + np.random.randn(100) * 0.5,
        'high': prices + np.abs(np.random.randn(100)),
        'low': prices - np.abs(np.random.randn(100)),
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 100)
    }, index=dates)
    
    # Test strategy
    strategy = RSIStrategy()
    strategy.initialize()
    
    signal = strategy.on_data(data)
    assert 'action' in signal
    assert 'quantity' in signal
    assert 'reason' in signal
    assert signal['action'] in ['buy', 'sell', 'hold']
    
    print(f"✓ RSI Strategy generated signal: {signal['action']}")
    return True


def test_ma_crossover_strategy():
    """Test Moving Average Crossover strategy with mock data."""
    print("\nTesting MA Crossover Strategy...")
    
    from trading_framework.strategies import MovingAverageCrossover
    
    # Create mock data with a trend
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    trend = np.linspace(100, 150, 100)
    noise = np.random.randn(100) * 2
    prices = trend + noise
    
    data = pd.DataFrame({
        'open': prices + np.random.randn(100) * 0.5,
        'high': prices + np.abs(np.random.randn(100)),
        'low': prices - np.abs(np.random.randn(100)),
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 100)
    }, index=dates)
    
    # Test strategy
    strategy = MovingAverageCrossover({'fast_period': 10, 'slow_period': 30})
    strategy.initialize()
    
    signal = strategy.on_data(data)
    assert 'action' in signal
    assert 'quantity' in signal
    assert 'reason' in signal
    assert signal['action'] in ['buy', 'sell', 'hold']
    
    print(f"✓ MA Crossover Strategy generated signal: {signal['action']}")
    return True


def test_backtester():
    """Test backtester with mock data."""
    print("\nTesting Backtester...")
    
    from trading_framework import Backtester
    from trading_framework.strategies import RSIStrategy
    
    # Create mock data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100) * 2)
    
    data = pd.DataFrame({
        'open': prices + np.random.randn(100) * 0.5,
        'high': prices + np.abs(np.random.randn(100)),
        'low': prices - np.abs(np.random.randn(100)),
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 100)
    }, index=dates)
    
    # Create strategy and backtester
    strategy = RSIStrategy({'position_size': 1})
    backtester = Backtester(strategy, initial_cash=10000.0)
    
    # Add data
    backtester.add_data(data)
    
    # Run backtest
    results = backtester.run()
    
    assert 'initial_value' in results
    assert 'final_value' in results
    assert 'return_pct' in results
    assert results['initial_value'] == 10000.0
    
    print(f"✓ Backtester ran successfully")
    print(f"  Initial: ${results['initial_value']:.2f}")
    print(f"  Final: ${results['final_value']:.2f}")
    print(f"  Return: {results['return_pct']:.2f}%")
    return True


def test_config():
    """Test configuration loading."""
    print("\nTesting Config...")
    
    from trading_framework import Config
    
    # Test config creation (won't validate without .env)
    config = Config()
    
    # Test that config has expected attributes
    assert hasattr(config, 'alpaca_api_key')
    assert hasattr(config, 'alpaca_secret_key')
    assert hasattr(config, 'alpaca_trading_mode')
    assert hasattr(config, 'validate')
    assert hasattr(config, 'is_paper_trading')
    
    print("✓ Config structure is correct")
    return True


def main():
    """Run all tests."""
    print("="*80)
    print("TRADING FRAMEWORK VALIDATION TESTS")
    print("="*80)
    
    tests = [
        test_imports,
        test_base_strategy,
        test_config,
        test_rsi_strategy,
        test_ma_crossover_strategy,
        test_backtester,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*80)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
