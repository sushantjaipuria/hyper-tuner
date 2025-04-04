import json
import os
import uuid
import logging
from datetime import datetime
from logging_config import get_logger

class StrategyManager:
    """Class to manage trading strategies"""
    
    def __init__(self, storage_dir='./strategies'):
        """Initialize the Strategy Manager"""
        self.logger = get_logger(__name__)
        self.storage_dir = storage_dir
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            self.logger.info(f"Created storage directory: {storage_dir}")
    
    def create_strategy(self, strategy_data):
        """
        Create a new trading strategy
        
        Args:
            strategy_data (dict): Strategy data including name, type, symbol, timeframe, entry_conditions, exit_conditions
            
        Returns:
            str: Strategy ID
        """
        try:
            # Validate strategy data
            self._validate_strategy_data(strategy_data)
            
            # Generate unique ID for the strategy
            strategy_id = str(uuid.uuid4())
            
            # Add metadata
            strategy_data['strategy_id'] = strategy_id
            strategy_data['created_at'] = datetime.now().isoformat()
            strategy_data['updated_at'] = datetime.now().isoformat()
            
            # Save strategy to file
            self._save_strategy_to_file(strategy_id, strategy_data)
            
            self.logger.info(f"Created strategy with ID: {strategy_id}")
            return strategy_id
        
        except Exception as e:
            self.logger.error(f"Error creating strategy: {str(e)}")
            raise
    
    def update_strategy(self, strategy_id, strategy_data):
        """
        Update an existing trading strategy
        
        Args:
            strategy_id (str): Strategy ID
            strategy_data (dict): Updated strategy data
            
        Returns:
            bool: True if successful
        """
        try:
            # Check if strategy exists
            if not self._strategy_exists(strategy_id):
                raise ValueError(f"Strategy with ID {strategy_id} not found")
            
            # Validate strategy data
            self._validate_strategy_data(strategy_data)
            
            # Get existing strategy
            existing_strategy = self.get_strategy(strategy_id)
            
            # Update strategy data
            existing_strategy.update(strategy_data)
            existing_strategy['updated_at'] = datetime.now().isoformat()
            
            # Save updated strategy to file
            self._save_strategy_to_file(strategy_id, existing_strategy)
            
            self.logger.info(f"Updated strategy with ID: {strategy_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error updating strategy: {str(e)}")
            raise
    
    def get_strategy(self, strategy_id):
        """
        Get a strategy by ID
        
        Args:
            strategy_id (str): Strategy ID
            
        Returns:
            dict: Strategy data
        """
        try:
            # Check if strategy exists
            if not self._strategy_exists(strategy_id):
                raise ValueError(f"Strategy with ID {strategy_id} not found")
            
            # Load strategy from file
            strategy_path = os.path.join(self.storage_dir, f"{strategy_id}.json")
            with open(strategy_path, 'r') as f:
                strategy_data = json.load(f)
            
            # Migrate any old format strategies to the new format
            strategy_data = self._migrate_strategy_if_needed(strategy_data)
            
            return strategy_data
        
        except Exception as e:
            self.logger.error(f"Error getting strategy: {str(e)}")
            raise
            
    def _migrate_strategy_if_needed(self, strategy):
        """
        Migrate an existing strategy to the new format if needed
        
        Args:
            strategy (dict): Strategy data
            
        Returns:
            dict: Migrated strategy data
        """
        try:
            # Check entry conditions
            if 'entry_conditions' in strategy:
                for condition in strategy['entry_conditions']:
                    # Migrate indicator conditions
                    if 'indicator' in condition and 'params' in condition:
                        params = condition.get('params', {})
                        
                        # Check if 'value' is a number, which is incorrect usage
                        if 'value' in params and isinstance(params['value'], (int, float)):
                            # Move the numeric value to a threshold parameter
                            condition['threshold'] = params['value']
                            
                            # Change the value parameter to a string (default to 'close')
                            params['value'] = 'close'
                            
                            # Log that we migrated this condition
                            self.logger.warning(f"Migrated strategy condition: moved numeric value {condition['threshold']} from 'value' to 'threshold'")
            
            # Also check exit conditions
            if 'exit_conditions' in strategy:
                for condition in strategy['exit_conditions']:
                    # Migrate indicator conditions
                    if 'indicator' in condition and 'params' in condition:
                        params = condition.get('params', {})
                        
                        # Check if 'value' is a number, which is incorrect usage
                        if 'value' in params and isinstance(params['value'], (int, float)):
                            # Move the numeric value to a threshold parameter
                            condition['threshold'] = params['value']
                            
                            # Change the value parameter to a string (default to 'close')
                            params['value'] = 'close'
                            
                            # Log that we migrated this condition
                            self.logger.warning(f"Migrated strategy condition: moved numeric value {condition['threshold']} from 'value' to 'threshold'")
            
            return strategy
        except Exception as e:
            self.logger.error(f"Error migrating strategy: {str(e)}")
            # Return the strategy unchanged if migration failed
            return strategy
    
    def delete_strategy(self, strategy_id):
        """
        Delete a strategy by ID
        
        Args:
            strategy_id (str): Strategy ID
            
        Returns:
            bool: True if successful
        """
        try:
            # Check if strategy exists
            if not self._strategy_exists(strategy_id):
                raise ValueError(f"Strategy with ID {strategy_id} not found")
            
            # Delete strategy file
            strategy_path = os.path.join(self.storage_dir, f"{strategy_id}.json")
            os.remove(strategy_path)
            
            self.logger.info(f"Deleted strategy with ID: {strategy_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error deleting strategy: {str(e)}")
            raise
    
    def list_strategies(self):
        """
        List all strategies
        
        Returns:
            list: List of strategy data
        """
        try:
            strategies = []
            
            # Iterate through strategy files
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    strategy_path = os.path.join(self.storage_dir, filename)
                    with open(strategy_path, 'r') as f:
                        strategy_data = json.load(f)
                    strategies.append(strategy_data)
            
            return strategies
        
        except Exception as e:
            self.logger.error(f"Error listing strategies: {str(e)}")
            raise
    
    def save_backtest_results(self, strategy_id, backtest_results):
        """
        Save backtest results for a strategy
        
        Args:
            strategy_id (str): Strategy ID
            backtest_results (dict): Backtest results
            
        Returns:
            str: Backtest ID
        """
        try:
            # Check if strategy exists
            if not self._strategy_exists(strategy_id):
                raise ValueError(f"Strategy with ID {strategy_id} not found")
            
            # Generate unique ID for the backtest
            backtest_id = str(uuid.uuid4())
            
            # Add metadata
            backtest_results['backtest_id'] = backtest_id
            backtest_results['strategy_id'] = strategy_id
            backtest_results['created_at'] = datetime.now().isoformat()
            
            # Create backtests directory if it doesn't exist
            backtests_dir = os.path.join(self.storage_dir, strategy_id, 'backtests')
            if not os.path.exists(backtests_dir):
                os.makedirs(backtests_dir)
            
            # Save backtest results to file
            backtest_path = os.path.join(backtests_dir, f"{backtest_id}.json")
            with open(backtest_path, 'w') as f:
                json.dump(backtest_results, f, indent=2)
            
            self.logger.info(f"Saved backtest results with ID: {backtest_id} for strategy: {strategy_id}")
            return backtest_id
        
        except Exception as e:
            self.logger.error(f"Error saving backtest results: {str(e)}")
            raise
    
    def get_backtest_results(self, strategy_id, backtest_id):
        """
        Get backtest results for a strategy
        
        Args:
            strategy_id (str): Strategy ID
            backtest_id (str): Backtest ID
            
        Returns:
            dict: Backtest results
        """
        try:
            # Check if strategy exists
            if not self._strategy_exists(strategy_id):
                raise ValueError(f"Strategy with ID {strategy_id} not found")
            
            # Check if backtest file exists
            backtest_path = os.path.join(self.storage_dir, strategy_id, 'backtests', f"{backtest_id}.json")
            if not os.path.exists(backtest_path):
                raise ValueError(f"Backtest with ID {backtest_id} not found for strategy {strategy_id}")
            
            # Load backtest results from file
            with open(backtest_path, 'r') as f:
                backtest_results = json.load(f)
            
            return backtest_results
        
        except Exception as e:
            self.logger.error(f"Error getting backtest results: {str(e)}")
            raise
    
    def save_optimization_results(self, strategy_id, optimization_results):
        """
        Save optimization results for a strategy
        
        Args:
            strategy_id (str): Strategy ID
            optimization_results (dict): Optimization results
            
        Returns:
            str: Optimization ID
        """
        try:
            # Check if strategy exists
            if not self._strategy_exists(strategy_id):
                raise ValueError(f"Strategy with ID {strategy_id} not found")
            
            # Generate unique ID for the optimization
            optimization_id = str(uuid.uuid4())
            
            # Add metadata
            optimization_results['optimization_id'] = optimization_id
            optimization_results['strategy_id'] = strategy_id
            optimization_results['created_at'] = datetime.now().isoformat()
            
            # Create optimizations directory if it doesn't exist
            optimizations_dir = os.path.join(self.storage_dir, strategy_id, 'optimizations')
            if not os.path.exists(optimizations_dir):
                os.makedirs(optimizations_dir)
            
            # Save optimization results to file
            optimization_path = os.path.join(optimizations_dir, f"{optimization_id}.json")
            with open(optimization_path, 'w') as f:
                json.dump(optimization_results, f, indent=2)
            
            self.logger.info(f"Saved optimization results with ID: {optimization_id} for strategy: {strategy_id}")
            return optimization_id
        
        except Exception as e:
            self.logger.error(f"Error saving optimization results: {str(e)}")
            raise
    
    def get_optimization_results(self, strategy_id, optimization_id):
        """
        Get optimization results for a strategy
        
        Args:
            strategy_id (str): Strategy ID
            optimization_id (str): Optimization ID
            
        Returns:
            dict: Optimization results
        """
        try:
            # Check if strategy exists
            if not self._strategy_exists(strategy_id):
                raise ValueError(f"Strategy with ID {strategy_id} not found")
            
            # Check if optimization file exists
            optimization_path = os.path.join(self.storage_dir, strategy_id, 'optimizations', f"{optimization_id}.json")
            if not os.path.exists(optimization_path):
                raise ValueError(f"Optimization with ID {optimization_id} not found for strategy {strategy_id}")
            
            # Load optimization results from file
            with open(optimization_path, 'r') as f:
                optimization_results = json.load(f)
            
            return optimization_results
        
        except Exception as e:
            self.logger.error(f"Error getting optimization results: {str(e)}")
            raise
    
    def _validate_strategy_data(self, strategy_data):
        """
        Validate strategy data
        
        Args:
            strategy_data (dict): Strategy data to validate
            
        Raises:
            ValueError: If validation fails
        """
        required_fields = ['name', 'type', 'symbol', 'timeframe', 'entry_conditions', 'exit_conditions']
        
        for field in required_fields:
            if field not in strategy_data:
                raise ValueError(f"Missing required field: {field}")
        
        if strategy_data['type'] not in ['buy', 'sell']:
            raise ValueError("Strategy type must be 'buy' or 'sell'")
            
        # Validate entry conditions
        if 'entry_conditions' in strategy_data:
            for condition in strategy_data['entry_conditions']:
                if 'indicator' in condition:
                    # Check if params is present for indicators
                    if 'params' not in condition:
                        condition['params'] = {}  # Add an empty params dict for backward compatibility
                        
                    # Validate the params
                    params = condition['params']
                    if 'value' in params and isinstance(params['value'], (int, float)):
                        # Migrate numeric 'value' to 'threshold'
                        self.logger.warning(f"Converting numeric 'value' parameter to 'threshold' during validation")
                        condition['threshold'] = params['value']
                        params['value'] = 'close'  # Set default to 'close'
                    elif 'value' in params and not isinstance(params['value'], str):
                        # Ensure 'value' is a string
                        params['value'] = str(params['value'])
                        
                # Make sure comparison conditions have a threshold
                if 'comparison' in condition and 'threshold' not in condition:
                    condition['threshold'] = 0  # Default threshold
                    self.logger.warning(f"Added default threshold of 0 to condition with comparison '{condition.get('comparison')}'")                
                        
        # Also validate exit conditions
        if 'exit_conditions' in strategy_data:
            for condition in strategy_data['exit_conditions']:
                if 'indicator' in condition:
                    # Check if params is present for indicators
                    if 'params' not in condition:
                        condition['params'] = {}  # Add an empty params dict for backward compatibility
                        
                    # Validate the params
                    params = condition['params']
                    if 'value' in params and isinstance(params['value'], (int, float)):
                        # Migrate numeric 'value' to 'threshold'
                        self.logger.warning(f"Converting numeric 'value' parameter to 'threshold' during validation")
                        condition['threshold'] = params['value']
                        params['value'] = 'close'  # Set default to 'close'
                    elif 'value' in params and not isinstance(params['value'], str):
                        # Ensure 'value' is a string
                        params['value'] = str(params['value'])
                        
                # Make sure comparison conditions have a threshold
                if 'comparison' in condition and 'threshold' not in condition:
                    condition['threshold'] = 0  # Default threshold
                    self.logger.warning(f"Added default threshold of 0 to condition with comparison '{condition.get('comparison')}'")                
    
    def _save_strategy_to_file(self, strategy_id, strategy_data):
        """
        Save strategy data to file
        
        Args:
            strategy_id (str): Strategy ID
            strategy_data (dict): Strategy data
        """
        # Create strategies directory if it doesn't exist
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
        
        # Create strategy directory if it doesn't exist
        strategy_dir = os.path.join(self.storage_dir, strategy_id)
        if not os.path.exists(strategy_dir):
            os.makedirs(strategy_dir)
        
        # Save strategy to file
        strategy_path = os.path.join(self.storage_dir, f"{strategy_id}.json")
        with open(strategy_path, 'w') as f:
            json.dump(strategy_data, f, indent=2)
    
    def _strategy_exists(self, strategy_id):
        """
        Check if a strategy exists
        
        Args:
            strategy_id (str): Strategy ID
            
        Returns:
            bool: True if strategy exists
        """
        strategy_path = os.path.join(self.storage_dir, f"{strategy_id}.json")
        return os.path.exists(strategy_path)

# Example usage:
if __name__ == "__main__":
    manager = StrategyManager()
    
    # Create a sample strategy
    strategy_data = {
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
    
    # strategy_id = manager.create_strategy(strategy_data)
    # print(f"Created strategy with ID: {strategy_id}")
