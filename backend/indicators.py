import pandas as pd
import numpy as np
import talib
import inspect
import logging
import json
import os
from talib import abstract

class Indicators:
    """Class to handle technical indicators using TA-Lib"""
    
    def __init__(self):
        """Initialize the Indicators class"""
        self.logger = logging.getLogger(__name__)
        
        # Check TA-Lib version
        import talib
        self.talib_version = talib.__version__
        self.logger.info(f"Using TA-Lib version {self.talib_version}")
        
        # Load indicator mappings if available
        self.indicator_mappings = self._load_indicator_mappings()
        
        # Get all TA-Lib functions that are indicators
        self.available_indicators = self._get_all_talib_indicators()
    
    def _get_all_talib_indicators(self):
        """
        Discover all available TA-Lib indicators and their metadata
        
        Returns:
            dict: Dictionary of all available indicators with metadata
        """
        # Initialize result dictionary with existing indicators to ensure backward compatibility
        indicators = self._get_default_indicators()
        
        # Define the mapping of TA-Lib function groups to categories
        categories = {
            'Overlap Studies': ['BBANDS', 'DEMA', 'EMA', 'HT_TRENDLINE', 'KAMA', 'MA', 'MAMA', 'MAVP', 'MIDPOINT', 
                              'MIDPRICE', 'SAR', 'SAREXT', 'SMA', 'T3', 'TEMA', 'TRIMA', 'WMA'],
            'Momentum Indicators': ['ADX', 'ADXR', 'APO', 'AROON', 'AROONOSC', 'BOP', 'CCI', 'CMO', 'DX', 'MACD',
                                  'MACDEXT', 'MACDFIX', 'MFI', 'MINUS_DI', 'MINUS_DM', 'MOM', 'PLUS_DI', 
                                  'PLUS_DM', 'PPO', 'ROC', 'ROCP', 'ROCR', 'ROCR100', 'RSI', 'STOCH', 'STOCHF', 
                                  'STOCHRSI', 'TRIX', 'ULTOSC', 'WILLR'],
            'Volume Indicators': ['AD', 'ADOSC', 'OBV'],
            'Volatility Indicators': ['ATR', 'NATR', 'TRANGE'],
            'Price Transform': ['AVGPRICE', 'MEDPRICE', 'TYPPRICE', 'WCLPRICE'],
            'Cycle Indicators': ['HT_DCPERIOD', 'HT_DCPHASE', 'HT_PHASOR', 'HT_SINE', 'HT_TRENDMODE'],
            'Pattern Recognition': ['CDL2CROWS', 'CDL3BLACKCROWS', 'CDL3INSIDE', 'CDL3LINESTRIKE', 'CDL3OUTSIDE',
                                  'CDL3STARSINSOUTH', 'CDL3WHITESOLDIERS', 'CDLABANDONEDBABY', 'CDLADVANCEBLOCK',
                                  'CDLBELTHOLD', 'CDLBREAKAWAY', 'CDLCLOSINGMARUBOZU', 'CDLCONCEALBABYSWALL',
                                  'CDLCOUNTERATTACK', 'CDLDARKCLOUDCOVER', 'CDLDOJI', 'CDLDOJISTAR',
                                  'CDLDRAGONFLYDOJI', 'CDLENGULFING', 'CDLEVENINGDOJISTAR', 'CDLEVENINGSTAR',
                                  'CDLGAPSIDESIDEWHITE', 'CDLGRAVESTONEDOJI', 'CDLHAMMER', 'CDLHANGINGMAN',
                                  'CDLHARAMI', 'CDLHARAMICROSS', 'CDLHIGHWAVE', 'CDLHIKKAKE', 'CDLHIKKAKEMOD',
                                  'CDLHOMINGPIGEON', 'CDLIDENTICAL3CROWS', 'CDLINNECK', 'CDLINVERTEDHAMMER',
                                  'CDLKICKING', 'CDLKICKINGBYLENGTH', 'CDLLADDERBOTTOM', 'CDLLONGLEGGEDDOJI',
                                  'CDLLONGLINE', 'CDLMARUBOZU', 'CDLMATCHINGLOW', 'CDLMATHOLD', 'CDLMORNINGDOJISTAR',
                                  'CDLMORNINGSTAR', 'CDLONNECK', 'CDLPIERCING', 'CDLRICKSHAWMAN', 'CDLRISEFALL3METHODS',
                                  'CDLSEPARATINGLINES', 'CDLSHOOTINGSTAR', 'CDLSHORTLINE', 'CDLSPINNINGTOP',
                                  'CDLSTALLEDPATTERN', 'CDLSTICKSANDWICH', 'CDLTAKURI', 'CDLTASUKIGAP',
                                  'CDLTHRUSTING', 'CDLTRISTAR', 'CDLUNIQUE3RIVER', 'CDLUPSIDEGAP2CROWS',
                                  'CDLXSIDEGAP3METHODS'],
            'Math Transform': ['ACOS', 'ASIN', 'ATAN', 'CEIL', 'COS', 'COSH', 'EXP', 'FLOOR', 'LN', 'LOG10',
                             'SIN', 'SINH', 'SQRT', 'TAN', 'TANH'],
            'Math Operators': ['ADD', 'DIV', 'MAX', 'MAXINDEX', 'MIN', 'MININDEX', 'MINMAX', 'MINMAXINDEX',
                             'MULT', 'SUB', 'SUM']
        }
        
        # Flatten categories to get category for each function
        func_to_category = {}
        for category, funcs in categories.items():
            for func in funcs:
                func_to_category[func] = category
        
        # Get all TA-Lib functions
        talib_functions = sorted(talib.get_functions())
        
        # Use mappings from file if available, or fallback to built-in descriptions
        descriptions = {}
        for func_name in talib_functions:
            if func_name in self.indicator_mappings:
                descriptions[func_name] = self.indicator_mappings[func_name]['display_name']
            else:
                descriptions[func_name] = f"{func_name.replace('_', ' ').title()} Indicator"
        
        # Process each TA-Lib function
        for func_name in talib_functions:
            try:
                # Skip if already defined in the default indicators
                if func_name in indicators:
                    continue
                    
                # Get the actual function
                func = getattr(talib, func_name)
                
                # Get category
                category = func_to_category.get(func_name, 'Other')
                
                # Get description and detailed description from mappings
                display_name = descriptions.get(func_name, f"{func_name.replace('_', ' ').title()} Indicator")
                detailed_description = ""
                if func_name in self.indicator_mappings:
                    detailed_description = self.indicator_mappings[func_name].get('description', '')
                
                # Get parameters
                params = []
                
                # Try to get info from abstract API
                try:
                    info = abstract.Function(func_name)
                    params = list(info.parameters.keys())
                    input_names = info.input_names
                    
                    # Add input parameters (value/price, high, low, etc.)
                    for input_name in input_names:
                        # Convert 'price' to 'value' for better UI representation
                        input_name_lower = input_name.lower()
                        if input_name_lower == 'price':
                            input_name = 'value'
                        
                        if input_name.lower() not in [p.lower() for p in params]:
                            params = [input_name.lower()] + params
                except Exception as e:
                    self.logger.warning(f"Abstract API failed for {func_name}: {str(e)}")
                    # Fallback: inspect the function
                    try:
                        signature = inspect.signature(func)
                        params = list(signature.parameters.keys())
                        # Ensure consistent naming for common price parameters
                        if 'real' in params or 'price' in params:
                            params = ['value'] + [p for p in params if p not in ('real', 'price')]
                    except Exception as inner_e:
                        self.logger.warning(f"Fallback parameter extraction failed for {func_name}: {str(inner_e)}")
                        # Use safe default parameters for common indicators
                        if func_name in self.indicator_mappings:
                            # Use known parameters for this indicator
                            # Most indicators use these two params at minimum
                            params = ['value', 'timeperiod']
                        else:
                            # Last resort default parameters
                            params = ['value', 'timeperiod']
                
                # Add to indicators dictionary
                indicators[func_name] = {
                    'function': func,
                    'params': params,
                    'display_name': display_name,
                    'description': detailed_description,
                    'category': category,
                    'code_name': func_name  # Original code name for reference
                }
            except Exception as e:
                self.logger.warning(f"Couldn't add indicator {func_name}: {str(e)}")
        
        return indicators
    
    def _get_default_indicators(self):
        """
        Get the default set of indicators with their detailed configuration
        Ensures backward compatibility with existing implementation
        
        Returns:
            dict: Dictionary of default indicators with their configuration
        """
        return {
            # Overlap Studies
            'SMA': {
                'function': talib.SMA,
                'params': ['value', 'timeperiod'],
                'display_name': 'Simple Moving Average (SMA)',
                'description': 'Average price over a specified period',
                'category': 'Overlap Studies',
                'code_name': 'SMA'
            },
            'EMA': {
                'function': talib.EMA,
                'params': ['value', 'timeperiod'],
                'display_name': 'Exponential Moving Average (EMA)',
                'description': 'Weighted moving average giving more importance to recent prices',
                'category': 'Overlap Studies',
                'code_name': 'EMA'
            },
            'WMA': {
                'function': talib.WMA,
                'params': ['value', 'timeperiod'],
                'display_name': 'Weighted Moving Average (WMA)',
                'description': 'Moving average with linearly increasing weights for newer data',
                'category': 'Overlap Studies',
                'code_name': 'WMA'
            },
            'DEMA': {
                'function': talib.DEMA,
                'params': ['value', 'timeperiod'],
                'display_name': 'Double Exponential Moving Average (DEMA)',
                'description': 'Moving average designed to reduce lag of traditional EMAs',
                'category': 'Overlap Studies',
                'code_name': 'DEMA'
            },
            'TEMA': {
                'function': talib.TEMA,
                'params': ['value', 'timeperiod'],
                'display_name': 'Triple Exponential Moving Average (TEMA)',
                'description': 'Moving average with reduced lag over traditional EMAs',
                'category': 'Overlap Studies',
                'code_name': 'TEMA'
            },
            'TRIMA': {
                'function': talib.TRIMA,
                'params': ['value', 'timeperiod'],
                'description': 'Triangular Moving Average',
                'category': 'Overlap Studies'
            },
            'KAMA': {
                'function': talib.KAMA,
                'params': ['value', 'timeperiod'],
                'description': 'Kaufman Adaptive Moving Average',
                'category': 'Overlap Studies'
            },
            'MAMA': {
                'function': talib.MAMA,
                'params': ['value', 'fastlimit', 'slowlimit'],
                'description': 'MESA Adaptive Moving Average',
                'category': 'Overlap Studies'
            },
            'BBANDS': {
                'function': talib.BBANDS,
                'params': ['value', 'timeperiod', 'nbdevup', 'nbdevdn', 'matype'],
                'display_name': 'Bollinger Bands (BB)',
                'description': 'Volatility bands placed above and below a moving average',
                'category': 'Overlap Studies',
                'code_name': 'BBANDS'
            },
            'SAR': {
                'function': talib.SAR,
                'params': ['high', 'low', 'acceleration', 'maximum'],
                'description': 'Parabolic SAR',
                'category': 'Overlap Studies'
            },
            
            # Momentum Indicators
            'RSI': {
                'function': talib.RSI,
                'params': ['value', 'timeperiod'],
                'display_name': 'Relative Strength Index (RSI)',
                'description': 'Momentum oscillator measuring speed and change of price movements (0-100)',
                'category': 'Momentum Indicators',
                'code_name': 'RSI'
            },
            'MACD': {
                'function': talib.MACD,
                'params': ['value', 'fastperiod', 'slowperiod', 'signalperiod'],
                'display_name': 'Moving Average Convergence Divergence (MACD)',
                'description': 'Trend-following momentum indicator showing relationship between two moving averages',
                'category': 'Momentum Indicators',
                'code_name': 'MACD'
            },
            'STOCH': {
                'function': talib.STOCH,
                'params': ['high', 'low', 'close', 'fastk_period', 'slowk_period', 'slowk_matype', 'slowd_period', 'slowd_matype'],
                'description': 'Stochastic',
                'category': 'Momentum Indicators'
            },
            'STOCHF': {
                'function': talib.STOCHF,
                'params': ['high', 'low', 'close', 'fastk_period', 'fastd_period', 'fastd_matype'],
                'description': 'Stochastic Fast',
                'category': 'Momentum Indicators'
            },
            'STOCHRSI': {
                'function': talib.STOCHRSI,
                'params': ['value', 'timeperiod', 'fastk_period', 'fastd_period', 'fastd_matype'],
                'description': 'Stochastic Relative Strength Index',
                'category': 'Momentum Indicators'
            },
            'ADX': {
                'function': talib.ADX,
                'params': ['high', 'low', 'close', 'timeperiod'],
                'description': 'Average Directional Movement Index',
                'category': 'Momentum Indicators'
            },
            'ADXR': {
                'function': talib.ADXR,
                'params': ['high', 'low', 'close', 'timeperiod'],
                'description': 'Average Directional Movement Index Rating',
                'category': 'Momentum Indicators'
            },
            'CCI': {
                'function': talib.CCI,
                'params': ['high', 'low', 'close', 'timeperiod'],
                'description': 'Commodity Channel Index',
                'category': 'Momentum Indicators'
            },
            'MOM': {
                'function': talib.MOM,
                'params': ['value', 'timeperiod'],
                'description': 'Momentum',
                'category': 'Momentum Indicators'
            },
            'ROC': {
                'function': talib.ROC,
                'params': ['value', 'timeperiod'],
                'description': 'Rate of change',
                'category': 'Momentum Indicators'
            },
            
            # Volume Indicators
            'OBV': {
                'function': talib.OBV,
                'params': ['close', 'volume'],
                'description': 'On Balance Volume',
                'category': 'Volume Indicators'
            },
            'AD': {
                'function': talib.AD,
                'params': ['high', 'low', 'close', 'volume'],
                'description': 'Chaikin A/D Line',
                'category': 'Volume Indicators'
            },
            'ADOSC': {
                'function': talib.ADOSC,
                'params': ['high', 'low', 'close', 'volume', 'fastperiod', 'slowperiod'],
                'description': 'Chaikin A/D Oscillator',
                'category': 'Volume Indicators'
            },
            
            # Volatility Indicators
            'ATR': {
                'function': talib.ATR,
                'params': ['high', 'low', 'close', 'timeperiod'],
                'description': 'Average True Range',
                'category': 'Volatility Indicators'
            },
            'NATR': {
                'function': talib.NATR,
                'params': ['high', 'low', 'close', 'timeperiod'],
                'description': 'Normalized Average True Range',
                'category': 'Volatility Indicators'
            },
            
            # Pattern Recognition
            'CDLENGULFING': {
                'function': talib.CDLENGULFING,
                'params': ['open', 'high', 'low', 'close'],
                'description': 'Engulfing Pattern',
                'category': 'Pattern Recognition'
            },
            'CDLDOJI': {
                'function': talib.CDLDOJI,
                'params': ['open', 'high', 'low', 'close'],
                'description': 'Doji',
                'category': 'Pattern Recognition'
            },
            'CDLHAMMER': {
                'function': talib.CDLHAMMER,
                'params': ['open', 'high', 'low', 'close'],
                'description': 'Hammer',
                'category': 'Pattern Recognition'
            }
        }
    
    def _load_indicator_mappings(self):
        """
        Load indicator mappings from JSON file
        
        Returns:
            dict: Dictionary of indicator mappings or empty dict if file not found
        """
        try:
            mapping_file = os.path.join(os.path.dirname(__file__), 'indicator_mappings.json')
            self.logger.info(f"Loading indicator mappings from {mapping_file}")
            
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r') as f:
                    mappings = json.load(f)
                self.logger.info(f"Loaded {len(mappings)} indicator mappings")
                return mappings
            else:
                self.logger.warning(f"Indicator mappings file not found at {mapping_file}")
                return {}
        except Exception as e:
            self.logger.error(f"Error loading indicator mappings: {str(e)}")
            return {}
    
    def get_available_indicators(self):
        """
        Get list of available indicators
        
        Returns:
            dict: Dictionary of available indicators with their metadata
        """
        result = {}
        for name, info in self.available_indicators.items():
            # Ensure minimal valid structure for each indicator
            cleaned_info = {
                'display_name': info.get('display_name', name),
                'description': info.get('description', ''),
                'category': info.get('category', 'Other'),
                'code_name': info.get('code_name', name)  # Original code for reference
            }
            
            # Ensure params is always a list
            if 'params' not in info or not isinstance(info['params'], list):
                # Default safe params
                self.logger.warning(f"Missing or invalid params for indicator {name}, using defaults")
                cleaned_info['params'] = ['value', 'timeperiod'] 
            else:
                cleaned_info['params'] = info['params']
                
            result[name] = cleaned_info
        
        # Log the number of indicators found
        self.logger.info(f"Returning {len(result)} available indicators")
        return result
    
    def calculate_indicator(self, indicator_name, data, params=None):
        """
        Calculate a technical indicator using TA-Lib
        
        Args:
            indicator_name (str): Name of the indicator to calculate
            data (pandas.DataFrame): DataFrame with OHLCV data
            params (dict): Parameters for the indicator
            
        Returns:
            pandas.Series or tuple of pandas.Series: Calculated indicator values
        """
        try:
            # Check if indicator is supported
            if indicator_name not in self.available_indicators:
                raise ValueError(f"Indicator {indicator_name} is not supported")
            
            # Get indicator info
            indicator_info = self.available_indicators[indicator_name]
            indicator_function = indicator_info['function']
            required_params = indicator_info['params']
            
            # Initialize parameters for the indicator function
            function_params = {}
            
            # Map DataFrame columns to required parameters
            for param in required_params:
                param_lower = param.lower()
                
                # Check if this parameter is provided in the params dict
                is_param_provided = params and param in params
                
                # Special handling for price/value parameters
                if param_lower == 'price' or param_lower == 'value':
                    if is_param_provided:
                        # If value is provided in params, check if it's a column name or a numeric value
                        param_value = params[param]
                        if isinstance(param_value, (int, float)):
                            # If it's a numeric value, we still need to use a price series
                            # This is likely a user error - they specified a value when they should have specified a timeperiod
                            self.logger.warning(f"Parameter 'value' was provided as a number ({param_value}). Using 'close' price series instead.")
                            function_params[param] = data['close'].values
                        elif isinstance(param_value, str) and param_value in data.columns:
                            # If it's a string and it's a column name, use that column
                            function_params[param] = data[param_value].values
                        else:
                            # Default to close if the provided value doesn't match any column
                            self.logger.warning(f"Parameter 'value' was provided but doesn't match a valid column. Using 'close' price series instead.")
                            function_params[param] = data['close'].values
                    else:
                        # Default to 'close' if not specified
                        function_params[param] = data['close'].values
                elif param_lower == 'open':
                    # Verify that the column exists before using it
                    if 'open' in data.columns and not data['open'].equals(pd.Series(0, index=data.index)):
                        function_params[param] = data['open'].values
                    else:
                        self.logger.warning(f"Column 'open' is missing or contains only zeros. Using 'close' values instead.")
                        function_params[param] = data['close'].values
                elif param_lower == 'high':
                    # Verify that the column exists before using it
                    if 'high' in data.columns and not data['high'].equals(pd.Series(0, index=data.index)):
                        function_params[param] = data['high'].values
                    else:
                        self.logger.warning(f"Column 'high' is missing or contains only zeros. Using 'close' values instead.")
                        function_params[param] = data['close'].values
                elif param_lower == 'low':
                    # Verify that the column exists before using it
                    if 'low' in data.columns and not data['low'].equals(pd.Series(0, index=data.index)):
                        function_params[param] = data['low'].values
                    else:
                        self.logger.warning(f"Column 'low' is missing or contains only zeros. Using 'close' values instead.")
                        function_params[param] = data['close'].values
                elif param_lower == 'close':
                    # Verify that the column exists before using it
                    if 'close' in data.columns:
                        function_params[param] = data['close'].values
                    else:
                        raise ValueError("Column 'close' is required but not available in the data")
                elif param_lower == 'volume':
                    # Verify that the column exists before using it
                    if 'volume' in data.columns:
                        function_params[param] = data['volume'].values
                    else:
                        # For volume, we'll default to zeros if not available
                        self.logger.warning(f"Column 'volume' is missing. Using zeros instead.")
                        function_params[param] = np.zeros(len(data))
                elif is_param_provided:
                    # Use provided parameter value
                    function_params[param] = params[param]
                else:
                    # Use default values for missing parameters
                    if param_lower == 'timeperiod':
                        function_params[param] = 14
                    elif param_lower == 'fastperiod':
                        function_params[param] = 12
                    elif param_lower == 'slowperiod':
                        function_params[param] = 26
                    elif param_lower == 'signalperiod':
                        function_params[param] = 9
                    elif param_lower == 'fastk_period':
                        function_params[param] = 5
                    elif param_lower == 'fastd_period':
                        function_params[param] = 3
                    elif param_lower == 'slowk_period':
                        function_params[param] = 3
                    elif param_lower == 'slowd_period':
                        function_params[param] = 3
                    elif param_lower == 'matype':
                        function_params[param] = 0  # SMA
                    elif param_lower == 'slowk_matype':
                        function_params[param] = 0  # SMA
                    elif param_lower == 'slowd_matype':
                        function_params[param] = 0  # SMA
                    elif param_lower == 'fastd_matype':
                        function_params[param] = 0  # SMA
                    elif param_lower == 'nbdevup':
                        function_params[param] = 2
                    elif param_lower == 'nbdevdn':
                        function_params[param] = 2
                    elif param_lower == 'acceleration':
                        function_params[param] = 0.02
                    elif param_lower == 'maximum':
                        function_params[param] = 0.2
                    elif param_lower == 'fastlimit':
                        function_params[param] = 0.5
                    elif param_lower == 'slowlimit':
                        function_params[param] = 0.05
                    else:
                        # For parameters we don't know about, set a reasonable default
                        if isinstance(param, str) and 'period' in param_lower:
                            function_params[param] = 14
                        else:
                            function_params[param] = 0
            
            # Calculate indicator
            # Many TA-Lib functions expect the first argument (price series) as a positional argument
            # We need to extract it and pass it separately
            
            # Determine which parameter is the price series parameter
            price_param_name = None
            for param in required_params:
                param_lower = param.lower()
                if param_lower in ['price', 'value', 'real']:
                    price_param_name = param
                    break
            
            # Extract the price series if we identified the parameter
            price_series = None
            if price_param_name and price_param_name in function_params:
                price_series = function_params.pop(price_param_name)
            
            # Call the indicator function with price series as first argument
            if price_series is not None:
                result = indicator_function(price_series, **function_params)
            else:
                # Fallback to using all as keyword arguments
                # Note: This might fail for indicators that expect a positional first argument
                self.logger.warning(f"Could not identify price series parameter for {indicator_name}. Using keyword arguments.")
                result = indicator_function(**function_params)
            
            # Convert result to DataFrame or Series
            if isinstance(result, tuple):
                # Multiple outputs (e.g., MACD returns macd, macdsignal, macdhist)
                result_dict = {}
                
                # Handle known multi-output indicators
                if indicator_name == 'MACD':
                    result_dict['macd'] = pd.Series(result[0], index=data.index)
                    result_dict['macdsignal'] = pd.Series(result[1], index=data.index)
                    result_dict['macdhist'] = pd.Series(result[2], index=data.index)
                elif indicator_name == 'BBANDS':
                    result_dict['upperband'] = pd.Series(result[0], index=data.index)
                    result_dict['middleband'] = pd.Series(result[1], index=data.index)
                    result_dict['lowerband'] = pd.Series(result[2], index=data.index)
                elif indicator_name == 'STOCH':
                    result_dict['slowk'] = pd.Series(result[0], index=data.index)
                    result_dict['slowd'] = pd.Series(result[1], index=data.index)
                elif indicator_name == 'STOCHF':
                    result_dict['fastk'] = pd.Series(result[0], index=data.index)
                    result_dict['fastd'] = pd.Series(result[1], index=data.index)
                elif indicator_name == 'STOCHRSI':
                    result_dict['fastk'] = pd.Series(result[0], index=data.index)
                    result_dict['fastd'] = pd.Series(result[1], index=data.index)
                elif indicator_name == 'MAMA':
                    result_dict['mama'] = pd.Series(result[0], index=data.index)
                    result_dict['fama'] = pd.Series(result[1], index=data.index)
                elif indicator_name == 'AROON':
                    result_dict['aroondown'] = pd.Series(result[0], index=data.index)
                    result_dict['aroonup'] = pd.Series(result[1], index=data.index)
                elif indicator_name == 'HT_PHASOR':
                    result_dict['inphase'] = pd.Series(result[0], index=data.index)
                    result_dict['quadrature'] = pd.Series(result[1], index=data.index)
                elif indicator_name == 'HT_SINE':
                    result_dict['sine'] = pd.Series(result[0], index=data.index)
                    result_dict['leadsine'] = pd.Series(result[1], index=data.index)
                elif indicator_name == 'MINMAX':
                    result_dict['min'] = pd.Series(result[0], index=data.index)
                    result_dict['max'] = pd.Series(result[1], index=data.index)
                elif indicator_name == 'MINMAXINDEX':
                    result_dict['minidx'] = pd.Series(result[0], index=data.index)
                    result_dict['maxidx'] = pd.Series(result[1], index=data.index)
                else:
                    # Generic handling for other multi-output indicators
                    for i, res in enumerate(result):
                        result_dict[f'output{i+1}'] = pd.Series(res, index=data.index)
                
                return result_dict
            else:
                # Single output
                return pd.Series(result, index=data.index, name=indicator_name)
        
        except Exception as e:
            self.logger.error(f"Error calculating indicator {indicator_name}: {str(e)}")
            raise

    def add_all_indicators(self, data, indicator_configs):
        """
        Add multiple indicators to a DataFrame
        
        Args:
            data (pandas.DataFrame): DataFrame with OHLCV data
            indicator_configs (list): List of indicator configurations
            
        Returns:
            pandas.DataFrame: DataFrame with indicators added
        """
        # Normalize data column names to handle any unexpected column formats
        self._normalize_dataframe_columns(data)
        try:
            # Validate data has required columns
            if 'close' not in data.columns:
                self.logger.error("Data missing required 'close' column")
                raise ValueError("Data missing required 'close' column. This is needed for most indicators.")
            
            # Check for empty data
            if data.empty:
                self.logger.error("Empty data provided for indicators")
                raise ValueError("Empty data provided. Cannot calculate indicators on empty data.")
            
            # Make a copy of the data with normalized column names
            result = data.copy()
            
            if not indicator_configs:
                self.logger.warning("No indicator configurations provided")
                return result
            
            # Add each indicator
            for idx, config in enumerate(indicator_configs):
                try:
                    # Validate config has required fields
                    if 'indicator' not in config:
                        self.logger.error(f"Missing 'indicator' key in configuration {idx}: {config}")
                        raise ValueError(f"Missing 'indicator' key in configuration {idx}")
                    
                    indicator_name = config['indicator']
                    params = config.get('params', {})
                    variable = config.get('variable', indicator_name.lower())
                    
                    self.logger.info(f"Adding indicator {indicator_name} with params {params} as variable {variable}")
                    
                    # Check if indicator exists
                    if indicator_name not in self.available_indicators:
                        self.logger.error(f"Indicator '{indicator_name}' not found in available indicators")
                        raise ValueError(f"Indicator '{indicator_name}' not found. Available indicators: {', '.join(sorted(self.available_indicators.keys())[:10])}...")
                    
                    # Calculate indicator
                    indicator_values = self.calculate_indicator(indicator_name, data, params)
                    
                    # Ensure variable name is valid - sanitize it
                    var_name = str(variable)  # Ensure it's a string
                    var_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in var_name)  # Replace invalid chars
                    # Ensure it starts with a letter or underscore
                    if var_name and not var_name[0].isalpha() and var_name[0] != '_':
                        var_name = 'ind_' + var_name
                    
                    self.logger.debug(f"Using indicator variable name: {var_name}")
                    
                    # Add indicator to result DataFrame
                    if isinstance(indicator_values, dict):
                        # Multiple outputs
                        for key, values in indicator_values.items():
                            result[f"{var_name}_{key}"] = values
                    else:
                        # Single output
                        result[var_name] = indicator_values
                        
                except Exception as e:
                    self.logger.error(f"Error processing indicator {idx} ({config.get('indicator', 'unknown')}): {str(e)}")
                    raise ValueError(f"Error processing indicator {config.get('indicator', 'unknown')}: {str(e)}")
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error adding indicators: {str(e)}")
            raise

    def _normalize_dataframe_columns(self, df):
        """
        Normalize DataFrame column names to ensure compatibility with indicators
        
        Args:
            df (pandas.DataFrame): DataFrame to normalize
        """
        # Check for and fix tuple column names
        if any(isinstance(col, tuple) for col in df.columns):
            self.logger.warning("DataFrame contains tuple column names. Converting to strings.")
            # Convert tuple columns to string columns
            new_columns = []
            for col in df.columns:
                if isinstance(col, tuple):
                    # For tuples like ('Close', 'RELIANCE.NS'), just use the first part
                    new_columns.append(col[0].lower())
                else:
                    new_columns.append(col)
            df.columns = new_columns
        
        # Make all column names lowercase for consistency
        df.columns = [col.lower() if isinstance(col, str) else str(col).lower() for col in df.columns]
        
        # Ensure standard columns are present
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                if col == 'close' and ('adj close' in df.columns or 'adjusted close' in df.columns):
                    which = 'adj close' if 'adj close' in df.columns else 'adjusted close'
                    self.logger.info(f"Using '{which}' column as 'close'")
                    df['close'] = df[which]
                elif col != 'volume':  # Volume can be zeros, but price columns should have values
                    self.logger.warning(f"Column '{col}' not found. Using 'close' column as fallback.")
                    if 'close' in df.columns:
                        df[col] = df['close']
                    else:
                        # Last resort - try to find any suitable price column
                        price_cols = [c for c in df.columns if any(x in c for x in ['close', 'price', 'last', 'value'])]
                        if price_cols:
                            self.logger.warning(f"No 'close' column found. Using '{price_cols[0]}' as price data.")
                            df[col] = df[price_cols[0]]
                        else:
                            self.logger.error(f"No suitable price column found to use as '{col}'")
                else:  # For volume
                    self.logger.warning(f"Column '{col}' not found. Using zeros.")
                    df[col] = 0
        
        return df

# Example usage:
if __name__ == "__main__":
    # Sample data
    data = pd.DataFrame({
        'open': [10, 11, 12, 11, 10],
        'high': [12, 13, 14, 13, 12],
        'low': [9, 10, 11, 10, 9],
        'close': [11, 12, 13, 12, 11],
        'volume': [100, 150, 200, 150, 100]
    })
    
    # Initialize indicators
    indicators = Indicators()
    
    # Get available indicators
    available_indicators = indicators.get_available_indicators()
    print(f"Number of available indicators: {len(available_indicators)}")
    
    # Calculate RSI
    rsi = indicators.calculate_indicator('RSI', data, {'timeperiod': 2})
    print("RSI:")
    print(rsi)
    
    # Calculate MACD
    macd = indicators.calculate_indicator('MACD', data, {'fastperiod': 2, 'slowperiod': 4, 'signalperiod': 2})
    print("\nMACD:")
    for key, values in macd.items():
        print(f"{key}:")
        print(values)
