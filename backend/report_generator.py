import os
import json
from datetime import datetime
import logging

# Get the logger
logger = logging.getLogger(__name__)

# Helper function to format datetime objects for json serialization
def format_datetime(value):
    """Format datetime objects to string for JSON serialization"""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value

def generate_position_tracking_section(backtest_results):
    """Generate section about position tracking"""
    try:
        position_data = backtest_results.get('position_tracking', [])
        
        if not position_data:
            return """## 9. Position Tracking

Detailed position tracking information is not available for this backtest.
"""
        
        # Generate position tracking table
        position_table = "| # | Action | Timestamp | Price | Size | Reason | Portfolio Value |\n"
        position_table += "|---|--------|-----------|-------|------|--------|---------------|\n"
        
        for idx, position_event in enumerate(position_data, 1):
            action = position_event.get('action', 'N/A')
            timestamp = position_event.get('timestamp', 'N/A')
            price = position_event.get('price', 0)
            size = position_event.get('size', 0)
            reason = position_event.get('reason', 'N/A')
            portfolio_value = position_event.get('portfolio_value', 0)
            
            row = f"| {idx} | {action} | {timestamp} | {price:.2f} | {size:.2f} | {reason} | {portfolio_value:.2f} |\n"
            position_table += row
        
        # Create a position lifecycle visualization (hold duration)
        position_lifecycles = []
        current_entry = None
        
        for event in position_data:
            action = event.get('action', '')
            if action == 'ENTRY':
                current_entry = event
            elif action == 'EXIT' and current_entry:
                entry_time = current_entry.get('timestamp')
                exit_time = event.get('timestamp')
                
                try:
                    # Make sure both are strings first
                    entry_time_str = format_datetime(entry_time) if isinstance(entry_time, datetime) else str(entry_time)
                    exit_time_str = format_datetime(exit_time) if isinstance(exit_time, datetime) else str(exit_time)
                    
                    # Parse the string timestamps to datetime objects
                    entry_dt = datetime.strptime(entry_time_str, '%Y-%m-%d %H:%M:%S')
                    exit_dt = datetime.strptime(exit_time_str, '%Y-%m-%d %H:%M:%S')
                    duration = (exit_dt - entry_dt).total_seconds() / 3600  # hours
                    
                    position_lifecycles.append({
                        'entry': entry_time,
                        'exit': exit_time,
                        'duration_hours': duration,
                        'entry_price': current_entry.get('price', 0),
                        'exit_price': event.get('price', 0),
                        'profit_pct': event.get('profit_pct', 0)
                    })
                except Exception as e:
                    logger.warning(f"Error calculating position duration: {str(e)}")
                
                current_entry = None
        
        # Generate duration statistics
        duration_stats = ""
        if position_lifecycles:
            durations = [p['duration_hours'] for p in position_lifecycles]
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            
            # Format durations for readability
            if avg_duration >= 24:
                avg_duration_str = f"{avg_duration/24:.2f} days"
            else:
                avg_duration_str = f"{avg_duration:.2f} hours"
                
            if min_duration >= 24:
                min_duration_str = f"{min_duration/24:.2f} days"
            else:
                min_duration_str = f"{min_duration:.2f} hours"
                
            if max_duration >= 24:
                max_duration_str = f"{max_duration/24:.2f} days"
            else:
                max_duration_str = f"{max_duration:.2f} hours"
            
            # Calculate profitability by hold time
            profitable_positions = [p for p in position_lifecycles if p['profit_pct'] > 0]
            unprofitable_positions = [p for p in position_lifecycles if p['profit_pct'] <= 0]
            
            avg_profitable_duration = sum([p['duration_hours'] for p in profitable_positions]) / len(profitable_positions) if profitable_positions else 0
            avg_unprofitable_duration = sum([p['duration_hours'] for p in unprofitable_positions]) / len(unprofitable_positions) if unprofitable_positions else 0
            
            if avg_profitable_duration >= 24:
                avg_profitable_str = f"{avg_profitable_duration/24:.2f} days"
            else:
                avg_profitable_str = f"{avg_profitable_duration:.2f} hours"
                
            if avg_unprofitable_duration >= 24:
                avg_unprofitable_str = f"{avg_unprofitable_duration/24:.2f} days"
            else:
                avg_unprofitable_str = f"{avg_unprofitable_duration:.2f} hours"
            
            duration_stats = f"""
### Position Duration Statistics
- **Average Position Duration**: {avg_duration_str}
- **Shortest Position**: {min_duration_str}
- **Longest Position**: {max_duration_str}
- **Average Duration of Profitable Trades**: {avg_profitable_str}
- **Average Duration of Unprofitable Trades**: {avg_unprofitable_str}
"""
        
        position_section = f"""## 9. Position Tracking

### Position Events
{position_table}

{duration_stats}

### Position Management
The engine managed positions according to the strategy rules:
- Entries were triggered when entry conditions were met
- Exits were triggered by exit conditions, stop loss, or take profit
- All positions were managed with the default position sizing (1 unit)
- Position tracking helps identify patterns between hold duration and profitability
"""
        return position_section
    except Exception as e:
        logger.error(f"Error generating position tracking section: {str(e)}")
        return "## 9. Position Tracking\n\nError generating position tracking section"

def generate_backtest_report_markdown(strategy, backtest_results):
    """
    Generate a comprehensive markdown report for a backtest
    
    Args:
        strategy (dict): Strategy configuration
        backtest_results (dict): Results from the backtest
        
    Returns:
        str: Markdown formatted report content
    """
    try:
        # Create report sections
        sections = []
        
        # 1. Strategy Definition
        sections.append(generate_strategy_section(strategy))
        
        # 2. Backtest Parameters
        sections.append(generate_parameters_section(backtest_results))
        
        # 3. Backtest Engine Interpretation
        sections.append(generate_engine_interpretation_section(strategy, backtest_results))
        
        # 4. Backtest Execution Steps
        sections.append(generate_execution_steps_section(strategy, backtest_results))
        
        # 5. Indicator Calculations
        sections.append(generate_indicators_section(strategy, backtest_results))
        
        # 6. Condition Evaluations - Pass backtest_results to include condition tracking
        sections.append(generate_conditions_section(strategy, backtest_results))
        
        # 7. Trades
        sections.append(generate_trades_section(backtest_results))
        
        # 8. Performance Metrics
        sections.append(generate_metrics_section(backtest_results))
        
        # 9. Position Tracking - NEW SECTION
        sections.append(generate_position_tracking_section(backtest_results))
        
        # Combine all sections
        report_content = "\n\n".join(sections)
        
        return report_content
    except Exception as e:
        logger.error(f"Error generating backtest report markdown: {str(e)}")
        return f"""# Backtest Report Generation Error

An error occurred while generating the backtest report: {str(e)}

Please contact support with the following details:
- Strategy ID: {strategy.get('strategy_id', 'Unknown')}
- Backtest ID: {backtest_results.get('backtest_id', 'Unknown')}
- Error: {str(e)}
"""

def generate_strategy_section(strategy):
    """Generate the strategy definition section"""
    try:
        strategy_name = strategy.get('name', 'Unnamed Strategy')
        strategy_type = strategy.get('type', 'Unknown Type').upper()
        symbol = strategy.get('symbol', 'Unknown Symbol')
        timeframe = strategy.get('timeframe', 'Unknown Timeframe')
        
        content = f"""# Backtest Report for {strategy_name}

## 1. Strategy Definition

### Basic Information
- **Strategy Name**: {strategy_name}
- **Strategy ID**: {strategy.get('strategy_id', 'Unknown ID')}
- **Strategy Type**: {strategy_type}
- **Symbol**: {symbol}
- **Timeframe**: {timeframe}

### User Defined Strategy Configuration
```json
{json.dumps(strategy, indent=2)}
```
"""
        return content
    except Exception as e:
        logger.error(f"Error generating strategy section: {str(e)}")
        return "## 1. Strategy Definition\n\nError generating strategy section"

def generate_parameters_section(backtest_results):
    """Generate the backtest parameters section"""
    try:
        start_date = backtest_results.get('start_date', 'Unknown')
        end_date = backtest_results.get('end_date', 'Unknown')
        initial_capital = backtest_results.get('initial_capital', 0)
        
        content = f"""## 2. Backtest Parameters

- **Start Date**: {start_date}
- **End Date**: {end_date}
- **Initial Capital**: ${initial_capital:,.2f}
- **Backtest ID**: {backtest_results.get('backtest_id', 'Unknown')}
"""
        return content
    except Exception as e:
        logger.error(f"Error generating parameters section: {str(e)}")
        return "## 2. Backtest Parameters\n\nError generating parameters section"

def generate_engine_interpretation_section(strategy, backtest_results):
    """Generate section about how the backtest engine interpreted the strategy"""
    try:
        # Try to find debug files related to this backtest
        debug_dir = os.path.join(os.path.dirname(__file__), 'debug')
        
        # Look for the strategy-comparison.md file
        if os.path.exists(os.path.join(debug_dir, "strategy-comparison.md")):
            with open(os.path.join(debug_dir, "strategy-comparison.md"), 'r') as f:
                comparison_content = f.read()
                
            # Extract the Backtrader Interpretation section
            try:
                start_marker = "## 2. Backtrader Interpretation of Strategy"
                end_marker = "## 3. Dynamically Created Backtrader Strategy Class"
                
                if start_marker in comparison_content and end_marker in comparison_content:
                    start_idx = comparison_content.find(start_marker)
                    end_idx = comparison_content.find(end_marker)
                    
                    interpretation_content = comparison_content[start_idx:end_idx].strip()
                    
                    content = f"""## 3. Backtest Engine Interpretation

{interpretation_content}
"""
                    return content
            except Exception as e:
                logger.error(f"Error extracting interpretation content: {str(e)}")
        
        # Fallback if we can't find the interpretation or extract it properly
        content = f"""## 3. Backtest Engine Interpretation

The backtest engine interprets your strategy definition and converts it into executable code.
It processes your entry and exit conditions, calculates indicators, and manages trades according to your rules.

### Strategy Type
The engine interprets this as a {strategy.get('type', 'unknown').upper()} strategy.

### Entry Conditions Interpretation
```json
{json.dumps(strategy.get('entry_conditions', []), indent=2)}
```

### Exit Conditions Interpretation
```json
{json.dumps(strategy.get('exit_conditions', []), indent=2)}
```
"""
        return content
    except Exception as e:
        logger.error(f"Error generating engine interpretation section: {str(e)}")
        return "## 3. Backtest Engine Interpretation\n\nError generating engine interpretation section"

def generate_execution_steps_section(strategy, backtest_results):
    """Generate section detailing the backtest execution steps"""
    try:
        content = f"""## 4. Backtest Execution Steps

The backtest engine follows these steps when executing a backtest:

1. **Initialize Backtest Environment**
   - Set up the backtest with initial capital of ${backtest_results.get('initial_capital', 0):,.2f}
   - Configure date range: {backtest_results.get('start_date', 'Unknown')} to {backtest_results.get('end_date', 'Unknown')}
   - Set up commission structure (0% commission in the current implementation)

2. **Load Historical Data**
   - Fetch historical price data for {strategy.get('symbol', 'the symbol')} with {strategy.get('timeframe', 'the selected')} timeframe
   - Validate data quality and completeness
   - Prepare data for indicator calculations

3. **Calculate Technical Indicators**
   - Process all indicators defined in the strategy
   - Add indicator values to the price data
   - Validate indicator calculations

4. **Create Trading Strategy**
   - Dynamically generate a Backtrader strategy class based on user-defined conditions
   - Set up entry logic based on {len(strategy.get('entry_conditions', []))} conditions
   - Set up exit logic based on {len(strategy.get('exit_conditions', []))} conditions
   - Configure stop-loss at {strategy.get('stop_loss', 0)}% and take-profit at {strategy.get('target_profit', 0)}%

5. **Execute Backtest Simulation**
   - Process each bar (candle) of historical data sequentially
   - Evaluate entry conditions when not in a position
   - Evaluate exit conditions when in a position
   - Track equity curve, drawdowns, and returns

6. **Process Results**
   - Calculate performance metrics (returns, win rate, drawdown, etc.)
   - Compile trade list with entry/exit details
   - Generate final performance report
"""
        return content
    except Exception as e:
        logger.error(f"Error generating execution steps section: {str(e)}")
        return "## 4. Backtest Execution Steps\n\nError generating execution steps section"

def generate_indicators_section(strategy, backtest_results):
    """Generate section about indicators used and their calculations"""
    try:
        indicators_used = []
        
        # Extract indicators from conditions
        for condition in strategy.get('entry_conditions', []) + strategy.get('exit_conditions', []):
            if 'indicator' in condition and 'variable' in condition:
                indicator_type = condition.get('indicator', 'Unknown')
                variable_name = condition.get('variable', 'Unknown')
                params = condition.get('params', {})
                
                # Avoid duplicates
                if not any(i['variable'] == variable_name for i in indicators_used):
                    indicators_used.append({
                        'type': indicator_type,
                        'variable': variable_name,
                        'params': params
                    })
        
        # If no indicators are found
        if not indicators_used:
            return """## 5. Indicator Calculations

No technical indicators were used in this strategy.
"""
        
        # Look for backtrader interpretation data
        debug_dir = os.path.join(os.path.dirname(__file__), 'debug')
        backtrader_indicators = {}
        
        if os.path.exists(os.path.join(debug_dir, "strategy-comparison.md")):
            try:
                with open(os.path.join(debug_dir, "strategy-comparison.md"), 'r') as f:
                    comparison_content = f.read()
                
                # Try to extract indicator section
                if "### Indicator Processing" in comparison_content:
                    section_start = comparison_content.find("### Indicator Processing")
                    section_end = comparison_content.find("###", section_start + 1)
                    if section_end == -1:  # If there's no next section
                        section_end = comparison_content.find("##", section_start + 1)
                    
                    if section_end > section_start:
                        indicator_section = comparison_content[section_start:section_end]
                        # Look for json block
                        json_start = indicator_section.find("```json")
                        json_end = indicator_section.find("```", json_start + 6)
                        
                        if json_start > -1 and json_end > json_start:
                            json_str = indicator_section[json_start + 7:json_end].strip()
                            try:
                                backtrader_indicators = json.loads(json_str)
                            except json.JSONDecodeError:
                                logger.warning("Failed to parse indicator JSON from strategy comparison")
            except Exception as e:
                logger.warning(f"Error reading strategy comparison: {str(e)}")
        
        # Generate content for each indicator
        indicators_content = []
        for idx, indicator in enumerate(indicators_used, 1):
            indicator_type = indicator['type']
            variable_name = indicator['variable']
            params = indicator['params']
            params_str = ", ".join([f"{k}={v}" for k, v in params.items()])
            
            # Get additional information from backtrader interpretation if available
            additional_info = ""
            if variable_name in backtrader_indicators:
                bt_info = backtrader_indicators[variable_name]
                if 'sample_values' in bt_info and bt_info['sample_values']:
                    sample_values = bt_info['sample_values']
                    if isinstance(sample_values, list) and len(sample_values) > 0:
                        sample_str = ", ".join([f"{val:.6f}" if isinstance(val, float) else str(val) for val in sample_values])
                        additional_info += f"\n- **Sample Values**: {sample_str}"
                
                if 'found_in_data' in bt_info:
                    additional_info += f"\n- **Successfully Added to Data**: {'Yes' if bt_info['found_in_data'] else 'No'}"
                    
                if 'actual_column' in bt_info and bt_info['actual_column'] != variable_name:
                    additional_info += f"\n- **Actual Column Name in Data**: {bt_info['actual_column']}"
            
            indicators_content.append(f"""### {indicator_type} - {variable_name}
- **Type**: {indicator_type}
- **Variable Name**: {variable_name}
- **Parameters**: {params_str or "Default parameters"}{additional_info}

The {indicator_type} indicator is calculated based on the price data and used in the strategy's decision-making process.
""")
        
        indicators_section = f"""## 5. Indicator Calculations

The following technical indicators were used in this strategy:

{"".join(indicators_content)}
"""
        return indicators_section
    except Exception as e:
        logger.error(f"Error generating indicators section: {str(e)}")
        return "## 5. Indicator Calculations\n\nError generating indicators section"

def generate_conditions_section(strategy, backtest_results=None):
    """Generate section about entry and exit conditions with tracking"""
    try:
        entry_conditions = strategy.get('entry_conditions', [])
        exit_conditions = strategy.get('exit_conditions', [])
        
        # Filter out indicator definitions from conditions
        entry_rules = [c for c in entry_conditions if 'comparison' in c or 'condition' in c]
        exit_rules = [c for c in exit_conditions if 'comparison' in c or 'condition' in c]
        
        # Entry conditions
        entry_content = "### Entry Conditions\n"
        if entry_rules:
            for idx, condition in enumerate(entry_rules, 1):
                comparison = condition.get('comparison', condition.get('condition', 'Unknown'))
                variable = condition.get('variable', 'Unknown')
                threshold = condition.get('threshold', 'N/A')
                action = condition.get('action', 'Unknown')
                
                entry_content += f"- **Condition {idx}**: {variable} {comparison} {threshold} → {action.upper()}\n"
        else:
            entry_content += "No specific entry conditions defined.\n"
        
        # Exit conditions
        exit_content = "\n### Exit Conditions\n"
        if exit_rules:
            for idx, condition in enumerate(exit_rules, 1):
                comparison = condition.get('comparison', condition.get('condition', 'Unknown'))
                variable = condition.get('variable', 'Unknown')
                threshold = condition.get('threshold', 'N/A')
                action = condition.get('action', 'Unknown')
                
                exit_content += f"- **Condition {idx}**: {variable} {comparison} {threshold} → {action.upper()}\n"
        else:
            exit_content += "No specific exit conditions defined.\n"
        
        # Stop loss and take profit
        risk_management = "\n### Risk Management\n"
        stop_loss = strategy.get('stop_loss', 0)
        target_profit = strategy.get('target_profit', 0)
        
        if stop_loss > 0:
            risk_management += f"- **Stop Loss**: {stop_loss}%\n"
        else:
            risk_management += "- **Stop Loss**: Not set\n"
            
        if target_profit > 0:
            risk_management += f"- **Take Profit**: {target_profit}%\n"
        else:
            risk_management += "- **Take Profit**: Not set\n"
        
        # Condition evaluation explanation
        evaluation_explanation = f"""
### Condition Evaluation Process

When evaluating {strategy.get('type', 'buy/sell').upper()} opportunities, the engine:

1. Checks if all entry conditions are satisfied at the current bar
2. Makes sure there's enough historical data for indicators to be valid
3. When conditions are met, enters a position with the default position size

When in a position, the engine evaluates:

1. Stop loss and take profit thresholds first (if set)
2. Then checks all exit conditions
3. If any exit condition is met, exits the position completely
"""
        
        # Add condition tracking section
        condition_tracking = ""
        
        # Check if we have backtest results and condition evaluation data
        if backtest_results and 'condition_evaluations' in backtest_results:
            condition_evals = backtest_results.get('condition_evaluations', [])
            if condition_evals:
                condition_tracking = """
### Condition Evaluation Tracking

The table below shows how conditions were evaluated at key decision points:

| Bar | Timestamp | Condition | Variable | Value | Comparison | Threshold | Result |
|-----|-----------|-----------|----------|-------|------------|-----------|--------|
"""
                # Filter to just include significant evaluation points (where trades occurred)
                trade_timestamps = set()
                for trade in backtest_results.get('trades', []):
                    entry_date = trade.get('entry_date')
                    exit_date = trade.get('exit_date')
                    if entry_date:
                        trade_timestamps.add(entry_date)
                    if exit_date:
                        trade_timestamps.add(exit_date)
                
                # Add evaluations near trade points or a limited sample
                num_tracked = 0
                trade_related_evals = []
                sample_evals = []
                
                for eval_point in condition_evals:
                    timestamp = eval_point.get('timestamp')
                    if not timestamp:
                        continue
                        
                    bar_num = eval_point.get('bar_number')
                    
                    # Check if this is near a trade timestamp
                    is_trade_point = False
                    for trade_time in trade_timestamps:
                        try:
                            # Make sure both are strings first
                            eval_time_str = format_datetime(timestamp) if isinstance(timestamp, datetime) else str(timestamp)
                            trade_time_str = format_datetime(trade_time) if isinstance(trade_time, datetime) else str(trade_time)
                            
                            # Now parse them
                            eval_dt = datetime.strptime(eval_time_str, '%Y-%m-%d %H:%M:%S')
                            trade_dt = datetime.strptime(trade_time_str, '%Y-%m-%d %H:%M:%S')
                            
                            if abs((eval_dt - trade_dt).total_seconds()) < 3600:  # Within an hour
                                is_trade_point = True
                                break
                        except Exception as e:
                            logger.warning(f"Error comparing timestamps: {str(e)}")
                    
                    if is_trade_point:
                        trade_related_evals.append(eval_point)
                    elif len(sample_evals) < 10:  # Keep a small sample of non-trade points
                        sample_evals.append(eval_point)
                
                # Prioritize trade-related evaluations
                evals_to_show = trade_related_evals + sample_evals
                evals_to_show = evals_to_show[:20]  # Limit to a reasonable number
                
                for eval_point in evals_to_show:
                    timestamp = eval_point.get('timestamp')
                    bar_num = eval_point.get('bar_number')
                    
                    for condition in eval_point.get('conditions', []):
                        condition_type = condition.get('type', '')
                        variable = condition.get('variable', '')
                        value = condition.get('value', '')
                        comparison = condition.get('comparison', '')
                        threshold = condition.get('threshold', '')
                        result = condition.get('result', False)
                        
                        # Format the value for display
                        value_str = 'N/A'
                        if value is not None:
                            try:
                                value_str = f"{float(value):.4f}" if isinstance(value, (int, float)) else str(value)
                            except:
                                value_str = str(value)
                        
                        # Add a row to the table
                        condition_tracking += f"| {bar_num} | {timestamp} | {condition_type.capitalize()} | {variable} | {value_str} | {comparison} | {threshold} | {'✓' if result else '✗'} |\n"
                        
                        num_tracked += 1
                
                if num_tracked == 0:
                    condition_tracking += "| - | - | No condition evaluations available | - | - | - | - | - |\n"
            else:
                condition_tracking = """
### Condition Evaluation Tracking

Detailed condition evaluation tracking is not available for this backtest run.
"""
        else:
            condition_tracking = """
### Condition Evaluation Tracking

Detailed condition evaluation tracking is not available for this backtest.
"""
        
        # Create the complete section
        conditions_section = f"""## 6. Condition Evaluations

{entry_content}

{exit_content}

{risk_management}

{evaluation_explanation}

{condition_tracking}
"""
        return conditions_section
    except Exception as e:
        logger.error(f"Error generating conditions section: {str(e)}")
        return "## 6. Condition Evaluations\n\nError generating conditions section"

def generate_trades_section(backtest_results):
    """Generate section about trades executed"""
    try:
        trades = backtest_results.get('trades', [])
        
        if not trades:
            return """## 7. Trades

No trades were executed during this backtest period.
"""
        
        # Generate trade summary
        trade_count = len(trades)
        winning_trades = backtest_results.get('winning_trades', 0)
        losing_trades = backtest_results.get('losing_trades', 0)
        win_rate = backtest_results.get('win_rate', 0) * 100
        
        # Calculate average profit/loss
        if trades:
            total_profit_pct = sum(trade.get('profit_pct', 0) for trade in trades)
            avg_profit_pct = total_profit_pct / len(trades)
            
            # Calculate average holding period
            holding_periods = []
            for trade in trades:
                entry_date = trade.get('entry_date')
                exit_date = trade.get('exit_date')
                
                if entry_date and exit_date:
                    try:
                        # Try to parse dates and calculate difference
                        entry_dt = datetime.strptime(entry_date, '%Y-%m-%d %H:%M:%S')
                        exit_dt = datetime.strptime(exit_date, '%Y-%m-%d %H:%M:%S')
                        days_held = (exit_dt - entry_dt).days
                        holding_periods.append(days_held)
                    except Exception as e:
                        logger.warning(f"Error calculating holding period: {str(e)}")
            
            avg_days_held = sum(holding_periods) / len(holding_periods) if holding_periods else "N/A"
        else:
            avg_profit_pct = 0
            avg_days_held = "N/A"
        
        # Generate a table of trades
        trades_table = "| # | Entry Date | Entry Price | Exit Date | Exit Price | Profit (%) | Profit (Points) |\n"
        trades_table += "|---|------------|------------|-----------|-----------|------------|------------------|\n"
        
        for idx, trade in enumerate(trades, 1):
            entry_date = trade.get('entry_date', 'N/A')
            entry_price = trade.get('entry_price', 0)
            exit_date = trade.get('exit_date', 'N/A')
            exit_price = trade.get('exit_price', 0)
            profit_pct = trade.get('profit_pct', 0)
            profit_points = trade.get('profit_points', 0)
            
            row = f"| {idx} | {entry_date} | {entry_price:.2f} | {exit_date} | {exit_price:.2f} | {profit_pct:.2f}% | {profit_points:.2f} |\n"
            trades_table += row
        
        trades_section = f"""## 7. Trades

### Trade Summary
- **Total Trades**: {trade_count}
- **Winning Trades**: {winning_trades} ({win_rate:.2f}%)
- **Losing Trades**: {losing_trades} ({100 - win_rate:.2f}%)
- **Average Profit/Loss**: {avg_profit_pct:.2f}%
- **Average Holding Period**: {avg_days_held if isinstance(avg_days_held, str) else f"{avg_days_held:.2f} days"}

### Trade List
{trades_table}
"""
        return trades_section
    except Exception as e:
        logger.error(f"Error generating trades section: {str(e)}")
        return "## 7. Trades\n\nError generating trades section"

def generate_metrics_section(backtest_results):
    """Generate section about performance metrics"""
    try:
        initial_capital = backtest_results.get('initial_capital', 0)
        final_value = backtest_results.get('final_value', 0)
        returns = backtest_results.get('returns', 0)
        win_rate = backtest_results.get('win_rate', 0) * 100
        max_drawdown = backtest_results.get('max_drawdown', 0)
        sharpe_ratio = backtest_results.get('sharpe_ratio', 0)
        trade_count = backtest_results.get('trade_count', 0)
        
        # Calculate additional metrics
        profit_amount = final_value - initial_capital
        
        # Check if we have equity curve data
        has_equity_curve = 'equity_curve' in backtest_results and backtest_results['equity_curve']
        equity_curve_note = """
### Equity Curve
An equity curve showing the portfolio value over time is available in the backtest results but not included in this text report.
"""
        
        metrics_section = f"""## 8. Performance Metrics

### Summary
- **Initial Capital**: ${initial_capital:,.2f}
- **Final Portfolio Value**: ${final_value:,.2f}
- **Absolute Profit/Loss**: ${profit_amount:,.2f}
- **Return**: {returns:.2f}%
- **Win Rate**: {win_rate:.2f}%
- **Maximum Drawdown**: {max_drawdown:.2f}%
- **Sharpe Ratio**: {sharpe_ratio:.2f}
- **Total Trades**: {trade_count}

### Calculation Methods
- **Return**: (Final Value - Initial Capital) / Initial Capital × 100
- **Win Rate**: Number of Winning Trades / Total Trades × 100
- **Drawdown**: Maximum peak-to-trough decline in portfolio value
- **Sharpe Ratio**: Mean of Returns / Standard Deviation of Returns × √252 (annualized)

{equity_curve_note if has_equity_curve else ""}
"""
        return metrics_section
    except Exception as e:
        logger.error(f"Error generating metrics section: {str(e)}")
        return "## 8. Performance Metrics\n\nError generating metrics section"
