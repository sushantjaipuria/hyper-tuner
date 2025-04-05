import pandas as pd
import numpy as np
import backtrader as bt
import uuid
import logging
from datetime import datetime, timedelta
import tempfile
import os
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import base64
import io
from debug_utils import save_strategy_debug_info, save_strategy_comparison

from indicators import Indicators
from data_provider import DataProvider
from utils import safe_strftime, format_date_for_api, log_date_conversion
from logging_config import get_logger
from market_calendar import is_market_hours, next_valid_market_time, format_market_time, parse_market_time

class BacktestEngine:
    """Class to handle backtesting of trading strategies"""
    
    def __init__(self, data_provider):
        """
        Initialize the backtest engine with a data provider
        
        Args:
            data_provider (DataProvider): An instance of a class implementing the DataProvider interface
        """
        self.data_provider = data_provider
        self.logger = get_logger(__name__)
        self.logger.info("BacktestEngine initialized")
        self.indicators = Indicators()
        
        # For tracking Backtrader's interpretation of strategies
        self.backtrader_interpretation = {
            'strategy_params': {},
            'indicators': {},
            'data_feed': {},
            'conditions': {}
        }
    
    def _safe_to_list(self, value):
        """
        Safely convert a value to a list, handling different types appropriately.
        
        Args:
            value: The value to convert (numpy array, pandas Series, list, etc.)
            
        Returns:
            list: The value converted to a list
        """
        if value is None:
            return []
            
        # If it's already a list, return it directly
        if isinstance(value, list):
            return value
            
        # Check if it has a tolist method (numpy arrays, pandas Series)
        if hasattr(value, 'tolist'):
            return value.tolist()
            
        # Try to convert other iterables to a list
        try:
            return list(value)
        except:
            # If all else fails, return an empty list
            self.logger.warning(f"Could not convert {type(value)} to list, returning empty list")
            return []
        
    def run_backtest(self, strategy, start_date, end_date, initial_capital=100000):
        """
        Run a backtest for a strategy
        
        Args:
            strategy (dict): Strategy configuration
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            initial_capital (float): Initial capital for the backtest
            
        Returns:
            dict: Backtest results
        """
        try:
            # Add debug logging for dates and initial capital at the start
            self.logger.info(f"BACKTEST ENGINE START: Backtesting period from {start_date} to {end_date}")
            self.logger.info(f"BACKTEST ENGINE START: Using initial_capital={initial_capital} (type: {type(initial_capital).__name__})")
            
            # Reset backtrader interpretation for this run
            self.backtrader_interpretation = {
                'strategy_params': {},
                'indicators': {},
                'data_feed': {},
                'conditions': {}
            }
            
            # Get strategy details
            strategy_id = strategy['strategy_id']
            strategy_name = strategy['name']
            strategy_type = strategy['type']
            symbol = strategy['symbol']
            timeframe = strategy['timeframe']
            entry_conditions = strategy['entry_conditions']
            exit_conditions = strategy['exit_conditions']
            
            # Get stop loss and target profit if available
            stop_loss = strategy.get('stop_loss', 0)
            target_profit = strategy.get('target_profit', 0)
            
            # Get historical data
            self.logger.info(f"Getting historical data for {symbol} from {start_date} to {end_date} with timeframe {timeframe}")
            data = self.data_provider.get_historical_data(symbol, timeframe, start_date, end_date)
            
            # Validate the data
            if data.empty:
                self.logger.error(f"No historical data found for {symbol} from {start_date} to {end_date}")
                raise ValueError(f"No historical data found for {symbol} from {start_date} to {end_date}. Please check the symbol and date range.")
                
            # Log actual data range
            if not data.empty:
                data_start = data.index.min().strftime('%Y-%m-%d') if hasattr(data.index.min(), 'strftime') else str(data.index.min())
                data_end = data.index.max().strftime('%Y-%m-%d') if hasattr(data.index.max(), 'strftime') else str(data.index.max())
                self.logger.info(f"DATA RANGE: Retrieved {len(data)} data points from {data_start} to {data_end}")
                
            # Check if close column exists and has valid data
            if 'close' not in data.columns:
                self.logger.error(f"No 'close' price data found for {symbol}")
                raise ValueError(f"No 'close' price data found for {symbol}. This is required for backtesting.")
                
            if data['close'].isnull().all() or (data['close'] == 0).all():
                self.logger.error(f"Invalid 'close' price data for {symbol} - all values are null or zero")
                raise ValueError(f"Invalid 'close' price data for {symbol}. Please check the data source.")
                
            self.logger.info(f"Successfully retrieved data for {symbol} with {len(data)} data points")
                
            # Add indicators to data
            indicator_configs = []
            for condition in entry_conditions + exit_conditions:
                if 'indicator' in condition:
                    indicator_configs.append(condition)
            
            # Validate data structure before adding indicators
            self._validate_data_structure(data)
            
            self.logger.info(f"Adding {len(indicator_configs)} indicators to data")
            data_with_indicators = self.indicators.add_all_indicators(data, indicator_configs)
            
            # Track indicator processing for debugging
            indicator_processing = {}
            for condition in indicator_configs:
                if 'indicator' in condition and 'variable' in condition:
                    indicator = condition['indicator']
                    variable = condition['variable']
                    params = condition.get('params', {})
                    
                    # For debugging, get sanitized variable name that might have been used
                    safe_var_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in variable)
                    if not safe_var_name[0].isalpha() and safe_var_name[0] != '_':
                        safe_var_name = 'ind_' + safe_var_name
                    
                    # Check both variable names
                    if variable in data_with_indicators.columns:
                        actual_var = variable
                    elif safe_var_name in data_with_indicators.columns:
                        actual_var = safe_var_name
                    else:
                        actual_var = None
                    
                    indicator_processing[variable] = {
                        'indicator_type': indicator,
                        'parameters': params,
                        'column_name': variable,
                        'sanitized_name': safe_var_name,
                        'found_in_data': actual_var is not None,
                        'actual_column': actual_var,
                        'sample_values': data_with_indicators[actual_var].head(3).tolist() if actual_var is not None and not data_with_indicators.empty else []
                    }
            
            self.backtrader_interpretation['indicators'] = indicator_processing
            
            # Validate that all required indicators were added
            entry_indicator_vars = []
            for condition in entry_conditions:
                if 'variable' in condition:
                    entry_indicator_vars.append(condition['variable'])
            
            # Also check exit conditions for required indicators
            exit_indicator_vars = []
            for condition in exit_conditions:
                if 'variable' in condition:
                    exit_indicator_vars.append(condition['variable'])
                    
            # Combine all required indicator variables
            all_indicator_vars = entry_indicator_vars + exit_indicator_vars
            
            # Check if any of the required indicators are missing
            missing_indicators = []
            for var in all_indicator_vars:
                # Check direct match
                if var not in data_with_indicators.columns:
                    # Also check sanitized version
                    safe_var_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in var)
                    if not safe_var_name[0].isalpha() and safe_var_name[0] != '_':
                        safe_var_name = 'ind_' + safe_var_name
                        
                    # Still missing after sanitization?
                    if safe_var_name not in data_with_indicators.columns:
                        missing_indicators.append(var)
            
            if missing_indicators:
                self.logger.error(f"Missing required indicators in data: {missing_indicators}")
                self.logger.error(f"Available columns: {list(data_with_indicators.columns)}")
                raise ValueError(f"Failed to calculate required indicators: {', '.join(missing_indicators)}. Check your indicator parameters.")
                
            # Log all available indicators for debugging
            self.logger.info(f"All columns available for backtesting: {list(data_with_indicators.columns)}")
            self.logger.info(f"Required indicator variables: {all_indicator_vars}")
            self.logger.info(f"All validations passed, proceeding with creating strategy")
                
                
            self.logger.info(f"Successfully added indicators to data. Shape: {data_with_indicators.shape}")
            
            # Drop rows with NaN values that might have been introduced by indicators
            orig_len = len(data_with_indicators)
            data_with_indicators = data_with_indicators.dropna()
            if len(data_with_indicators) < orig_len:
                self.logger.warning(f"Dropped {orig_len - len(data_with_indicators)} rows with NaN values")
                
            if data_with_indicators.empty:
                self.logger.error("No valid data left after adding indicators and removing NaN values")
                raise ValueError("No valid data available for backtesting after adding indicators. Try a different date range or check indicator parameters.")
            
            
            # Create a Backtrader strategy class dynamically
            try:
                bt_strategy_class = self._create_bt_strategy_class(
                    strategy_type, 
                    entry_conditions, 
                    exit_conditions, 
                    stop_loss, 
                    target_profit
                )
                
                # We'll save debug information at the end after we have results
                
            except Exception as e:
                self.logger.error(f"Failed to create Backtrader strategy class: {str(e)}")
                raise ValueError(f"Failed to create strategy class: {str(e)}. Please check your strategy configuration.")
            
            # Set up Backtrader cerebro
            cerebro = bt.Cerebro()
            
            # Add strategy to cerebro
            cerebro.addstrategy(bt_strategy_class)
            
            # Add data to cerebro
            try:
                feed = self._create_bt_data_feed(data_with_indicators)
                cerebro.adddata(feed)
            except Exception as e:
                self.logger.error(f"Failed to create or add data feed: {str(e)}")
                raise ValueError(f"Failed to process data for backtesting: {str(e)}. Check data structure and indicators.")
            
            # Set initial cash
            cerebro.broker.setcash(initial_capital)
            
            # Add debug logging after setting initial cash
            self.logger.info(f"BACKTEST ENGINE CEREBRO: Set initial_capital={initial_capital}, Cerebro cash={cerebro.broker.getcash()}")
            
            # Set commission (0%)
            cerebro.broker.setcommission(commission=0)
            
            # Run backtest
            self.logger.info(f"Running backtest for strategy {strategy_name}...")
            results = cerebro.run()
            strat = results[0]
            
            # Get backtest results
            portfolio_value = cerebro.broker.getvalue()
            returns = (portfolio_value - initial_capital) / initial_capital * 100
            
            # Add debug logging with dates, initial capital and final value
            self.logger.info(f"BACKTEST ENGINE END: Completed backtest from {start_date} to {end_date}")
            self.logger.info(f"BACKTEST ENGINE END: Backtest completed with initial_capital={initial_capital}, final_value={portfolio_value}, returns={returns:.2f}%")
            
            # Add additional summary of data range used
            if not data.empty:
                data_start = data.index.min().strftime('%Y-%m-%d') if hasattr(data.index.min(), 'strftime') else str(data.index.min())
                data_end = data.index.max().strftime('%Y-%m-%d') if hasattr(data.index.max(), 'strftime') else str(data.index.max())
                self.logger.info(f"BACKTEST DATA SUMMARY: Data used for backtest spans from {data_start} to {data_end}")
                self.logger.info(f"BACKTEST DATA SUMMARY: Contains {len(data)} data points for symbol {symbol}")
            
            # Get all trades
            trades = []
            try:
                self.logger.info(f"Processing {len(strat.trades)} trade records")
                
                for i, trade in enumerate(strat.trades):
                    try:
                        # Handle trade data whether it's a dictionary or an object
                        if isinstance(trade, dict):
                            # For dictionary trades
                            self.logger.debug(f"Processing dictionary trade {i+1}: {trade}")
                            trade_data = {
                                'entry_date': self._format_datetime(trade.get('entry_date')),
                                'entry_price': trade.get('entry_price'),
                                'exit_date': self._format_datetime(trade.get('exit_date')),
                                'exit_price': trade.get('exit_price'),
                                'profit_points': trade.get('profit_points', 0),
                                'profit_pct': trade.get('profit_pct', 0),
                                'size': trade.get('size', 1)
                            }
                        else:
                            # For object trades (in case we change implementation later)
                            self.logger.debug(f"Processing object trade {i+1}: {type(trade)}")
                            trade_data = {
                                'entry_date': self._format_datetime(getattr(trade, 'entry_date', None)),
                                'entry_price': getattr(trade, 'entry_price', 0),
                                'exit_date': self._format_datetime(getattr(trade, 'exit_date', None)),
                                'exit_price': getattr(trade, 'exit_price', 0),
                                'profit_points': getattr(trade, 'profit_points', 0),
                                'profit_pct': getattr(trade, 'profit_pct', 0),
                                'size': getattr(trade, 'size', 1)
                            }
                            
                        trades.append(trade_data)
                        self.logger.debug(f"Successfully processed trade {i+1}")
                    except Exception as e:
                        self.logger.warning(f"Error processing trade {i+1}: {str(e)}")
                        # Create a minimal valid trade record to avoid breaking analysis
                        trades.append({
                            'entry_date': 'Unknown',
                            'entry_price': 0,
                            'exit_date': 'Unknown',
                            'exit_price': 0,
                            'profit_points': 0,
                            'profit_pct': 0,
                            'size': 1
                        })
            except Exception as e:
                self.logger.error(f"Error processing trades list: {str(e)}")
                # Create a minimal set of trades for results
                trades = []
            
            # Calculate additional metrics and prepare results
            try:
                winning_trades = [t for t in trades if t['profit_pct'] > 0]
                losing_trades = [t for t in trades if t['profit_pct'] <= 0]
                win_rate = len(winning_trades) / len(trades) if trades else 0
                
                # Get metrics from strategy instance
                equity_curve = getattr(strat, 'equity_curve', [])
                max_drawdown = getattr(strat, 'max_drawdown', 0)
                returns_series = getattr(strat, 'returns', [])
                sharpe_ratio = getattr(strat, 'sharpe_ratio', 0)
                
                # Add market hours information to trades for reporting
                for trade in trades:
                    try:
                        # Try to parse and validate entry date
                        if trade.get('entry_date'):
                            try:
                                entry_dt = parse_market_time(trade['entry_date'])
                                trade['entry_in_market_hours'] = is_market_hours(entry_dt)
                            except:
                                trade['entry_in_market_hours'] = False
                        
                        # Try to parse and validate exit date
                        if trade.get('exit_date'):
                            try:
                                exit_dt = parse_market_time(trade['exit_date'])
                                trade['exit_in_market_hours'] = is_market_hours(exit_dt)
                            except:
                                trade['exit_in_market_hours'] = False
                    except Exception as e:
                        self.logger.warning(f"Error validating trade timestamps: {str(e)}")
                
                # Count invalid timestamps in position tracking
                position_events_outside_hours = sum(1 for p in getattr(strat, 'position_tracking', []) if p.get('is_market_hours') is False)
                condition_evals_outside_hours = sum(1 for c in getattr(strat, 'condition_evaluations', []) if c.get('is_market_hours') is False)
                
                # Prepare results
                backtest_results = {
                'backtest_id': str(uuid.uuid4()),
                'strategy_id': strategy_id,
                'start_date': start_date,
                'end_date': end_date,
                'initial_capital': initial_capital,
                'final_value': portfolio_value,
                'returns': returns,
                'win_rate': win_rate,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'trade_count': len(trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'trades': trades,
                'equity_curve': self._safe_to_list(equity_curve),
                'returns_series': self._safe_to_list(returns_series),
                'condition_evaluations': getattr(strat, 'condition_evaluations', []),
                'position_tracking': getattr(strat, 'position_tracking', []),
                'market_hours_validation': {
                    'enabled': True,
                    'market_hours': '9:15 AM - 3:15 PM IST (Monday-Friday)',
                    'position_events_outside_hours': position_events_outside_hours,
                    'condition_evaluations_outside_hours': condition_evals_outside_hours,
                },
                'summary': {
                    'returns': returns,
                    'win_rate': win_rate,
                    'max_drawdown': max_drawdown,
                    'sharpe_ratio': sharpe_ratio,
                    'trade_count': len(trades)
                }
            }
                
                self.logger.info(f"Backtest completed: Returns: {returns:.2f}%, Win Rate: {win_rate:.2f}, Sharpe: {sharpe_ratio:.2f}")
                
                # Now save strategy comparison with the results
                self.logger.info("Saving strategy comparison...")
                debug_file = save_strategy_comparison(
                    strategy, 
                    bt_strategy_class, 
                    self.backtrader_interpretation,
                    self.logger, 
                    backtest_results
                )
                self.logger.info(f"Strategy comparison saved to {debug_file}")
                
                return backtest_results
            except Exception as e:
                self.logger.error(f"Error preparing backtest results: {str(e)}")
                # Return minimal valid backtest results
                minimal_results = {
                    'backtest_id': str(uuid.uuid4()),
                    'strategy_id': strategy_id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'initial_capital': initial_capital,
                    'final_value': portfolio_value,
                    'returns': returns,
                    'win_rate': 0,
                    'max_drawdown': 0,
                    'sharpe_ratio': 0,
                    'trade_count': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'trades': [],
                    'equity_curve': [],
                    'returns_series': [],
                    'summary': {
                        'returns': returns,
                        'win_rate': 0,
                        'max_drawdown': 0,
                        'sharpe_ratio': 0,
                        'trade_count': 0
                    }
                }
                return minimal_results
        
        except Exception as e:
            self.logger.error(f"Error running backtest: {str(e)}")
            raise
    
    def _format_datetime(self, dt_value):
        """
        Format a datetime value to string, handling various input types
        Preserves timezone information when available
        Ensures timestamps conform to market hours
        
        Args:
            dt_value: Can be datetime object, string, or None
            
        Returns:
            str or None: Formatted datetime string or None
        """
        if dt_value is None:
            return None
            
        try:
            # If it's already a string, use our market_calendar parse function
            if isinstance(dt_value, str):
                try:
                    # Parse the string into a datetime object
                    parsed_dt = parse_market_time(dt_value)
                    # Format using our market_calendar utility
                    return format_market_time(parsed_dt)
                except Exception as e:
                    self.logger.warning(f"Error parsing datetime string {dt_value}: {str(e)}")
                    # Return original string with IST if it doesn't have timezone
                    has_tz_info = '+05:30' in dt_value or ' IST' in dt_value
                    if not has_tz_info and ' ' in dt_value and len(dt_value) >= 16:
                        return dt_value + ' IST'
                    return dt_value
                
            # If it's a datetime object, format it using our market_calendar utility
            if isinstance(dt_value, datetime):
                return format_market_time(dt_value)
                
            # Try to convert other types to string with logging
            result = str(dt_value)
            # Check if the result appears to be a datetime but doesn't have timezone
            if ' ' in result and len(result) >= 16 and not ('+05:30' in result or ' IST' in result):
                # Try to append timezone for consistency
                result = result + ' IST'
                
            return log_date_conversion(
                dt_value,
                result,
                f"conversion of {type(dt_value).__name__} to string with timezone handling",
                extra_info={"context": "backtest_engine_format_datetime"}
            )
        except Exception as e:
            self.logger.warning(f"Error formatting datetime: {str(e)}")
            result = str(dt_value) if dt_value is not None else None
            return log_date_conversion(
                dt_value,
                result,
                "fallback string conversion after error",
                extra_info={"error": str(e), "context": "backtest_engine_format_datetime"}
            )
    
    def _create_bt_strategy_class(self, strategy_type, entry_conditions, exit_conditions, stop_loss=0, target_profit=0):
        """
        Create a Backtrader strategy class dynamically
        
        Args:
            strategy_type (str): Strategy type (buy or sell)
            entry_conditions (list): List of entry conditions
            exit_conditions (list): List of exit conditions
            stop_loss (float): Stop loss percentage
            target_profit (float): Target profit percentage
            
        Returns:
            backtrader.Strategy: Backtrader strategy class
        """
        # Store the strategy parameters for debug purposes
        strategy_params = {
            'strategy_type': strategy_type,
            'entry_conditions': entry_conditions,
            'exit_conditions': exit_conditions,
            'stop_loss': stop_loss,
            'target_profit': target_profit
        }
        
        # Track how Backtrader interprets the strategy
        self.backtrader_interpretation['strategy_params'] = strategy_params
        
        # Track how entry and exit conditions are interpreted
        entry_interpretation = []
        for condition in entry_conditions:
            if 'indicator' in condition:
                if 'variable' in condition:
                    # This is an indicator initialization
                    entry_interpretation.append({
                        'type': 'indicator_setup',
                        'indicator': condition.get('indicator'),
                        'variable': condition.get('variable'),
                        'params': condition.get('params', {})
                    })
            elif 'comparison' in condition or 'condition' in condition:
                # This is a comparison condition
                entry_interpretation.append({
                    'type': 'comparison',
                    'variable': condition.get('variable', ''),
                    'comparison': condition.get('comparison', condition.get('condition', '')),
                    'threshold': condition.get('threshold', 0),
                    'action': condition.get('action', '')
                })
        
        exit_interpretation = []
        for condition in exit_conditions:
            if 'indicator' in condition:
                if 'variable' in condition:
                    # This is an indicator initialization
                    exit_interpretation.append({
                        'type': 'indicator_setup',
                        'indicator': condition.get('indicator'),
                        'variable': condition.get('variable'),
                        'params': condition.get('params', {})
                    })
            elif 'comparison' in condition or 'condition' in condition:
                # This is a comparison condition
                exit_interpretation.append({
                    'type': 'comparison',
                    'variable': condition.get('variable', ''),
                    'comparison': condition.get('comparison', condition.get('condition', '')),
                    'threshold': condition.get('threshold', 0),
                    'action': condition.get('action', '')
                })
        
        self.backtrader_interpretation['conditions'] = {
            'entry_interpretation': entry_interpretation,
            'exit_interpretation': exit_interpretation,
            'backtrader_translation': {
                'strategy_type': 'BUY' if strategy_type == 'buy' else 'SELL',
                'stop_loss_handling': f"{stop_loss}% stop loss will trigger exit" if stop_loss > 0 else "No stop loss",
                'take_profit_handling': f"{target_profit}% profit target will trigger exit" if target_profit > 0 else "No take profit"
            }
        }
        # Define a custom strategy class
        class CustomStrategy(bt.Strategy):
            def __init__(self):
                self.order = None
                self.buyprice = None
                self.buycomm = None
                self.trades = []
                self.equity_curve = []
                self.returns = []
                self.max_drawdown = 0
                self.sharpe_ratio = 0
                
                # Add position tracking to fix the 'barlen' issue
                self.position_entry_bar = None  # Store the bar when a position is entered
                
                # Add condition tracking and position tracking storage
                self.condition_evaluations = []
                self.position_tracking = []
                
                # Parse entry conditions
                self.entry_conditions = entry_conditions
                
                # Parse exit conditions
                self.exit_conditions = exit_conditions
                
                # Set stop loss and target profit
                self.stop_loss = stop_loss
                self.target_profit = target_profit
                
                # Log available data feed lines for debugging
                self.log("Available data feed lines:")
                for i, data in enumerate(self.datas):
                    self.log(f"Data feed {i} lines: {', '.join([l for l in dir(data.lines) if not l.startswith('_')])}")
                
                # Log strategy conditions for debugging
                self.log(f"Entry conditions: {self.entry_conditions}")
                
                # Initialize variables
                for condition in self.entry_conditions + self.exit_conditions:
                    if 'variable' in condition:
                        var_name = condition['variable']
                        # Ensure variable name is a valid Python identifier
                        if not var_name.isidentifier():
                            self.log(f"Warning: Variable name '{var_name}' is not a valid Python identifier. Skipping.")
                            continue
                        try:
                            setattr(self, var_name, None)
                            self.log(f"Initialized variable: {var_name}")
                        except Exception as e:
                            self.log(f"Error setting attribute for variable '{var_name}': {str(e)}")
                            
                # Check for each variable if it exists as a line in the data feed
                for condition in self.entry_conditions + self.exit_conditions:
                    if 'variable' in condition:
                        var_name = condition['variable']
                        # Also check the sanitized name
                        safe_var_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in var_name)
                        if not safe_var_name[0].isalpha() and safe_var_name[0] != '_':
                            safe_var_name = 'ind_' + safe_var_name
                            
                        has_line = hasattr(self.datas[0].lines, var_name)
                        has_safe_line = hasattr(self.datas[0].lines, safe_var_name)
                        
                        self.log(f"Variable {var_name} as line: {has_line}, as safe line {safe_var_name}: {has_safe_line}")
                        
                        if not has_line and not has_safe_line:
                            self.log(f"WARNING: Variable {var_name} is not available as a line in the data feed")
                            self.log(f"This may cause the strategy to fail when evaluating conditions")
                            self.log(f"Please check indicator configuration and variable naming")
                            
                # Log completed initialization
                self.log("Strategy initialization complete")
                
                # Additional setup for debug purposes
                # Store the starting time of the strategy
                self.start_date = self.datas[0].datetime.datetime(0)
                self.log(f"Starting strategy at: {self.start_date}")
                
                # Debug: check if first few bars have indicator values
                for i in range(min(3, len(self.datas[0]))):
                    self.log(f"Bar {i} values:")
                    for line_name in [l for l in dir(self.datas[0].lines) if not l.startswith('_')]:
                        line = getattr(self.datas[0].lines, line_name)
                        try:
                            self.log(f"  {line_name}: {line[i]}")
                        except:
                            self.log(f"  {line_name}: Error accessing value")
                    self.log("---")
                    
                self.log("Strategy ready")
                
            
            def _format_date(self, dt_value):
                """Format a datetime value to string, preserving timezone and validating market hours"""
                if dt_value is None:
                    return None
                    
                try:
                    # Leverage our market_calendar utility for consistent formatting
                    if isinstance(dt_value, datetime):
                        return format_market_time(dt_value)
                    
                    # If not a datetime object, convert to string and try to parse
                    result = str(dt_value)
                    try:
                        parsed_dt = parse_market_time(result)
                        return format_market_time(parsed_dt)
                    except:
                        # If parsing fails, just ensure it has IST timezone
                        if ' ' in result and len(result) >= 16 and not ('+05:30' in result or ' IST' in result):
                            result = result + ' IST'
                        return result
                except Exception as e:
                    self.log(f"Error formatting datetime: {str(e)}")
                    return str(dt_value) if dt_value is not None else None
            
            def log(self, txt, dt=None):
                """Logging function"""
                dt = dt or self.datas[0].datetime.date(0)
                print(f"{dt.isoformat()}: {txt}")
            
            def notify_order(self, order):
                """Handle order notifications, ensuring trades have valid market hour timestamps"""
                if order.status in [order.Submitted, order.Accepted]:
                    # Order has been submitted/accepted - nothing to do
                    return
                
                # Check if an order has been completed
                if order.status in [order.Completed]:
                    if order.isbuy():
                        self.log(f"BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")
                        self.buyprice = order.executed.price
                        self.buycomm = order.executed.comm
                        
                        # Get raw timestamp and validate against market hours
                        timestamp_raw = self.datas[0].datetime.datetime(0)
                        
                        # If outside market hours, adjust to next valid market time
                        if not is_market_hours(timestamp_raw):
                            original_timestamp = timestamp_raw
                            timestamp_raw = next_valid_market_time(timestamp_raw)
                            self.log(f"Adjusted entry timestamp from {format_market_time(original_timestamp)} to {format_market_time(timestamp_raw)} (market hours validation)")
                        
                        timestamp_str = self._format_date(timestamp_raw)
                        
                        # Create a new trade record
                        self.current_trade = {
                            'entry_date': timestamp_str,
                            'entry_price': order.executed.price,
                            'exit_date': None,
                            'exit_price': None,
                            'profit_points': 0,
                            'profit_pct': 0,
                            'size': order.executed.size
                        }
                        
                        # Store the current bar index for position tracking
                        self.position_entry_bar = len(self.datas[0])
                        
                        # Track position entry with validated timestamp
                        self.position_tracking.append({
                            'action': 'ENTRY',
                            'timestamp': timestamp_str,
                            'original_timestamp': self._format_date(self.datas[0].datetime.datetime(0)),
                            'price': order.executed.price,
                            'size': order.executed.size,
                            'bar_index': len(self.datas[0]),
                            'reason': 'Entry conditions met',
                            'portfolio_value': self.broker.getvalue(),
                            'is_market_hours': is_market_hours(timestamp_raw)
                        })
                    
                    elif order.issell():
                        self.log(f"SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")
                        
                        # Get raw timestamp and validate against market hours
                        timestamp_raw = self.datas[0].datetime.datetime(0)
                        
                        # If outside market hours, adjust to next valid market time
                        if not is_market_hours(timestamp_raw):
                            original_timestamp = timestamp_raw
                            timestamp_raw = next_valid_market_time(timestamp_raw)
                            self.log(f"Adjusted exit timestamp from {format_market_time(original_timestamp)} to {format_market_time(timestamp_raw)} (market hours validation)")
                        
                        timestamp_str = self._format_date(timestamp_raw)
                        
                        # Update the current trade record
                        self.current_trade['exit_date'] = timestamp_str
                        self.current_trade['exit_price'] = order.executed.price
                        
                        # Calculate profit in points and percent
                        if strategy_type == 'buy':
                            self.current_trade['profit_points'] = order.executed.price - self.buyprice
                            self.current_trade['profit_pct'] = (order.executed.price / self.buyprice - 1) * 100
                        else:  # sell strategy
                            self.current_trade['profit_points'] = self.buyprice - order.executed.price
                            self.current_trade['profit_pct'] = (self.buyprice / order.executed.price - 1) * 100
                        
                        # Determine exit reason
                        exit_reason = 'Exit conditions met'
                        
                        # Check if exit was due to stop loss or take profit
                        if hasattr(self, 'buyprice') and self.buyprice:
                            price = order.executed.price
                            if strategy_type == 'buy':
                                profit_pct = (price / self.buyprice - 1) * 100
                                loss_pct = (1 - price / self.buyprice) * 100
                            else:  # sell strategy
                                profit_pct = (1 - price / self.buyprice) * 100
                                loss_pct = (price / self.buyprice - 1) * 100
                            
                            if self.target_profit > 0 and profit_pct >= self.target_profit:
                                exit_reason = f'Take profit triggered ({profit_pct:.2f}%)'
                            elif self.stop_loss > 0 and loss_pct >= self.stop_loss:
                                exit_reason = f'Stop loss triggered ({loss_pct:.2f}%)'
                        
                        # Track position exit with validated timestamp
                        self.position_tracking.append({
                            'action': 'EXIT',
                            'timestamp': timestamp_str,
                            'original_timestamp': self._format_date(self.datas[0].datetime.datetime(0)),
                            'price': order.executed.price,
                            'size': order.executed.size,
                            'bar_index': len(self.datas[0]),
                            'reason': exit_reason,
                            'portfolio_value': self.broker.getvalue(),
                            'profit_pct': self.current_trade['profit_pct'],
                            'is_market_hours': is_market_hours(timestamp_raw)
                        })
                        
                        # Add the completed trade to the trades list
                        self.trades.append(self.current_trade)
                        self.current_trade = None
                        
                        # Reset position tracking when position is closed via sell order
                        self.position_entry_bar = None
                    
                    self.order = None
                
                elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                    self.log('Order Canceled/Margin/Rejected')
                    self.order = None
            
            def notify_trade(self, trade):
                """Handle trade notifications"""
                if not trade.isclosed:
                    return
                
                self.log(f"OPERATION PROFIT, GROSS: {trade.pnl:.2f}, NET: {trade.pnlcomm:.2f}")
            
            def next(self):
                """Define what to do for each bar"""
                # Skip if an order is pending
                if self.order:
                    return
                
                # Update equity curve
                self.equity_curve.append(self.broker.getvalue())
                
                # Calculate returns
                if len(self.equity_curve) > 1:
                    daily_return = (self.equity_curve[-1] / self.equity_curve[-2]) - 1
                    self.returns.append(daily_return)
                else:
                    self.returns.append(0)
                
                # Update max drawdown
                if len(self.equity_curve) > 1:
                    # Calculate drawdown
                    peak = max(self.equity_curve)
                    drawdown = (peak - self.equity_curve[-1]) / peak * 100
                    self.max_drawdown = max(self.max_drawdown, drawdown)
                
                # Calculate Sharpe ratio
                if len(self.returns) > 1:
                    try:
                        returns_array = np.array(self.returns)
                        # Avoid division by zero or NaN values
                        std_dev = np.std(returns_array)
                        if std_dev > 0 and not np.isnan(std_dev):
                            self.sharpe_ratio = np.mean(returns_array) / std_dev * np.sqrt(252)
                        else:
                            self.sharpe_ratio = 0
                            print(f"{self.datas[0].datetime.date(0).isoformat()}: Warning: Standard deviation of returns is zero or NaN, setting Sharpe ratio to 0")
                    except Exception as e:
                        self.sharpe_ratio = 0
                        print(f"{self.datas[0].datetime.date(0).isoformat()}: Error calculating Sharpe ratio: {str(e)}. Setting to 0.")
                
                # Check entry conditions if not in position
                if not self.position:
                    # Evaluate entry conditions
                    enter_trade = self._evaluate_entry_conditions()
                    
                    if enter_trade:
                        # Calculate position size (1 quantity for simplicity)
                        size = 1
                        
                        # Enter position
                        if strategy_type == 'buy':
                            self.log(f"BUY CREATE, {size} @ {self.datas[0].close[0]:.2f}")
                            self.order = self.buy(size=size)
                        else:  # sell strategy
                            self.log(f"SELL CREATE, {size} @ {self.datas[0].close[0]:.2f}")
                            self.order = self.sell(size=size)
                            
                        # Note: position_entry_bar will be set in notify_order when the order is executed
                
                # Check exit conditions if in position
                else:
                    # Check stop loss and target profit first
                    price = self.datas[0].close[0]
                    entry_price = self.buyprice
                    
                    if entry_price is not None:
                        if strategy_type == 'buy':
                            # For buy strategy
                            profit_pct = (price / entry_price - 1) * 100
                            loss_pct = (1 - price / entry_price) * 100
                        else:
                            # For sell strategy
                            profit_pct = (1 - price / entry_price) * 100
                            loss_pct = (price / entry_price - 1) * 100
                        
                        # Check if we hit target profit
                        if self.target_profit > 0 and profit_pct >= self.target_profit:
                            self.log(f"TARGET PROFIT REACHED: {profit_pct:.2f}%")
                            exit_trade = True
                        
                        # Check if we hit stop loss
                        elif self.stop_loss > 0 and loss_pct >= self.stop_loss:
                            self.log(f"STOP LOSS TRIGGERED: {loss_pct:.2f}%")
                            exit_trade = True
                        
                        # Otherwise, evaluate other exit conditions
                        else:
                            exit_trade = self._evaluate_exit_conditions()
                    else:
                        # If entry price is None, evaluate other exit conditions
                        exit_trade = self._evaluate_exit_conditions()
                    
                    if exit_trade:
                        # Exit position
                        if strategy_type == 'buy':
                            self.log(f"SELL CREATE, {self.position.size} @ {self.datas[0].close[0]:.2f}")
                            self.order = self.sell(size=self.position.size)
                        else:  # sell strategy
                            self.log(f"BUY CREATE, {abs(self.position.size)} @ {self.datas[0].close[0]:.2f}")
                            self.order = self.buy(size=abs(self.position.size))
            
            def _evaluate_entry_conditions(self):
                """Evaluate entry conditions"""
                # Get the current bar
                current_bar = len(self.datas[0])
                
                # Need a minimum number of bars for indicators to work
                if current_bar < 30:  # Arbitrary threshold to ensure indicators have enough data
                    return False
                
                # Get raw timestamp and check market hours
                timestamp_raw = self.datas[0].datetime.datetime(0)
                is_within_market = is_market_hours(timestamp_raw)
                
                # If outside market hours, record the original but use next valid time for display
                if not is_within_market:
                    original_timestamp = timestamp_raw
                    adjusted_timestamp = next_valid_market_time(timestamp_raw)
                    timestamp_str = self._format_date(adjusted_timestamp)
                    self.log(f"Condition evaluated outside market hours: {format_market_time(original_timestamp)} → {format_market_time(adjusted_timestamp)}")
                else:
                    timestamp_str = self._format_date(timestamp_raw)
                
                # Add tracking for this evaluation
                bar_tracking = {
                    'timestamp': timestamp_str,
                    'original_timestamp': self._format_date(timestamp_raw),
                    'bar_number': current_bar,
                    'is_market_hours': is_within_market,
                    'conditions': []
                }
                
                # Track if any condition evaluates to True
                enter_trade = False
                
                # Parse and evaluate conditions
                for condition in self.entry_conditions:
                    # Skip indicator definitions (these are just for adding indicators)
                    if 'indicator' in condition and 'comparison' not in condition:
                        continue
                        
                    # If it's a comparison condition
                    if 'comparison' in condition:
                        # Get the variable to compare
                        if 'variable' in condition:
                            var_name = condition['variable']
                            
                            # Sanitize variable name to match line name formatting in data feed
                            safe_var_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in var_name)
                            if not safe_var_name[0].isalpha() and safe_var_name[0] != '_':
                                safe_var_name = 'ind_' + safe_var_name
                            
                            # Check if the variable is defined as a line in the data feed
                            # First try exact name, then sanitized name
                            line_exists = False
                            if hasattr(self.datas[0].lines, var_name):
                                line_exists = True
                                line_name = var_name
                            elif hasattr(self.datas[0].lines, safe_var_name):
                                line_exists = True
                                line_name = safe_var_name
                                
                            if line_exists:
                                # Log that we found the indicator line
                                self.log(f"Found indicator line for {var_name} as {line_name}")
                                
                                # Get the current value of the variable
                                var_value = getattr(self.datas[0].lines, line_name)[0]
                                
                                # Get the threshold to compare against
                                threshold = condition.get('threshold', 0)
                                
                                # Get the comparison operator
                                comparison = condition.get('comparison', '>')
                                
                                # Log the comparison we're about to make
                                self.log(f"Evaluating condition: {line_name} {comparison} {threshold} (current value: {var_value})")
                                
                                # Evaluate the condition
                                condition_result = False
                                if comparison == '>':
                                    condition_result = var_value > threshold
                                    if condition_result:
                                        enter_trade = True
                                elif comparison == '>=':
                                    condition_result = var_value >= threshold
                                    if condition_result:
                                        enter_trade = True
                                elif comparison == '<':
                                    condition_result = var_value < threshold
                                    if condition_result:
                                        enter_trade = True
                                elif comparison == '<=':
                                    condition_result = var_value <= threshold
                                    if condition_result:
                                        enter_trade = True
                                elif comparison == '==':
                                    condition_result = var_value == threshold
                                    if condition_result:
                                        enter_trade = True
                                elif comparison == '!=':
                                    condition_result = var_value != threshold
                                    if condition_result:
                                        enter_trade = True
                                
                                # Track this condition evaluation
                                try:
                                    bar_tracking['conditions'].append({
                                        'type': 'entry',
                                        'variable': var_name,
                                        'value': float(var_value) if not np.isnan(var_value) else None,
                                        'comparison': comparison,
                                        'threshold': threshold,
                                        'result': condition_result
                                    })
                                except Exception as e:
                                    self.log(f"Error tracking condition: {str(e)}")
                            else:
                                # Log that we couldn't find the indicator line
                                self.log(f"Warning: Indicator line '{var_name}' not found in data feed")
                                # List available lines for debugging
                                available_lines = dir(self.datas[0].lines)
                                self.log(f"Available lines: {', '.join([l for l in available_lines if not l.startswith('_')])}")
                                
                                # Track the failed condition lookup
                                bar_tracking['conditions'].append({
                                    'type': 'entry',
                                    'variable': var_name,
                                    'value': None,
                                    'comparison': condition.get('comparison', '>'),
                                    'threshold': condition.get('threshold', 0),
                                    'result': False,
                                    'error': f"Variable not found in data feed"
                                })
                
                # Add the entry evaluation to tracked history
                self.condition_evaluations.append(bar_tracking)
                
                # Return the result
                return enter_trade
            
            def _evaluate_exit_conditions(self):
                """Evaluate exit conditions"""
                # Check how long we've been in position
                bars_in_position = 0
                current_bar = len(self.datas[0])
                
                if self.position_entry_bar is not None:
                    bars_in_position = current_bar - self.position_entry_bar
                    self.log(f"Position tracking: Current bar: {current_bar}, Entry bar: {self.position_entry_bar}, Bars in position: {bars_in_position}")
                else:
                    self.log(f"Position tracking: Entry bar not set, using default 0 bars in position")
                
                # Get raw timestamp and check market hours
                timestamp_raw = self.datas[0].datetime.datetime(0)
                is_within_market = is_market_hours(timestamp_raw)
                
                # If outside market hours, record the original but use next valid time for display
                if not is_within_market:
                    original_timestamp = timestamp_raw
                    adjusted_timestamp = next_valid_market_time(timestamp_raw)
                    timestamp_str = self._format_date(adjusted_timestamp)
                    self.log(f"Exit condition evaluated outside market hours: {format_market_time(original_timestamp)} → {format_market_time(adjusted_timestamp)}")
                else:
                    timestamp_str = self._format_date(timestamp_raw)
                
                # Add tracking for this evaluation
                bar_tracking = {
                    'timestamp': timestamp_str,
                    'original_timestamp': self._format_date(timestamp_raw),
                    'bar_number': current_bar,
                    'bars_in_position': bars_in_position,
                    'is_market_hours': is_within_market,
                    'conditions': []
                }
                
                # Track if any condition evaluates to True
                exit_trade = False
                exit_reason = None
                
                # Parse and evaluate conditions
                for condition in self.exit_conditions:
                    # Skip indicator definitions (these are just for adding indicators)
                    if 'indicator' in condition and 'comparison' not in condition:
                        continue
                        
                    # If it's a comparison condition
                    if 'comparison' in condition:
                        # Get the variable to compare
                        if 'variable' in condition:
                            var_name = condition['variable']
                            
                            # Sanitize variable name to match line name formatting in data feed
                            safe_var_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in var_name)
                            if not safe_var_name[0].isalpha() and safe_var_name[0] != '_':
                                safe_var_name = 'ind_' + safe_var_name
                            
                            # Check if the variable is defined as a line in the data feed
                            # First try exact name, then sanitized name
                            line_exists = False
                            if hasattr(self.datas[0].lines, var_name):
                                line_exists = True
                                line_name = var_name
                            elif hasattr(self.datas[0].lines, safe_var_name):
                                line_exists = True
                                line_name = safe_var_name
                                
                            if line_exists:
                                # Log that we found the indicator line
                                self.log(f"Found indicator line for {var_name} as {line_name}")
                                
                                # Get the current value of the variable
                                var_value = getattr(self.datas[0].lines, line_name)[0]
                                
                                # Get the threshold to compare against
                                threshold = condition.get('threshold', 0)
                                
                                # Get the comparison operator
                                comparison = condition.get('comparison', '>')
                                
                                # Log the comparison we're about to make
                                self.log(f"Evaluating exit condition: {line_name} {comparison} {threshold} (current value: {var_value})")
                                
                                # Evaluate the condition
                                condition_result = False
                                if comparison == '>':
                                    condition_result = var_value > threshold
                                    if condition_result:
                                        exit_trade = True
                                elif comparison == '>=':
                                    condition_result = var_value >= threshold
                                    if condition_result:
                                        exit_trade = True
                                elif comparison == '<':
                                    condition_result = var_value < threshold
                                    if condition_result:
                                        exit_trade = True
                                elif comparison == '<=':
                                    condition_result = var_value <= threshold
                                    if condition_result:
                                        exit_trade = True
                                elif comparison == '==':
                                    condition_result = var_value == threshold
                                    if condition_result:
                                        exit_trade = True
                                elif comparison == '!=':
                                    condition_result = var_value != threshold
                                    if condition_result:
                                        exit_trade = True
                                
                                # Track this condition evaluation
                                try:
                                    bar_tracking['conditions'].append({
                                        'type': 'exit',
                                        'variable': var_name,
                                        'value': float(var_value) if not np.isnan(var_value) else None,
                                        'comparison': comparison,
                                        'threshold': threshold,
                                        'result': condition_result
                                    })
                                    
                                    if condition_result:
                                        exit_reason = f"Exit condition met: {var_name} {comparison} {threshold}"
                                except Exception as e:
                                    self.log(f"Error tracking condition: {str(e)}")
                            else:
                                # Log that we couldn't find the indicator line
                                self.log(f"Warning: Indicator line '{var_name}' not found in data feed")
                                # List available lines for debugging
                                available_lines = dir(self.datas[0].lines)
                                self.log(f"Available lines: {', '.join([l for l in available_lines if not l.startswith('_')])}")
                                
                                # Track the failed condition lookup
                                bar_tracking['conditions'].append({
                                    'type': 'exit',
                                    'variable': var_name,
                                    'value': None,
                                    'comparison': condition.get('comparison', '>'),
                                    'threshold': condition.get('threshold', 0),
                                    'result': False,
                                    'error': f"Variable not found in data feed"
                                })
                
                # If no conditions triggered, check if we've been in position too long
                # as a failsafe - exit after 20 days in position if no other exit triggered
                if bars_in_position > 20 and not exit_trade:
                    exit_trade = True
                    exit_reason = f"Exit triggered by position duration: {bars_in_position} bars exceeds 20 bar limit"
                    self.log(exit_reason)
                    
                    bar_tracking['conditions'].append({
                        'type': 'exit',
                        'variable': 'bars_in_position',
                        'value': bars_in_position,
                        'comparison': '>',
                        'threshold': 20,
                        'result': True
                    })
                
                # Add the exit evaluation to tracked history
                self.condition_evaluations.append(bar_tracking)
                
                # Return the result
                return exit_trade
        
        return CustomStrategy
    
    def _validate_data_structure(self, data):
        """
        Validate the structure of the DataFrame to ensure it's suitable for backtesting
        
        Args:
            data (pandas.DataFrame): DataFrame to validate
        """
        # Check for tuple column names and convert to strings if necessary
        if any(isinstance(col, tuple) for col in data.columns):
            self.logger.warning("DataFrame contains tuple column names. Converting to strings.")
            data.columns = [str(col) if isinstance(col, tuple) else col for col in data.columns]
        
        # Check for any other problematic column types
        non_str_cols = [col for col in data.columns if not isinstance(col, str)]
        if non_str_cols:
            self.logger.warning(f"DataFrame contains non-string column names: {non_str_cols}. Converting to strings.")
            data.columns = [str(col) for col in data.columns]
        
        # Ensure required columns exist
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            self.logger.error(f"DataFrame missing required columns: {missing_columns}")
            raise ValueError(f"Data missing required columns: {', '.join(missing_columns)}")
            
        # Check for NaN or infinite values in the 'close' column
        if data['close'].isna().any() or np.isinf(data['close']).any():
            self.logger.warning("'close' column contains NaN or infinite values. Cleaning data...")
            data['close'] = data['close'].replace([np.inf, -np.inf], np.nan).fillna(method='ffill').fillna(method='bfill')
        
        return data
    
    def _create_bt_data_feed(self, data):
        """
        Create a Backtrader data feed from a Pandas DataFrame
        
        Args:
            data (pandas.DataFrame): DataFrame with OHLCV data
            
        Returns:
            backtrader.feeds.PandasData: Backtrader data feed
        """
        # Save data to temporary file for Backtrader
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            data.to_csv(tmp.name)
            tmp_path = tmp.name
        
        # Ensure all column names are strings
        data.columns = [str(col) for col in data.columns]
        
        # Collect indicator columns (non-OHLC columns)
        indicator_columns = []
        data_feed_indicators = {}
        
        for column in data.columns:
            # Skip standard OHLCV columns 
            if column not in ['open', 'high', 'low', 'close', 'volume']:
                # Ensure column name is a valid Python identifier
                col_name = str(column)
                # Replace any invalid characters with underscore
                col_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in col_name)
                # Ensure it starts with a letter or underscore
                if not col_name[0].isalpha() and col_name[0] != '_':
                    col_name = 'ind_' + col_name
                
                self.logger.debug(f"Adding indicator column: {column} as {col_name}")
                indicator_columns.append((col_name, column))
                
                # Track for debugging
                data_feed_indicators[column] = {
                    'backtrader_name': col_name,
                    'sample_values': data[column].head(3).tolist() if not data.empty else []
                }
        
        # Store data feed configuration for debugging
        self.backtrader_interpretation['data_feed'] = {
            'columns': list(data.columns),
            'indicator_mappings': dict(indicator_columns),
            'indicator_samples': data_feed_indicators
        }
        
        self.logger.info(f"Identified {len(indicator_columns)} indicator columns to add to data feed")
        if indicator_columns:
            self.logger.debug(f"Indicator mappings: {dict(indicator_columns)}")
        
        # Create a class that properly inherits from PandasData and defines lines correctly
        # This is the key fix: properly setting up line definitions for backtrader
        lines = tuple(col_name for col_name, _ in indicator_columns)
        params = (
            ('datetime', None),
            ('open', 'open'),
            ('high', 'high'),
            ('low', 'low'),
            ('close', 'close'),
            ('volume', 'volume'),
            ('openinterest', None),
        ) + tuple((col_name, col_orig) for col_name, col_orig in indicator_columns)
        
        # Create the CustomPandasData class with proper lines
        CustomPandasData = type(
            'CustomPandasData', 
            (bt.feeds.PandasData,), 
            {
                'lines': lines,
                'params': params
            }
        )
        
        # Log the created data feed class structure
        self.logger.info(f"Created CustomPandasData with {len(lines)} additional lines")
        self.logger.debug(f"Lines: {lines}")
        self.logger.debug(f"Params: {params}")
        
        # Create the data feed instance
        feed = CustomPandasData(dataname=data)
        
        # Clean up temporary file
        os.unlink(tmp_path)
        
        return feed

# Example usage:
if __name__ == "__main__":
    from data_provider_factory import provider_factory
    
    # Initialize components
    data_provider = provider_factory.get_provider()
    backtest_engine = BacktestEngine(data_provider)
    
    # Create a sample strategy
    strategy = {
        'strategy_id': '123',
        'name': 'EMA Crossover',
        'type': 'buy',
        'symbol': 'NIFTY 50',
        'timeframe': '1hour',
        'entry_conditions': [
            {
                'indicator': 'EMA',
                'params': {'period': 12},
                'variable': 'ema_short'
            },
            {
                'indicator': 'EMA',
                'params': {'period': 26},
                'variable': 'ema_long'
            },
            {
                'condition': 'ema_short > ema_long',
                'action': 'buy'
            }
        ],
        'exit_conditions': [
            {
                'condition': 'profit >= 3%',
                'action': 'exit'
            },
            {
                'condition': 'loss >= 1%',
                'action': 'exit'
            }
        ]
    }
    
    # Run backtest
    # results = backtest_engine.run_backtest(strategy, '2021-01-01', '2021-12-31')
    # print(results)
