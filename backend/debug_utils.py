import os
import uuid
from datetime import datetime
import json
import inspect

def save_strategy_comparison(strategy, bt_strategy_class, backtrader_interpretation, logger, backtest_results=None):
    """
    Save a comparison of the user-defined strategy, backtrader interpretation, and dynamic class code
    to a fixed file named strategy-comparison.md
    
    Args:
        strategy (dict): Original user-defined strategy
        bt_strategy_class (type): Dynamically created Backtrader strategy class
        backtrader_interpretation (dict): How Backtrader interpreted and processed the strategy
        logger: Logger instance
        backtest_results (dict, optional): Results from backtest execution
    """
    try:
        # Create debug directory if it doesn't exist
        debug_dir = os.path.join(os.path.dirname(__file__), 'debug')
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        
        # Use a fixed filename
        debug_file_path = os.path.join(debug_dir, "strategy-comparison.md")
        
        # Try to get the source code of the dynamic strategy class
        try:
            # This might not work for all dynamically created classes
            strategy_class_code = inspect.getsource(bt_strategy_class)
        except Exception as e:
            logger.warning(f"Could not get source code for dynamic class: {str(e)}")
            # Fallback to a simple representation
            strategy_class_code = f"# Could not get source code: {str(e)}\n"
            strategy_class_code += f"# Class name: {bt_strategy_class.__name__}\n"
            strategy_class_code += f"# Class methods: {', '.join([m for m in dir(bt_strategy_class) if not m.startswith('_')])}"
        
        # Create markdown content
        md_content = f"""# Strategy Comparison
        
## 1. Original User-Defined Strategy
```json
{json.dumps(strategy, indent=2)}
```

## 2. Backtrader Interpretation of Strategy
### Strategy Type and Parameters
```json
{json.dumps(backtrader_interpretation.get('strategy_params', {}), indent=2)}
```

### Indicator Processing
```json
{json.dumps(backtrader_interpretation.get('indicators', {}), indent=2)}
```

### Data Feed Configuration
```json
{json.dumps(backtrader_interpretation.get('data_feed', {}), indent=2)}
```

### Entry & Exit Condition Interpretation
```json
{json.dumps(backtrader_interpretation.get('conditions', {}), indent=2)}
```

## 3. Dynamically Created Backtrader Strategy Class
```python
{strategy_class_code}
```
"""
        
        # Write to file
        with open(debug_file_path, 'w') as f:
            f.write(md_content)
        
        logger.info(f"Saved strategy comparison to {debug_file_path}")
        return debug_file_path
        
    except Exception as e:
        logger.error(f"Error saving strategy comparison: {str(e)}")
        return None

def save_strategy_debug_info(strategy, bt_strategy_class, logger, backtest_results=None):
    """
    Save debug information about a strategy and its backtrader implementation to a file
    
    Args:
        strategy (dict): Original user-defined strategy
        bt_strategy_class (type): Dynamically created Backtrader strategy class
        logger: Logger instance
        backtest_results (dict, optional): Results from backtest execution
    """
    try:
        # Create debug directory if it doesn't exist
        debug_dir = os.path.join(os.path.dirname(__file__), 'debug')
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        
        # Generate a unique ID for this debug file
        debug_id = str(uuid.uuid4())[:8]  # Use shorter ID for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a filename with strategy ID and timestamp
        strategy_id = strategy.get('strategy_id', 'unknown')
        filename = f"{strategy_id}_{timestamp}_{debug_id}_debug.md"
        debug_file_path = os.path.join(debug_dir, filename)
        
        # Try to get the source code of the dynamic strategy class
        try:
            # This might not work for all dynamically created classes
            strategy_class_code = inspect.getsource(bt_strategy_class)
        except Exception as e:
            logger.warning(f"Could not get source code for dynamic class: {str(e)}")
            # Fallback to a simple representation
            strategy_class_code = f"# Could not get source code: {str(e)}\n"
            strategy_class_code += f"# Class name: {bt_strategy_class.__name__}\n"
            strategy_class_code += f"# Class methods: {', '.join([m for m in dir(bt_strategy_class) if not m.startswith('_')])}"
        
        # Create markdown content
        md_content = f"""# Strategy Debug Information

## Basic Information
- Debug ID: {debug_id}
- Timestamp: {datetime.now().isoformat()}
- Strategy ID: {strategy_id}
- Strategy Name: {strategy.get('name', 'Unknown')}

## Original User-Defined Strategy
```json
{json.dumps(strategy, indent=2)}
```

## Backtrader Strategy Information
- Strategy Type: {strategy.get('type', 'Unknown')}
- Symbol: {strategy.get('symbol', 'Unknown')}
- Timeframe: {strategy.get('timeframe', 'Unknown')}

### Entry Conditions
```json
{json.dumps(strategy.get('entry_conditions', []), indent=2)}
```

### Exit Conditions
```json
{json.dumps(strategy.get('exit_conditions', []), indent=2)}
```

## Dynamically Created Backtrader Strategy Class
```python
{strategy_class_code}
```

{"" if backtest_results is None else f'''
## Backtest Results Summary
- Returns: {backtest_results.get('returns', 'N/A')}%
- Win Rate: {backtest_results.get('win_rate', 'N/A') * 100:.2f}%
- Trade Count: {backtest_results.get('trade_count', 'N/A')}
- Winning Trades: {backtest_results.get('winning_trades', 'N/A')}
- Losing Trades: {backtest_results.get('losing_trades', 'N/A')}
- Max Drawdown: {backtest_results.get('max_drawdown', 'N/A')}%
- Sharpe Ratio: {backtest_results.get('sharpe_ratio', 'N/A')}

### Trades List
```json
{json.dumps(backtest_results.get('trades', []), indent=2)}
```
'''}
"""
        
        # Write to file
        with open(debug_file_path, 'w') as f:
            f.write(md_content)
        
        logger.info(f"Saved strategy debug information to {debug_file_path}")
        return debug_file_path
        
    except Exception as e:
        logger.error(f"Error saving strategy debug information: {str(e)}")
        return None
