# Strategy Comparison
        
## 1. Original User-Defined Strategy
```json
{
  "name": "test",
  "type": "buy",
  "symbol": "ZOMATO",
  "timeframe": "15minute",
  "entry_conditions": [
    {
      "indicator": "SMA",
      "comparison": "<=",
      "params": {
        "value": "close",
        "timeperiod": 20
      },
      "variable": "sma",
      "threshold": 205
    }
  ],
  "exit_conditions": [],
  "stop_loss": 5,
  "target_profit": 25,
  "strategy_id": "2c2564b9-11bf-4ba8-8fe4-10367acc5a4d",
  "created_at": "2025-04-05T07:53:29.869482",
  "updated_at": "2025-04-05T07:53:29.869491"
}
```

## 2. Backtrader Interpretation of Strategy
### Strategy Type and Parameters
```json
{
  "strategy_type": "buy",
  "entry_conditions": [
    {
      "indicator": "SMA",
      "comparison": "<=",
      "params": {
        "value": "close",
        "timeperiod": 20
      },
      "variable": "sma",
      "threshold": 205
    }
  ],
  "exit_conditions": [],
  "stop_loss": 5,
  "target_profit": 25
}
```

### Indicator Processing
```json
{
  "sma": {
    "indicator_type": "SMA",
    "parameters": {
      "value": "close",
      "timeperiod": 20
    },
    "column_name": "sma",
    "sanitized_name": "sma",
    "found_in_data": true,
    "actual_column": "sma",
    "sample_values": [
      NaN,
      NaN,
      NaN
    ]
  }
}
```

### Data Feed Configuration
```json
{
  "columns": [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "sma"
  ],
  "indicator_mappings": {
    "sma": "sma"
  },
  "indicator_samples": {
    "sma": {
      "backtrader_name": "sma",
      "sample_values": [
        280.1450000000001,
        279.74500000000006,
        279.3900000000001
      ]
    }
  }
}
```

### Entry & Exit Condition Interpretation
```json
{
  "entry_interpretation": [
    {
      "type": "indicator_setup",
      "indicator": "SMA",
      "variable": "sma",
      "params": {
        "value": "close",
        "timeperiod": 20
      }
    }
  ],
  "exit_interpretation": [],
  "backtrader_translation": {
    "strategy_type": "BUY",
    "stop_loss_handling": "5% stop loss will trigger exit",
    "take_profit_handling": "25% profit target will trigger exit"
  }
}
```

## 3. Dynamically Created Backtrader Strategy Class
```python
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
                """Format a datetime value to string"""
                if dt_value is None:
                    return None
                    
                try:
                    if isinstance(dt_value, datetime):
                        return dt_value.strftime('%Y-%m-%d %H:%M:%S')
                    return str(dt_value)
                except Exception as e:
                    self.log(f"Error formatting datetime: {str(e)}")
                    return str(dt_value) if dt_value is not None else None
            
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
                            'entry_date': self._format_date(self.datas[0].datetime.datetime(0)),
                            'entry_price': order.executed.price,
                            'exit_date': None,
                            'exit_price': None,
                            'profit_points': 0,
                            'profit_pct': 0,
                            'size': order.executed.size
                        }
                        
                        # Store the current bar index for position tracking
                        self.position_entry_bar = len(self.datas[0])
                        
                        # Track position entry
                        timestamp_raw = self.datas[0].datetime.datetime(0)
                        timestamp_str = self._format_date(timestamp_raw)
                        self.position_tracking.append({
                            'action': 'ENTRY',
                            'timestamp': timestamp_str,
                            'price': order.executed.price,
                            'size': order.executed.size,
                            'bar_index': len(self.datas[0]),
                            'reason': 'Entry conditions met',
                            'portfolio_value': self.broker.getvalue()
                        })
                    
                    elif order.issell():
                        self.log(f"SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")
                        
                        # Update the current trade record
                        self.current_trade['exit_date'] = self._format_date(self.datas[0].datetime.datetime(0))
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
                        
                        # Track position exit
                        timestamp_raw = self.datas[0].datetime.datetime(0)
                        timestamp_str = self._format_date(timestamp_raw)
                        self.position_tracking.append({
                            'action': 'EXIT',
                            'timestamp': timestamp_str,
                            'price': order.executed.price,
                            'size': order.executed.size,
                            'bar_index': len(self.datas[0]),
                            'reason': exit_reason,
                            'portfolio_value': self.broker.getvalue(),
                            'profit_pct': self.current_trade['profit_pct']
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
                
                # Add tracking for this evaluation
                timestamp_raw = self.datas[0].datetime.datetime(0)
                timestamp_str = self._format_date(timestamp_raw)
                bar_tracking = {
                    'timestamp': timestamp_str,
                    'bar_number': current_bar,
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
                
                # Add tracking for this evaluation
                timestamp_raw = self.datas[0].datetime.datetime(0)
                timestamp_str = self._format_date(timestamp_raw)
                bar_tracking = {
                    'timestamp': timestamp_str,
                    'bar_number': current_bar,
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

```
