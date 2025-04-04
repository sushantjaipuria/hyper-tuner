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

from indicators import Indicators
from data_provider import DataProvider
from utils import safe_strftime, format_date_for_api, log_date_conversion
from logging_config import get_logger

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
                'summary': {
                    'returns': returns,
                    'win_rate': win_rate,
                    'max_drawdown': max_drawdown,
                    'sharpe_ratio': sharpe_ratio,
                    'trade_count': len(trades)
                }
            }
                
                self.logger.info(f"Backtest completed: Returns: {returns:.2f}%, Win Rate: {win_rate:.2f}, Sharpe: {sharpe_ratio:.2f}")
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
        
        Args:
            dt_value: Can be datetime object, string, or None
            
        Returns:
            str or None: Formatted datetime string or None
        """
        if dt_value is None:
            return None
            
        try:
            # If it's already a string, log and return as is
            if isinstance(dt_value, str):
                return log_date_conversion(
                    dt_value,
                    dt_value,
                    "string datetime passthrough",
                    extra_info={"context": "backtest_engine_format_datetime"}
                )
                
            # If it's a datetime object, format it using our utility
            if isinstance(dt_value, datetime):
                return safe_strftime(
                    dt_value, 
                    '%Y-%m-%d %H:%M:%S',
                    extra_info={"context": "backtest_engine_format_datetime"}
                )
                
            # Try to convert other types to string with logging
            result = str(dt_value)
            return log_date_conversion(
                dt_value,
                result,
                f"conversion of {type(dt_value).__name__} to string",
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
            
        Returns:
            backtrader.Strategy: Backtrader strategy class
        """
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
                
            
            def log(self, txt, dt=None):
                """Logging function"""
                dt = dt or self.datas[0].datetime.date(0)
                print(f"{dt.isoformat()}: {txt}")
            
            def notify_order(self, order):
                """Handle order notifications"""
                if order.status in [order.Submitted, order.Accepted]:
                    # Order has been submitted/accepted - nothing to do
                    return
                
                # Check if an order has been completed
                if order.status in [order.Completed]:
                    if order.isbuy():
                        self.log(f"BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")
                        self.buyprice = order.executed.price
                        self.buycomm = order.executed.comm
                        
                        # Create a new trade record
                        self.current_trade = {
                            'entry_date': self.datas[0].datetime.datetime(0),
                            'entry_price': order.executed.price,
                            'exit_date': None,
                            'exit_price': None,
                            'profit_points': 0,
                            'profit_pct': 0,
                            'size': order.executed.size
                        }
                        
                        # Store the current bar index for position tracking
                        self.position_entry_bar = len(self.datas[0])
                    
                    elif order.issell():
                        self.log(f"SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")
                        
                        # Update the current trade record
                        self.current_trade['exit_date'] = self.datas[0].datetime.datetime(0)
                        self.current_trade['exit_price'] = order.executed.price
                        
                        # Calculate profit in points and percent
                        if strategy_type == 'buy':
                            self.current_trade['profit_points'] = order.executed.price - self.buyprice
                            self.current_trade['profit_pct'] = (order.executed.price / self.buyprice - 1) * 100
                        else:  # sell strategy
                            self.current_trade['profit_points'] = self.buyprice - order.executed.price
                            self.current_trade['profit_pct'] = (self.buyprice / order.executed.price - 1) * 100
                        
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
                                if comparison == '>':
                                    if var_value > threshold:
                                        return True
                                elif comparison == '>=':
                                    if var_value >= threshold:
                                        return True
                                elif comparison == '<':
                                    if var_value < threshold:
                                        return True
                                elif comparison == '<=':
                                    if var_value <= threshold:
                                        return True
                                elif comparison == '==':
                                    if var_value == threshold:
                                        return True
                                elif comparison == '!=':
                                    if var_value != threshold:
                                        return True
                            else:
                                # Log that we couldn't find the indicator line
                                self.log(f"Warning: Indicator line '{var_name}' not found in data feed")
                                # List available lines for debugging
                                available_lines = dir(self.datas[0].lines)
                                self.log(f"Available lines: {', '.join([l for l in available_lines if not l.startswith('_')])}")
                
                # If no conditions triggered, return False
                return False
            
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
                                if comparison == '>':
                                    if var_value > threshold:
                                        return True
                                elif comparison == '>=':
                                    if var_value >= threshold:
                                        return True
                                elif comparison == '<':
                                    if var_value < threshold:
                                        return True
                                elif comparison == '<=':
                                    if var_value <= threshold:
                                        return True
                                elif comparison == '==':
                                    if var_value == threshold:
                                        return True
                                elif comparison == '!=':
                                    if var_value != threshold:
                                        return True
                            else:
                                # Log that we couldn't find the indicator line
                                self.log(f"Warning: Indicator line '{var_name}' not found in data feed")
                                # List available lines for debugging
                                available_lines = dir(self.datas[0].lines)
                                self.log(f"Available lines: {', '.join([l for l in available_lines if not l.startswith('_')])}")
                
                # If no conditions triggered, check if we've been in position too long
                # as a failsafe - exit after 20 days in position if no other exit triggered
                if bars_in_position > 20:
                    self.log(f"Exit triggered by position duration: {bars_in_position} bars exceeds 20 bar limit")
                    return True
                    
                return False
        
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
