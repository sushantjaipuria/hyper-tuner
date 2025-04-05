import uuid
import logging
import json
import numpy as np
import pandas as pd
from skopt import gp_minimize
from skopt.space import Real, Integer, Categorical
from skopt.utils import use_named_args
import threading
import time
from copy import deepcopy
from logging_config import get_logger

class Optimizer:
    """Class to handle optimization of trading strategies"""
    
    def __init__(self, backtest_engine):
        """Initialize the Optimizer"""
        self.logger = get_logger(__name__)
        self.backtest_engine = backtest_engine
        self.optimizations = {}
    
    def optimize_strategy(self, strategy, original_backtest):
        """
        Optimize a trading strategy using Bayesian optimization
        
        Args:
            strategy (dict): Strategy configuration
            original_backtest (dict): Original backtest results
            
        Returns:
            dict: Optimization results
        """
        try:
            # Create a copy of the strategy
            strategy_copy = deepcopy(strategy)
            
            # Generate unique ID for the optimization
            optimization_id = str(uuid.uuid4())
            
            # Initialize optimization status
            self.optimizations[optimization_id] = {
                'status': 'starting',
                'progress': 0,
                'best_params': None,
                'best_result': None,
                'original_result': original_backtest['summary']['returns'],
                'iteration_results': []
            }
            
            # Get optimization parameters
            parameters_to_optimize = self._identify_parameters_to_optimize(strategy_copy)
            
            if not parameters_to_optimize:
                raise ValueError("No parameters to optimize found in the strategy")
            
            # Define the search space
            search_space = self._create_search_space(parameters_to_optimize)
            
            # Run optimization in a separate thread
            thread = threading.Thread(
                target=self._run_optimization,
                args=(
                    optimization_id,
                    strategy_copy,
                    original_backtest,
                    parameters_to_optimize,
                    search_space
                )
            )
            thread.daemon = True
            thread.start()
            
            # Return initial optimization results
            return {
                'optimization_id': optimization_id,
                'status': 'running',
                'summary': original_backtest['summary'],
                'comparison': {
                    'original': original_backtest['summary'],
                    'optimized': None
                }
            }
        
        except Exception as e:
            self.logger.error(f"Error starting optimization: {str(e)}")
            raise
    
    def get_optimization_status(self, optimization_id):
        """
        Get the status of an optimization
        
        Args:
            optimization_id (str): Optimization ID
            
        Returns:
            dict: Optimization status
        """
        try:
            if optimization_id not in self.optimizations:
                self.logger.error(f"Optimization with ID {optimization_id} not found")
                raise ValueError(f"Optimization with ID {optimization_id} not found")
            
            # Get a copy of the optimization status
            status = deepcopy(self.optimizations[optimization_id])
            
            # Format iteration results for better frontend visualization
            if 'iteration_results' in status and status['iteration_results']:
                # Calculate best objective value for each iteration (needed for chart)
                best_value = None
                for i, result in enumerate(status['iteration_results']):
                    # The objective is the negative of what we want to maximize
                    # Convert to positive values for visualization
                    current_value = -result['objective_value'] if 'objective_value' in result else 0
                    
                    # Update best seen so far
                    if best_value is None or current_value > best_value:
                        best_value = current_value
                    
                    # Add the best so far to the result
                    result['best_so_far'] = best_value
                    
                    # Add iteration number if not present
                    if 'iteration' not in result:
                        result['iteration'] = i + 1
            
            # Log basic status information
            self.logger.info(f"Status: {status.get('status')}, Progress: {status.get('progress')}%")
            self.logger.info(f"Iteration results count: {len(status.get('iteration_results', []))}")
            
            # Ensure all necessary fields are present
            if 'status' not in status:
                status['status'] = 'unknown'
            
            if 'progress' not in status:
                status['progress'] = 0
                
            if status['status'] == 'completed' and 'progress' in status:
                status['progress'] = 100  # Always set progress to 100% when complete
            
            # Return the status
            return status
        
        except Exception as e:
            self.logger.error(f"Error getting optimization status: {str(e)}")
            # Return a minimal valid status on error
            return {
                'status': 'error',
                'progress': 0,
                'error': str(e),
                'iteration_results': []
            }
            
    def _ensure_serializable(self, obj):
        """
        Ensure an object is JSON serializable by converting any non-serializable types
        
        Args:
            obj: The object to make serializable
            
        Returns:
            The serializable object
        """
        if isinstance(obj, dict):
            return {k: self._ensure_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._ensure_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return [self._ensure_serializable(item) for item in obj]
        elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32, np.float16)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return self._ensure_serializable(obj.tolist())
        elif hasattr(obj, 'tolist'):
            # For Pandas Series or other objects with tolist method
            try:
                return self._ensure_serializable(obj.tolist())
            except:
                return str(obj)
        elif hasattr(obj, 'to_dict'):
            # For Pandas DataFrames or other objects with to_dict method
            try:
                return self._ensure_serializable(obj.to_dict())
            except:
                return str(obj)
        elif obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        else:
            # For any other type, convert to string to ensure serializability
            self.logger.warning(f"Converting non-serializable type {type(obj).__name__} to string")
            return str(obj)
    
    def _identify_parameters_to_optimize(self, strategy):
        """
        Identify parameters to optimize in a strategy
        
        Args:
            strategy (dict): Strategy configuration
            
        Returns:
            list: List of parameters to optimize
        """
        parameters = []
        
        # Extract parameters from entry conditions
        for i, condition in enumerate(strategy['entry_conditions']):
            if 'indicator' in condition and 'params' in condition:
                # Add indicator parameters from params dictionary
                for param_name, param_value in condition['params'].items():
                    parameters.append({
                        'name': f"entry_{i}_{condition['indicator']}_{param_name}",
                        'path': ['entry_conditions', i, 'params', param_name],
                        'type': type(param_value).__name__,
                        'current_value': param_value
                    })
                
                # Add threshold value if present
                if 'threshold' in condition:
                    threshold_value = condition['threshold']
                    parameters.append({
                        'name': f"entry_{i}_{condition['indicator']}_threshold",
                        'path': ['entry_conditions', i, 'threshold'],
                        'type': type(threshold_value).__name__,
                        'current_value': threshold_value
                    })
        
        # Extract parameters from exit conditions
        if isinstance(strategy['exit_conditions'], list):
            for i, condition in enumerate(strategy['exit_conditions']):
                if 'indicator' in condition and 'params' in condition:
                    # Add indicator parameters from params dictionary
                    for param_name, param_value in condition['params'].items():
                        parameters.append({
                            'name': f"exit_{i}_{condition['indicator']}_{param_name}",
                            'path': ['exit_conditions', i, 'params', param_name],
                            'type': type(param_value).__name__,
                            'current_value': param_value
                        })
                    
                    # Add threshold value if present
                    if 'threshold' in condition:
                        threshold_value = condition['threshold']
                        parameters.append({
                            'name': f"exit_{i}_{condition['indicator']}_threshold",
                            'path': ['exit_conditions', i, 'threshold'],
                            'type': type(threshold_value).__name__,
                            'current_value': threshold_value
                        })
        
        # Add stop loss and target profit parameters
        if 'stop_loss' in strategy:
            parameters.append({
                'name': 'stop_loss',
                'path': ['stop_loss'],
                'type': type(strategy['stop_loss']).__name__,
                'current_value': strategy['stop_loss']
            })
        
        if 'target_profit' in strategy:
            parameters.append({
                'name': 'target_profit',
                'path': ['target_profit'],
                'type': type(strategy['target_profit']).__name__,
                'current_value': strategy['target_profit']
            })
        
        return parameters
    
    def _create_search_space(self, parameters):
        """
        Create a search space for Bayesian optimization
        
        Args:
            parameters (list): List of parameters to optimize
            
        Returns:
            list: List of parameter spaces
        """
        search_space = []
        
        for param in parameters:
            param_name = param['name']
            param_type = param['type']
            current_value = param['current_value']
            
            if param_type == 'int':
                # For integer parameters (e.g., periods)
                if 'period' in param_name.lower():
                    # For period parameters, create a range around the current value
                    min_value = max(2, int(current_value * 0.5))
                    max_value = int(current_value * 2)
                    search_space.append(Integer(min_value, max_value, name=param_name))
                else:
                    # For other integer parameters
                    min_value = max(1, int(current_value * 0.5))
                    max_value = int(current_value * 2)
                    search_space.append(Integer(min_value, max_value, name=param_name))
            
            elif param_type == 'float':
                # For float parameters
                if 'threshold' in param_name.lower():
                    # Special handling for threshold values
                    # The range should be more contextually appropriate
                    # For small values, use absolute bounds
                    if abs(current_value) < 10.0:
                        min_value = max(-100, current_value - abs(current_value * 2))
                        max_value = min(100, current_value + abs(current_value * 2))
                    else:
                        # For larger values, use relative bounds
                        min_value = current_value * 0.5
                        max_value = current_value * 1.5
                    search_space.append(Real(min_value, max_value, name=param_name))
                elif 'limit' in param_name.lower() or 'acceleration' in param_name.lower() or 'maximum' in param_name.lower():
                    # For limit parameters (e.g., fastlimit, slowlimit)
                    min_value = max(0.01, current_value * 0.5)
                    max_value = min(0.99, current_value * 2)
                    search_space.append(Real(min_value, max_value, name=param_name))
                else:
                    # For other float parameters
                    min_value = max(0.001, current_value * 0.5)
                    max_value = current_value * 2
                    search_space.append(Real(min_value, max_value, name=param_name))
            
            elif param_type == 'str':
                # For string parameters (e.g., MA type)
                if 'matype' in param_name.lower():
                    # For MA type parameters
                    search_space.append(Categorical(['SMA', 'EMA', 'WMA', 'DEMA', 'TEMA', 'TRIMA', 'KAMA'], name=param_name))
                else:
                    # For other string parameters
                    search_space.append(Categorical([current_value], name=param_name))
        
        return search_space
    
    def _update_strategy_params(self, strategy, parameters, params_values):
        """
        Update strategy parameters with new values
        
        Args:
            strategy (dict): Strategy configuration
            parameters (list): List of parameters to optimize
            params_values (dict): New parameter values
            
        Returns:
            dict: Updated strategy configuration
        """
        # Create a deep copy of the strategy
        updated_strategy = deepcopy(strategy)
        
        # Update parameters with new values
        for param in parameters:
            param_name = param['name']
            param_path = param['path']
            
            # Get the new value
            new_value = params_values[param_name]
            
            # Convert MA type string to integer if needed
            if 'matype' in param_name.lower():
                matype_map = {'SMA': 0, 'EMA': 1, 'WMA': 2, 'DEMA': 3, 'TEMA': 4, 'TRIMA': 5, 'KAMA': 6}
                if new_value in matype_map:
                    new_value = matype_map[new_value]
            
            # Add logging for threshold parameters
            if 'threshold' in param_name.lower():
                self.logger.info(f"Updating threshold parameter {param_name}: {param_path} from {param['current_value']} to {new_value}")
            
            # Update the parameter
            target = updated_strategy
            for key in param_path[:-1]:
                target = target[key] if isinstance(key, str) else target[int(key)]
            
            target[param_path[-1]] = new_value
        
        return updated_strategy
    
    def _run_optimization(self, optimization_id, strategy, original_backtest, parameters, search_space):
        """
        Run Bayesian optimization for a strategy
        
        Args:
            optimization_id (str): Optimization ID
            strategy (dict): Strategy configuration
            original_backtest (dict): Original backtest results
            parameters (list): List of parameters to optimize
            search_space (list): List of parameter spaces
        """
        # Update optimization status
        self.optimizations[optimization_id]['status'] = 'running'
        
        # Get backtest parameters
        start_date = original_backtest['start_date']
        end_date = original_backtest['end_date']
        initial_capital = original_backtest['initial_capital']
        
        # Create objective function for optimization
        @use_named_args(search_space)
        def objective(**params):
            # Update optimization status
            self.optimizations[optimization_id]['status'] = 'running iteration'
            
            # Log which parameters are being tested in this iteration
            self.logger.info(f"Optimization iteration with parameters:")
            threshold_params = {k: v for k, v in params.items() if 'threshold' in k.lower()}
            if threshold_params:
                self.logger.info(f"Threshold parameters: {threshold_params}")
            other_params = {k: v for k, v in params.items() if 'threshold' not in k.lower()}
            if other_params:
                self.logger.info(f"Other parameters: {other_params}")
                
            # Update strategy with new parameters
            updated_strategy = self._update_strategy_params(strategy, parameters, params)
            
            # Run backtest with updated parameters
            try:
                backtest_results = self.backtest_engine.run_backtest(
                    updated_strategy,
                    start_date,
                    end_date,
                    initial_capital
                )
                
                # Extract relevant metrics
                returns = backtest_results['returns']
                win_rate = backtest_results['win_rate']
                max_drawdown = backtest_results['max_drawdown']
                sharpe_ratio = backtest_results['sharpe_ratio']
                
                # Define objective value to minimize (negative of a weighted combination of metrics)
                # Note: Since gp_minimize minimizes, we negate the metrics we want to maximize
                objective_value = -(
                    0.5 * returns +            # Higher returns are better
                    0.2 * win_rate * 100 +     # Higher win rate is better
                    0.1 * (100 - max_drawdown) + # Lower drawdown is better
                    0.2 * sharpe_ratio         # Higher Sharpe ratio is better
                )
                
                # Store iteration result
                iteration_result = {
                    'params': params,
                    'returns': returns,
                    'win_rate': win_rate,
                    'max_drawdown': max_drawdown,
                    'sharpe_ratio': sharpe_ratio,
                    'objective_value': objective_value
                }
                
                self.optimizations[optimization_id]['iteration_results'].append(iteration_result)
                
                # Update best result if applicable
                if self.optimizations[optimization_id]['best_result'] is None or objective_value < self.optimizations[optimization_id]['best_result']:
                    self.optimizations[optimization_id]['best_params'] = params
                    self.optimizations[optimization_id]['best_result'] = objective_value
                
                return objective_value
            
            except Exception as e:
                self.logger.error(f"Error in optimization iteration: {str(e)}")
                # Return a high value to indicate failure
                return 1000000
        
        try:
            # Run Bayesian optimization
            n_calls = 50  # Number of iterations (increased from 20 for better optimization results)
            # Note: This value can be modified by editing this script directly
            result = gp_minimize(
                objective,
                search_space,
                n_calls=n_calls,
                random_state=42,
                verbose=True,
                callback=lambda res: self._update_optimization_progress(optimization_id, res.func_vals, n_calls)
            )
            
            # Get best parameters
            best_params = {space.name: result.x[i] for i, space in enumerate(search_space)}
            
            # Update strategy with best parameters
            best_strategy = self._update_strategy_params(strategy, parameters, best_params)
            
            # Run backtest with best parameters
            best_backtest = self.backtest_engine.run_backtest(
                best_strategy,
                start_date,
                end_date,
                initial_capital
            )
            
            # Calculate improvements
            original_summary = original_backtest['summary']
            optimized_summary = best_backtest['summary']
            
            # Ensure summaries have all required fields
            required_fields = ['returns', 'win_rate', 'max_drawdown', 'sharpe_ratio', 'trade_count']
            
            # Validate and ensure original summary has all fields
            for field in required_fields:
                if field not in original_summary:
                    self.logger.warning(f"Original summary missing field: {field}, adding default value")
                    original_summary[field] = 0.0
                    
            # Validate and ensure optimized summary has all fields
            for field in required_fields:
                if field not in optimized_summary:
                    self.logger.warning(f"Optimized summary missing field: {field}, adding default value")
                    optimized_summary[field] = 0.0
            
            improvements = {
                'returns': optimized_summary['returns'] - original_summary['returns'],
                'win_rate': optimized_summary['win_rate'] - original_summary['win_rate'],
                'max_drawdown': original_summary['max_drawdown'] - optimized_summary['max_drawdown'],
                'sharpe_ratio': optimized_summary['sharpe_ratio'] - original_summary['sharpe_ratio']
            }
            
            # Log optimization results with focus on threshold parameters
            self.logger.info(f"Optimization completed successfully for {optimization_id}")
            threshold_params = {k: v for k, v in best_params.items() if 'threshold' in k.lower()}
            if threshold_params:
                self.logger.info(f"Optimized threshold parameters: {threshold_params}")
                
                # Generate a comparison table for threshold parameters
                self.logger.info("Threshold parameter comparison:")
                for param in parameters:
                    if 'threshold' in param['name'].lower():
                        original = param['current_value']
                        optimized = best_params.get(param['name'], original)
                        improvement = ((optimized - original) / abs(original)) * 100 if original != 0 else 0
                        self.logger.info(f"  {param['name']}: Original={original:.4f}, Optimized={optimized:.4f}, Change={improvement:.2f}%")
            
            # Update optimization status
            self.optimizations[optimization_id]['status'] = 'completed'
            self.optimizations[optimization_id]['progress'] = 100
            self.optimizations[optimization_id]['best_params'] = best_params
            self.optimizations[optimization_id]['best_result'] = -result.fun
            self.optimizations[optimization_id]['best_backtest'] = best_backtest
            self.optimizations[optimization_id]['improvements'] = improvements
            self.optimizations[optimization_id]['comparison'] = {
                'original': original_summary,
                'optimized': optimized_summary
            }
            
            # Add detailed logging for the comparison data
            self.logger.info(f"Optimization completed: {optimization_id}")
            self.logger.info(f"Original summary structure: {list(original_summary.keys())}")
            self.logger.info(f"Optimized summary structure: {list(optimized_summary.keys())}")
            self.logger.info(f"Comparison data structure: {list(self.optimizations[optimization_id]['comparison'].keys())}")
            
            # Log the actual values for debugging
            self.logger.info(f"Original returns: {original_summary.get('returns')} (type: {type(original_summary.get('returns')).__name__})")
            self.logger.info(f"Optimized returns: {optimized_summary.get('returns')} (type: {type(optimized_summary.get('returns')).__name__})")
        
        except Exception as e:
            # Update optimization status on error
            self.optimizations[optimization_id]['status'] = 'failed'
            self.optimizations[optimization_id]['error'] = str(e)
            self.logger.error(f"Optimization failed: {str(e)}")
    
    def _update_optimization_progress(self, optimization_id, func_vals, n_calls):
        """Update optimization progress"""
        try:
            progress = min(100, int(len(func_vals) / n_calls * 100))
            self.optimizations[optimization_id]['progress'] = progress
        except Exception as e:
            self.logger.error(f"Error updating optimization progress: {str(e)}")

# Example usage:
if __name__ == "__main__":
    from kite_integration import KiteIntegration
    from backtest_engine import BacktestEngine
    
    # Initialize components
    kite = KiteIntegration()
    backtest_engine = BacktestEngine(kite)
    optimizer = Optimizer(backtest_engine)
    
    # Create a sample strategy and backtest
    strategy = {
        'strategy_id': '123',
        'name': 'EMA Crossover',
        'type': 'buy',
        'symbol': 'NIFTY 50',
        'timeframe': '1hour',
        'entry_conditions': [
            {
                'indicator': 'EMA',
                'params': {'timeperiod': 12},
                'variable': 'ema_short'
            },
            {
                'indicator': 'EMA',
                'params': {'timeperiod': 26},
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
    
    original_backtest = {
        'backtest_id': '456',
        'strategy_id': '123',
        'start_date': '2021-01-01',
        'end_date': '2021-12-31',
        'initial_capital': 100000,
        'summary': {
            'returns': 15.5,
            'win_rate': 0.65,
            'max_drawdown': 8.2,
            'sharpe_ratio': 1.1,
            'trade_count': 42
        }
    }
    
    # Run optimization
    # optimization_results = optimizer.optimize_strategy(strategy, original_backtest)
    # print(optimization_results)
