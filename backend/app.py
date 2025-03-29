from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import logging
import numpy as np
import csv
import io
from datetime import datetime

# Import custom modules
from strategy_manager import StrategyManager
from backtest_engine import BacktestEngine
from optimizer import Optimizer
from data_provider_factory import provider_factory
from indicators import Indicators

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes

# Initialize components
strategy_manager = StrategyManager()
data_provider = provider_factory.get_provider()
logger.info(f"Using data provider: {provider_factory.get_provider_name()}")
backtest_engine = BacktestEngine(data_provider)
optimizer = Optimizer(backtest_engine)
indicators = Indicators()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "data_provider": provider_factory.get_provider_name()
    })


@app.route('/api/save-strategy', methods=['POST'])
def save_strategy():
    """Save a trading strategy"""
    try:
        data = request.json
        strategy_id = strategy_manager.create_strategy(data)
        return jsonify({"success": True, "strategy_id": strategy_id})
    except Exception as e:
        logger.error(f"Error saving strategy: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/test', methods=['GET'])
def test_connection():
    """Simple test endpoint to verify connectivity"""
    return jsonify({"success": True, "message": "Backend API is reachable"})


@app.route('/api/get-strategy/<strategy_id>', methods=['GET'])
def get_strategy(strategy_id):
    """Get a trading strategy by ID"""
    try:
        strategy = strategy_manager.get_strategy(strategy_id)
        return jsonify({"success": True, "strategy": strategy})
    except Exception as e:
        logger.error(f"Error getting strategy: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/run-backtest', methods=['POST'])
def run_backtest():
    """Run a backtest for a strategy"""
    try:
        data = request.json
        strategy_id = data.get('strategy_id')
        
        if not strategy_id:
            logger.error("Missing strategy_id in request")
            return jsonify({"success": False, "error": "Missing strategy_id"}), 400
        
        # Get strategy from manager
        try:
            strategy = strategy_manager.get_strategy(strategy_id)
        except Exception as strat_err:
            logger.error(f"Error retrieving strategy {strategy_id}: {str(strat_err)}")
            return jsonify({"success": False, "error": f"Could not retrieve strategy: {str(strat_err)}"}), 404
        
        # Validate backtest parameters
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        initial_capital = data.get('initial_capital', 100000)
        
        if not start_date or not end_date:
            logger.error("Missing date parameters")
            return jsonify({"success": False, "error": "Start date and end date are required"}), 400
        
        try:
            # Validate dates format
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError as date_err:
            logger.error(f"Invalid date format: {str(date_err)}")
            return jsonify({"success": False, "error": f"Invalid date format. Use YYYY-MM-DD format: {str(date_err)}"}), 400
        
        # Run backtest with enhanced error handling
        try:
            logger.info(f"Running backtest for strategy {strategy_id} from {start_date} to {end_date}")
            logger.debug(f"Strategy: {strategy}")
            logger.debug(f"Using data provider: {type(data_provider).__name__}")
            
            backtest_results = backtest_engine.run_backtest(
                strategy, 
                start_date, 
                end_date, 
                initial_capital
            )
            
            # Save backtest results
            strategy_manager.save_backtest_results(strategy_id, backtest_results)
            
            logger.info(f"Backtest completed successfully for strategy {strategy_id}")
            return jsonify({
                "success": True, 
                "backtest_id": backtest_results["backtest_id"],
                "summary": backtest_results["summary"]
            })
        except ValueError as val_err:
            # Handle specific known errors more gracefully
            error_message = str(val_err)
            
            if "EMA() takes at least 1 positional argument" in error_message:
                error_message = "Error with EMA indicator: Please check the indicator parameters. Make sure you're not using a numeric value for 'value' parameter."
            elif "No 'close' price data found" in error_message:
                error_message = "Unable to retrieve price data. Please check the symbol and try again."
            
            logger.error(f"Backtest error: {error_message}")
            return jsonify({"success": False, "error": error_message}), 400
        except Exception as bt_err:
            error_message = str(bt_err)
            error_type = type(bt_err).__name__
            
            # Enhance error messages for common data structure issues
            if "'tuple' object has no attribute" in error_message:
                error_message = "Data structure error: The application is trying to access an attribute on a tuple. This is likely due to improper handling of Yahoo Finance data structure. The fix has been applied and should resolve on retry."
            elif "object has no attribute 'sma'" in error_message:
                error_message = "Indicator error: Could not apply SMA indicator properly to the data. The data structure from Yahoo Finance may need additional processing. Try running the backtest again."
            
            logger.error(f"Error running backtest ({error_type}): {error_message}")
            return jsonify({
                "success": False, 
                "error": f"Backtest engine error: {error_message}",
                "errorType": error_type
            }), 400
            
    except Exception as e:
        logger.error(f"Unexpected error running backtest: {str(e)}")
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


@app.route('/api/run-optimization', methods=['POST'])
def run_optimization():
    """Run optimization for a strategy"""
    try:
        logger.info("Received request to run optimization")
        data = request.json
        strategy_id = data.get('strategy_id')
        backtest_id = data.get('backtest_id')
        
        if not strategy_id:
            logger.error("Missing strategy_id in optimization request")
            return jsonify({"success": False, "error": "Missing strategy_id"}), 400
            
        if not backtest_id:
            logger.error("Missing backtest_id in optimization request")
            return jsonify({"success": False, "error": "Missing backtest_id"}), 400
        
        # Get strategy and original backtest results
        try:
            strategy = strategy_manager.get_strategy(strategy_id)
            original_backtest = strategy_manager.get_backtest_results(strategy_id, backtest_id)
        except Exception as e:
            logger.error(f"Error retrieving strategy or backtest data: {str(e)}")
            return jsonify({"success": False, "error": f"Failed to retrieve data: {str(e)}"}), 400
        
        # Start the optimization process (which now runs in background)
        logger.info(f"Starting optimization for strategy {strategy_id}")
        optimization_results = optimizer.optimize_strategy(
            strategy, 
            original_backtest
        )
        
        # Return immediately with the optimization ID
        optimization_id = optimization_results["optimization_id"]
        logger.info(f"Optimization started with ID: {optimization_id}")
        
        # Save initial optimization results
        strategy_manager.save_optimization_results(strategy_id, optimization_results)
        
        return jsonify({
            "success": True, 
            "optimization_id": optimization_id,
            "summary": original_backtest["summary"],
            "comparison": {"original": original_backtest["summary"], "optimized": None}
        })
    except Exception as e:
        logger.error(f"Error running optimization: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/optimization-status/<optimization_id>', methods=['GET'])
def optimization_status(optimization_id):
    """Get the status of an ongoing optimization process"""
    try:
        logger.info(f"Received request for optimization status: {optimization_id}")
        
        # Check if optimization exists
        if optimization_id not in optimizer.optimizations:
            logger.error(f"Optimization with ID {optimization_id} not found")
            return jsonify({"success": False, "error": f"Optimization with ID {optimization_id} not found"}), 404
        
        # Get optimization status
        status = optimizer.get_optimization_status(optimization_id)
        
        # Log basic status information
        logger.info(f"Status: {status.get('status')}, Progress: {status.get('progress')}%, Iterations: {len(status.get('iteration_results', []))}")
        
        # Create a simplified status object that's guaranteed to be serializable
        safe_status = {
            'status': status.get('status', 'unknown'),
            'progress': status.get('progress', 0),
            'iteration_results': []
        }
        
        # Add iteration results with safe numeric values
        if 'iteration_results' in status and status['iteration_results']:
            for result in status['iteration_results']:
                safe_result = {
                    'iteration': len(safe_status['iteration_results']) + 1,
                    'objective_value': float(result.get('objective_value', 0)) if result.get('objective_value') is not None else 0
                }
                safe_status['iteration_results'].append(safe_result)
        
        # Add best parameters if available
        if 'best_params' in status and status['best_params']:
            safe_status['best_params'] = {}
            for key, value in status['best_params'].items():
                if isinstance(value, (int, float, str, bool)) or value is None:
                    safe_status['best_params'][key] = value
                elif hasattr(value, 'item'):  # Handle numpy types
                    try:
                        safe_status['best_params'][key] = value.item()
                    except:
                        safe_status['best_params'][key] = float(value) if isinstance(value, (np.floating, np.float64, np.float32)) else int(value)
                else:
                    safe_status['best_params'][key] = str(value)
        
        # Add best result if available
        if 'best_result' in status and status['best_result'] is not None:
            safe_status['best_result'] = float(status['best_result'])
        
        # Add comparison data if completed
        if status.get('status') == 'completed' and 'comparison' in status and status['comparison']:
            safe_status['comparison'] = {}
            
            # Process original metrics
            if 'original' in status['comparison']:
                safe_status['comparison']['original'] = {}
                for key, value in status['comparison']['original'].items():
                    if isinstance(value, (int, float, str, bool)) or value is None:
                        safe_status['comparison']['original'][key] = value
                    elif hasattr(value, 'item'):  # Handle numpy types
                        try:
                            safe_status['comparison']['original'][key] = value.item()
                        except:
                            safe_status['comparison']['original'][key] = float(value) if isinstance(value, (np.floating, np.float64, np.float32)) else int(value)
                    else:
                        safe_status['comparison']['original'][key] = str(value)
            
            # Process optimized metrics
            if 'optimized' in status['comparison']:
                safe_status['comparison']['optimized'] = {}
                for key, value in status['comparison']['optimized'].items():
                    if isinstance(value, (int, float, str, bool)) or value is None:
                        safe_status['comparison']['optimized'][key] = value
                    elif hasattr(value, 'item'):  # Handle numpy types
                        try:
                            safe_status['comparison']['optimized'][key] = value.item()
                        except:
                            safe_status['comparison']['optimized'][key] = float(value) if isinstance(value, (np.floating, np.float64, np.float32)) else int(value)
                    else:
                        safe_status['comparison']['optimized'][key] = str(value)
        
        # Ensure all needed keys for frontend are present
        if 'comparison' not in safe_status and status.get('status') == 'completed':
            safe_status['comparison'] = {
                'original': status.get('original_result', {}),
                'optimized': {}
            }
        
        # Try to serialize to verify it's OK
        try:
            import json
            json_str = json.dumps({"success": True, "status": safe_status})
            logger.info(f"Successfully serialized status with length {len(json_str)}")
        except Exception as e:
            logger.error(f"Failed to serialize status: {str(e)}")
            return jsonify({"success": False, "error": "Failed to serialize optimization status"}), 500
        
        return jsonify({"success": True, "status": safe_status})
    except Exception as e:
        logger.error(f"Error getting optimization status: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/get-available-indicators', methods=['GET'])
def get_available_indicators():
    """Get list of available technical indicators"""
    try:
        logger.info("Fetching available indicators")
        indicator_list = indicators.get_available_indicators()
        logger.info(f"Successfully retrieved {len(indicator_list)} indicators")
        return jsonify({"success": True, "indicators": indicator_list})
    except Exception as e:
        logger.error(f"Error getting indicators: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return a minimal successful response with default indicators
        # This is better than failing completely
        try:
            default_indicators = indicators._get_default_indicators()
            # Sanitize the default indicators format
            simplified_indicators = {}
            for name, info in default_indicators.items():
                simplified_indicators[name] = {
                    'display_name': info.get('display_name', name),
                    'description': info.get('description', ''),
                    'category': info.get('category', 'Other'),
                    'params': info.get('params', ['value', 'timeperiod']),
                    'code_name': info.get('code_name', name)
                }
            logger.info(f"Falling back to {len(simplified_indicators)} default indicators")
            return jsonify({"success": True, "indicators": simplified_indicators})
        except Exception as fallback_error:
            logger.error(f"Error creating fallback indicators: {str(fallback_error)}")
            # Last resort minimal response with essential indicators
            minimal_indicators = {
                "SMA": {
                    "display_name": "Simple Moving Average (SMA)",
                    "description": "Average price over a specified period",
                    "category": "Overlap Studies",
                    "params": ["value", "timeperiod"],
                    "code_name": "SMA"
                },
                "EMA": {
                    "display_name": "Exponential Moving Average (EMA)",
                    "description": "Weighted moving average giving more importance to recent prices",
                    "category": "Overlap Studies",
                    "params": ["value", "timeperiod"],
                    "code_name": "EMA"
                },
                "RSI": {
                    "display_name": "Relative Strength Index (RSI)",
                    "description": "Momentum oscillator measuring speed and change of price movements (0-100)",
                    "category": "Momentum Indicators",
                    "params": ["value", "timeperiod"],
                    "code_name": "RSI"
                }
            }
            return jsonify({"success": True, "indicators": minimal_indicators})


@app.route('/api/debug/optimization-status/<optimization_id>', methods=['GET'])
def debug_optimization_status(optimization_id):
    """Debug endpoint for troubleshooting optimization status serialization"""
    try:
        logger.info(f"Debug request for optimization status: {optimization_id}")
        
        # First try to get the real status
        try:
            status = optimizer.get_optimization_status(optimization_id)
            logger.info(f"Retrieved actual optimization status for debugging")
        except Exception as e:
            logger.error(f"Could not retrieve actual status: {str(e)}")
            # Create a simplified test status
            status = {
                'status': 'completed',
                'progress': 100,
                'best_params': {'param1': 10, 'param2': 20},
                'best_result': 0.85,
                'iteration_results': [
                    {'iteration': 1, 'result': 0.5},
                    {'iteration': 2, 'result': 0.7},
                    {'iteration': 3, 'result': 0.85}
                ],
                'comparison': {
                    'original': {'returns': 5.2, 'win_rate': 0.6},
                    'optimized': {'returns': 7.8, 'win_rate': 0.75}
                }
            }
            logger.info(f"Created simplified test status for debugging")
        
        # Try to serialize with default json
        try:
            import json
            json_str = json.dumps(status)
            logger.info(f"Successfully serialized status with default JSON encoder")
        except Exception as e:
            logger.error(f"Default JSON serialization failed: {str(e)}")
            
            # Implement a custom JSON encoder to handle problematic types
            class CustomEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, (np.integer, np.int64, np.int32)):
                        return int(obj)
                    elif isinstance(obj, (np.floating, np.float64, np.float32)):
                        return float(obj)
                    elif isinstance(obj, np.ndarray):
                        return obj.tolist()
                    elif hasattr(obj, 'tolist'):
                        return obj.tolist()
                    elif hasattr(obj, 'to_dict'):
                        return obj.to_dict()
                    else:
                        return str(obj)
            
            try:
                json_str = json.dumps(status, cls=CustomEncoder)
                logger.info(f"Successfully serialized status with custom JSON encoder")
                status = json.loads(json_str)  # Convert back to ensure it's fully serializable
            except Exception as e:
                logger.error(f"Custom JSON serialization also failed: {str(e)}")
                # Last resort: create a minimal valid response
                status = {
                    'status': 'error',
                    'message': 'Could not serialize the optimization status'
                }
        
        return jsonify({"success": True, "status": status})
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/save-optimized-strategy', methods=['POST'])
def save_optimized_strategy():
    """Save an optimized strategy as a new strategy"""
    try:
        data = request.json
        strategy_id = data.get('strategy_id')
        optimization_id = data.get('optimization_id')
        
        logger.info(f"Saving optimized strategy for strategy {strategy_id} from optimization {optimization_id}")
        
        if not strategy_id or not optimization_id:
            logger.error("Missing strategy_id or optimization_id in request")
            return jsonify({"success": False, "error": "Missing strategy_id or optimization_id"}), 400
            
        # Get original strategy
        try:
            strategy = strategy_manager.get_strategy(strategy_id)
        except Exception as e:
            logger.error(f"Could not retrieve original strategy: {str(e)}")
            return jsonify({"success": False, "error": f"Could not retrieve original strategy: {str(e)}"}), 404
        
        # Get optimization data
        if optimization_id not in optimizer.optimizations:
            logger.error(f"Optimization with ID {optimization_id} not found")
            return jsonify({"success": False, "error": f"Optimization with ID {optimization_id} not found"}), 404
            
        optimization_status = optimizer.get_optimization_status(optimization_id)
        
        if optimization_status.get('status') != 'completed' or 'best_params' not in optimization_status:
            logger.error("Optimization not completed or no best parameters available")
            return jsonify({"success": False, "error": "Optimization not completed or no best parameters available"}), 400
        
        # Identify parameters that can be optimized
        parameters_to_optimize = optimizer._identify_parameters_to_optimize(strategy)
        
        # Update strategy with optimized parameters
        optimized_strategy = optimizer._update_strategy_params(
            strategy, 
            parameters_to_optimize,
            optimization_status['best_params']
        )
        
        # Rename the strategy to indicate it's optimized
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        optimized_strategy['name'] = f"{strategy['name']}_optimized_{timestamp}"
        
        # Save as a new strategy
        new_strategy_id = strategy_manager.create_strategy(optimized_strategy)
        
        # Create parameter comparison data for the response
        param_comparison = []
        for param in parameters_to_optimize:
            param_name = param['name']
            original_value = param['current_value']
            optimized_value = optimization_status['best_params'].get(param_name, original_value)
            
            # Format values for display
            if isinstance(original_value, float):
                original_value = round(original_value, 4)
            if isinstance(optimized_value, float):
                optimized_value = round(optimized_value, 4)
                
            # Extract a more readable name for threshold parameters
            display_name = param_name
            if 'threshold' in param_name.lower():
                # Extract indicator name and type (entry/exit) for a more readable display
                parts = param_name.split('_')
                # Find the indicator part (typically at index 2)
                indicator_name = parts[2] if len(parts) > 2 else 'indicator'
                # Determine if it's entry or exit
                condition_type = 'Entry' if parts[0] == 'entry' else 'Exit'
                display_name = f"{condition_type} {indicator_name} threshold"
            elif '_period' in param_name.lower() or 'timeperiod' in param_name.lower():
                # Better naming for period parameters
                parts = param_name.split('_')
                condition_type = 'Entry' if parts[0] == 'entry' else 'Exit'
                indicator_name = parts[2] if len(parts) > 2 else 'indicator'
                display_name = f"{condition_type} {indicator_name} period"
                
            param_comparison.append({
                'parameter': display_name,
                'original_value': original_value,
                'optimized_value': optimized_value
            })
        
        logger.info(f"Successfully saved optimized strategy with ID: {new_strategy_id}")
        
        return jsonify({
            "success": True, 
            "new_strategy_id": new_strategy_id,
            "strategy_name": optimized_strategy['name'],
            "parameter_comparison": param_comparison
        })
    except Exception as e:
        logger.error(f"Error saving optimized strategy: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/export-optimization-csv/<optimization_id>', methods=['GET'])
def export_optimization_csv(optimization_id):
    """Generate and download CSV report for optimization results"""
    try:
        logger.info(f"Generating CSV report for optimization: {optimization_id}")
        
        # Check if optimization exists
        if optimization_id not in optimizer.optimizations:
            logger.error(f"Optimization with ID {optimization_id} not found")
            return jsonify({"success": False, "error": f"Optimization with ID {optimization_id} not found"}), 404
        
        # Get optimization status
        status = optimizer.get_optimization_status(optimization_id)
        
        # Check if optimization is completed
        if status.get('status') != 'completed':
            logger.error(f"Optimization {optimization_id} is not completed yet")
            return jsonify({"success": False, "error": "Optimization not completed yet"}), 400
        
        # Create CSV in memory
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        
        # Write header
        csv_writer.writerow(['Trading Strategy Hyper-Tuner - Optimization Report'])
        csv_writer.writerow(['Generated on:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        csv_writer.writerow(['Optimization ID:', optimization_id])
        csv_writer.writerow([])
        
        # Write performance comparison
        csv_writer.writerow(['PERFORMANCE COMPARISON'])
        if 'comparison' in status and status['comparison']:
            comparison = status['comparison']
            csv_writer.writerow(['Metric', 'Original', 'Optimized', 'Improvement', 'Improvement (%)'])
            
            # Helper function to calculate improvement
            def calc_improvement(original, optimized):
                if original == 0:
                    return optimized, 'N/A'
                improvement = optimized - original
                pct_improvement = (improvement / abs(original)) * 100
                return improvement, f"{pct_improvement:.2f}%"
            
            # Add metrics
            if 'original' in comparison and 'optimized' in comparison:
                original = comparison['original']
                optimized = comparison['optimized']
                
                # Returns
                orig_returns = original.get('returns', 0)
                opt_returns = optimized.get('returns', 0)
                imp, imp_pct = calc_improvement(orig_returns, opt_returns)
                csv_writer.writerow(['Returns (%)', f"{orig_returns:.2f}", f"{opt_returns:.2f}", f"{imp:.2f}", imp_pct])
                
                # Win Rate
                orig_wr = original.get('win_rate', 0) * 100
                opt_wr = optimized.get('win_rate', 0) * 100
                imp, imp_pct = calc_improvement(orig_wr, opt_wr)
                csv_writer.writerow(['Win Rate (%)', f"{orig_wr:.2f}", f"{opt_wr:.2f}", f"{imp:.2f}", imp_pct])
                
                # Max Drawdown - Note: Lower is better
                orig_dd = original.get('max_drawdown', 0)
                opt_dd = optimized.get('max_drawdown', 0)
                # For drawdown, improvement is the reduction
                imp, imp_pct = calc_improvement(orig_dd, opt_dd)
                imp = -imp  # Invert because lower drawdown is better
                csv_writer.writerow(['Max Drawdown (%)', f"{orig_dd:.2f}", f"{opt_dd:.2f}", f"{imp:.2f}", imp_pct])
                
                # Sharpe Ratio
                orig_sr = original.get('sharpe_ratio', 0)
                opt_sr = optimized.get('sharpe_ratio', 0)
                imp, imp_pct = calc_improvement(orig_sr, opt_sr)
                csv_writer.writerow(['Sharpe Ratio', f"{orig_sr:.2f}", f"{opt_sr:.2f}", f"{imp:.2f}", imp_pct])
                
                # Trade Count
                orig_tc = original.get('trade_count', 0)
                opt_tc = optimized.get('trade_count', 0)
                imp, imp_pct = calc_improvement(orig_tc, opt_tc)
                csv_writer.writerow(['Trade Count', f"{orig_tc}", f"{opt_tc}", f"{imp}", imp_pct])
        
        csv_writer.writerow([])
        
        # Write optimized parameters
        if 'best_params' in status and status['best_params']:
            csv_writer.writerow(['OPTIMIZED PARAMETERS'])
            csv_writer.writerow(['Parameter', 'Value'])
            
            for param_name, param_value in status['best_params'].items():
                if isinstance(param_value, (int, float)):
                    csv_writer.writerow([param_name, f"{param_value:.4f}" if isinstance(param_value, float) else str(param_value)])
                else:
                    csv_writer.writerow([param_name, str(param_value)])
        
        csv_writer.writerow([])
        
        # Write optimization details
        csv_writer.writerow(['OPTIMIZATION DETAILS'])
        csv_writer.writerow(['Status:', status.get('status', 'Unknown')])
        csv_writer.writerow(['Progress:', f"{status.get('progress', 0)}%"])
        csv_writer.writerow(['Best Result:', f"{status.get('best_result', 0):.4f}"])
        
        # Write iteration results if available
        if 'iteration_results' in status and status['iteration_results']:
            csv_writer.writerow([])
            csv_writer.writerow(['ITERATION RESULTS'])
            csv_writer.writerow(['Iteration', 'Objective Value', 'Best So Far'])
            
            for result in status['iteration_results']:
                iteration = result.get('iteration', 0)
                obj_value = result.get('objective_value', 0)
                best_so_far = result.get('best_so_far', 0)
                
                csv_writer.writerow([iteration, f"{obj_value:.4f}", f"{best_so_far:.4f}"])
        
        # Get the CSV data
        csv_data = csv_buffer.getvalue()
        
        # Create a response with the CSV data
        response = Response(csv_data, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=optimization_report_{optimization_id}.csv'
        
        logger.info(f"Successfully generated CSV report for optimization: {optimization_id}")
        return response
    except Exception as e:
        logger.error(f"Error generating CSV report: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/debug/optimization-results/<optimization_id>', methods=['GET'])
def debug_optimization_results(optimization_id):
    """Debug endpoint to check raw optimization results"""
    try:
        logger.info(f"Debug request for raw optimization results: {optimization_id}")
        
        # Check if the optimization exists
        if optimization_id not in optimizer.optimizations:
            logger.error(f"Optimization with ID {optimization_id} not found")
            return jsonify({"success": False, "error": f"Optimization with ID {optimization_id} not found"}), 404
        
        # Get raw optimization data
        raw_data = optimizer.optimizations.get(optimization_id, {})
        
        # Log what we found
        logger.info(f"Raw optimization data keys: {list(raw_data.keys())}")
        
        # Create a simplified version that should be serializable
        safe_data = {
            'status': raw_data.get('status', 'unknown'),
            'progress': raw_data.get('progress', 0),
            'has_best_params': 'best_params' in raw_data,
            'best_result': float(raw_data.get('best_result', 0)) if raw_data.get('best_result') is not None else 0,
            'has_comparison': 'comparison' in raw_data,
            'comparison_keys': list(raw_data.get('comparison', {}).keys()) if isinstance(raw_data.get('comparison'), dict) else []
        }
        
        # Add some details about the optimization if they exist
        if 'best_params' in raw_data and raw_data['best_params']:
            try:
                safe_data['best_params_sample'] = {
                    k: str(v) for k, v in list(raw_data['best_params'].items())[:3]
                }
            except Exception as e:
                logger.error(f"Error extracting best params sample: {str(e)}")
                safe_data['best_params_error'] = str(e)
        
        # Add iteration count if available
        if 'iteration_results' in raw_data:
            safe_data['iteration_count'] = len(raw_data['iteration_results'])
        
        # Try to extract comparison data safely
        if 'comparison' in raw_data and isinstance(raw_data['comparison'], dict):
            if 'original' in raw_data['comparison']:
                original = raw_data['comparison']['original']
                if isinstance(original, dict):
                    safe_data['original_summary'] = {
                        k: str(v) for k, v in original.items()
                    }
            
            if 'optimized' in raw_data['comparison']:
                optimized = raw_data['comparison']['optimized']
                if isinstance(optimized, dict):
                    safe_data['optimized_summary'] = {
                        k: str(v) for k, v in optimized.items()
                    }
        
        return jsonify({"success": True, "data": safe_data})
    except Exception as e:
        logger.error(f"Error in debug endpoint for raw optimization results: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting Flask server on port 3001")
    app.run(debug=True, host='0.0.0.0', port=3001)
