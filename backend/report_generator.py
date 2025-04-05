"""
Report generator for backtesting results.
Generates a markdown report with details about the backtest.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any
from market_calendar import format_market_time

def generate_backtest_report(backtest_results: Dict[str, Any], strategy: Dict[str, Any]) -> str:
    """
    Generate a comprehensive backtest report in markdown format
    
    Args:
        backtest_results (dict): Results from backtest engine
        strategy (dict): Strategy configuration
        
    Returns:
        str: Markdown formatted report
    """
    # Basic information
    backtest_id = backtest_results.get('backtest_id', str(uuid.uuid4()))
    strategy_name = strategy.get('name', 'Unnamed Strategy')
    strategy_type = strategy.get('type', 'Unknown')
    symbol = strategy.get('symbol', 'Unknown')
    timeframe = strategy.get('timeframe', 'Unknown')
    start_date = backtest_results.get('start_date', 'Unknown')
    end_date = backtest_results.get('end_date', 'Unknown')
    
    # Performance metrics
    initial_capital = backtest_results.get('initial_capital', 0)
    final_value = backtest_results.get('final_value', 0)
    returns = backtest_results.get('returns', 0)
    win_rate = backtest_results.get('win_rate', 0) * 100  # Convert to percentage
    max_drawdown = backtest_results.get('max_drawdown', 0)
    sharpe_ratio = backtest_results.get('sharpe_ratio', 0)
    trade_count = backtest_results.get('trade_count', 0)
    winning_trades = backtest_results.get('winning_trades', 0)
    losing_trades = backtest_results.get('losing_trades', 0)
    
    # Extract trades
    trades = backtest_results.get('trades', [])
    position_tracking = backtest_results.get('position_tracking', [])
    condition_evaluations = backtest_results.get('condition_evaluations', [])
    
    # Market hours validation info
    market_hours_validation = backtest_results.get('market_hours_validation', {})
    market_hours = market_hours_validation.get('market_hours', '9:15 AM - 3:15 PM IST (Monday-Friday)')
    position_events_outside_hours = market_hours_validation.get('position_events_outside_hours', 0)
    condition_evals_outside_hours = market_hours_validation.get('condition_evaluations_outside_hours', 0)
    market_hours_enabled = market_hours_validation.get('enabled', False)
    
    # Generate report
    report = f"""# Backtest Report: {strategy_name}

## Summary
- **Strategy**: {strategy_name} ({strategy_type.capitalize()} strategy)
- **Symbol**: {symbol}
- **Timeframe**: {timeframe}
- **Period**: {start_date} to {end_date}
- **Initial Capital**: ₹{initial_capital:,.2f}
- **Final Value**: ₹{final_value:,.2f}
- **Returns**: {returns:.2f}%
- **Win Rate**: {win_rate:.2f}%
- **Max Drawdown**: {max_drawdown:.2f}%
- **Sharpe Ratio**: {sharpe_ratio:.2f}
- **Trades**: {trade_count} ({winning_trades} winning, {losing_trades} losing)

## Market Hours Validation
- **Market Hours**: {market_hours}
- **Validation Enabled**: {market_hours_enabled}
- **Position Events Outside Market Hours**: {position_events_outside_hours}
- **Condition Evaluations Outside Market Hours**: {condition_evals_outside_hours}

## Entry & Exit Conditions
"""
    
    # Add entry conditions
    report += "### Entry Conditions\n"
    for i, condition in enumerate(strategy.get('entry_conditions', []), 1):
        if 'indicator' in condition and 'variable' in condition:
            report += f"{i}. Create indicator: {condition.get('indicator', 'Unknown')} as {condition.get('variable', 'Unknown')}"
            if 'params' in condition:
                params_str = ', '.join([f"{k}={v}" for k, v in condition.get('params', {}).items()])
                report += f" with parameters: {params_str}"
            report += "\n"
        elif 'condition' in condition or 'comparison' in condition:
            comp = condition.get('comparison', condition.get('condition', 'Unknown'))
            var = condition.get('variable', 'Unknown')
            threshold = condition.get('threshold', 'Unknown')
            report += f"{i}. When {var} {comp} {threshold}\n"
    
    # Add exit conditions
    report += "\n### Exit Conditions\n"
    for i, condition in enumerate(strategy.get('exit_conditions', []), 1):
        if 'indicator' in condition and 'variable' in condition:
            report += f"{i}. Create indicator: {condition.get('indicator', 'Unknown')} as {condition.get('variable', 'Unknown')}"
            if 'params' in condition:
                params_str = ', '.join([f"{k}={v}" for k, v in condition.get('params', {}).items()])
                report += f" with parameters: {params_str}"
            report += "\n"
        elif 'condition' in condition or 'comparison' in condition:
            comp = condition.get('comparison', condition.get('condition', 'Unknown'))
            var = condition.get('variable', 'Unknown')
            threshold = condition.get('threshold', 'Unknown')
            report += f"{i}. When {var} {comp} {threshold}\n"
    
    # Add stop loss and take profit if present
    if 'stop_loss' in strategy and strategy['stop_loss'] > 0:
        report += f"\n**Stop Loss**: {strategy['stop_loss']}%\n"
    if 'target_profit' in strategy and strategy['target_profit'] > 0:
        report += f"**Take Profit**: {strategy['target_profit']}%\n"
    
    # Add trade list
    report += "\n## Trade List\n"
    report += "| # | Action | Timestamp | Price | Size | Reason | Portfolio Value |\n"
    report += "|---|--------|-----------|-------|------|--------|----------------|\n"
    
    for i, trade in enumerate(position_tracking, 1):
        action = trade.get('action', '')
        timestamp = trade.get('timestamp', '')
        price = trade.get('price', 0)
        size = trade.get('size', 0)
        reason = trade.get('reason', '')
        portfolio = trade.get('portfolio_value', 0)
        
        # Add market hours validation indicator
        is_valid_time = trade.get('is_market_hours', True)
        time_indicator = "" if is_valid_time else " ⚠️"
        
        report += f"| {i} | {action} | {timestamp}{time_indicator} | {price:.2f} | {size:.2f} | {reason} | {portfolio:.2f} |\n"
    
    # Add explanation for market hours validation
    if market_hours_enabled:
        report += "\n**Note**: ⚠️ indicates timestamps that were adjusted to conform to market hours.\n"
    
    # Add condition evaluation tracking
    report += "\n### Condition Evaluation Tracking\n"
    report += "The table below shows how conditions were evaluated at key decision points:\n\n"
    report += "| Bar | Timestamp | Condition | Variable | Value | Comparison | Threshold | Result |\n"
    report += "|-----|-----------|-----------|----------|-------|------------|-----------|--------|\n"
    
    # Limit to 20 rows for readability
    eval_count = 0
    for eval_data in condition_evaluations:
        if eval_count >= 20:
            break
            
        bar_number = eval_data.get('bar_number', '')
        timestamp = eval_data.get('timestamp', '')
        
        # Add market hours validation indicator
        is_valid_time = eval_data.get('is_market_hours', True)
        time_indicator = "" if is_valid_time else " ⚠️"
        
        for condition in eval_data.get('conditions', []):
            if eval_count >= 20:
                break
                
            condition_type = condition.get('type', '')
            variable = condition.get('variable', '')
            value = condition.get('value', '')
            comparison = condition.get('comparison', '')
            threshold = condition.get('threshold', '')
            result = '✓' if condition.get('result', False) else '✗'
            
            report += f"| {bar_number} | {timestamp}{time_indicator} | {condition_type} | {variable} | {value} | {comparison} | {threshold} | {result} |\n"
            eval_count += 1
    
    # Add explanation if we truncated the table
    if len(condition_evaluations) > 20:
        report += "\n*Table truncated to 20 rows for readability.*\n"
    
    return report

def save_backtest_report(backtest_results, strategy, output_dir=None):
    """
    Generate and save a backtest report to a file
    
    Args:
        backtest_results (dict): Results from backtest engine
        strategy (dict): Strategy configuration
        output_dir (str, optional): Directory to save the report. Defaults to './reports'.
        
    Returns:
        str: Path to the generated report file
    """
    # Generate the report
    report_content = generate_backtest_report(backtest_results, strategy)
    
    # Create output directory if it doesn't exist
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), 'reports')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create filename
    backtest_id = backtest_results.get('backtest_id', str(uuid.uuid4()))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backtest_report_{backtest_id}.md"
    filepath = os.path.join(output_dir, filename)
    
    # Write to file
    with open(filepath, 'w') as f:
        f.write(report_content)
    
    return filepath
