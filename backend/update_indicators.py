import os
import json

def update_indicators_file():
    """Update the indicators.py file with enhanced mappings"""
    print("Updating indicators.py with enhanced indicator mappings...")
    
    # Load indicator mappings
    try:
        with open('indicator_mappings.json', 'r') as f:
            mappings = json.load(f)
        print(f"Loaded {len(mappings)} indicators from mapping file")
    except Exception as e:
        print(f"Error loading mappings: {str(e)}")
        return
    
    # Read current indicators.py file
    try:
        with open('indicators.py', 'r') as f:
            content = f.read()
        print("Read indicators.py file")
    except Exception as e:
        print(f"Error reading indicators.py: {str(e)}")
        return
    
    # Add imports
    if "import json" not in content:
        content = content.replace(
            "import logging\nfrom talib import abstract",
            "import logging\nimport json\nimport os\nfrom talib import abstract"
        )
    
    # Add mappings loading in __init__
    if "_load_indicator_mappings" not in content:
        content = content.replace(
            "def __init__(self):\n        \"\"\"Initialize the Indicators class\"\"\"\n        self.logger = logging.getLogger(__name__)\n        \n        # Get all TA-Lib functions that are indicators\n        self.available_indicators = self._get_all_talib_indicators()",
            """def __init__(self):
        \"\"\"Initialize the Indicators class\"\"\"
        self.logger = logging.getLogger(__name__)
        
        # Load indicator mappings if available
        self.indicator_mappings = self._load_indicator_mappings()
        
        # Get all TA-Lib functions that are indicators
        self.available_indicators = self._get_all_talib_indicators()"""
        )
    
    # Add _load_indicator_mappings method
    if "def _load_indicator_mappings" not in content:
        load_mappings_method = """
    def _load_indicator_mappings(self):
        \"\"\"
        Load indicator mappings from JSON file
        
        Returns:
            dict: Dictionary of indicator mappings or empty dict if file not found
        \"\"\"
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
"""
        # Insert before get_available_indicators
        content = content.replace(
            "    def get_available_indicators(self):",
            load_mappings_method + "    def get_available_indicators(self):"
        )
    
    # Update get_available_indicators method
    content = content.replace(
        """    def get_available_indicators(self):
        \"\"\"
        Get list of available indicators
        
        Returns:
            dict: Dictionary of available indicators with their metadata
        \"\"\"
        result = {}
        for name, info in self.available_indicators.items():
            result[name] = {
                'description': info['description'],
                'category': info.get('category', 'Other'),
                'params': info['params']
            }
        return result""",
        """    def get_available_indicators(self):
        \"\"\"
        Get list of available indicators
        
        Returns:
            dict: Dictionary of available indicators with their metadata
        \"\"\"
        result = {}
        for name, info in self.available_indicators.items():
            result[name] = {
                'display_name': info.get('display_name', name),
                'description': info.get('description', ''),
                'category': info.get('category', 'Other'),
                'params': info['params'],
                'code_name': info.get('code_name', name)  # Original code for reference
            }
        return result"""
    )
    
    # Update description in _get_all_talib_indicators method
    content = content.replace(
        """# Descriptions for common indicators (can be expanded)
        descriptions = {
            'SMA': 'Simple Moving Average',
            'EMA': 'Exponential Moving Average',
            'WMA': 'Weighted Moving Average',
            'DEMA': 'Double Exponential Moving Average',
            'TEMA': 'Triple Exponential Moving Average',
            'TRIMA': 'Triangular Moving Average',
            'KAMA': 'Kaufman Adaptive Moving Average',
            'MAMA': 'MESA Adaptive Moving Average',
            'BBANDS': 'Bollinger Bands',
            'SAR': 'Parabolic SAR',
            'RSI': 'Relative Strength Index',
            'MACD': 'Moving Average Convergence/Divergence',
            'STOCH': 'Stochastic',
            'STOCHF': 'Stochastic Fast',
            'STOCHRSI': 'Stochastic Relative Strength Index',
            'ADX': 'Average Directional Movement Index',
            'ADXR': 'Average Directional Movement Index Rating',
            'CCI': 'Commodity Channel Index',
            'MOM': 'Momentum',
            'ROC': 'Rate of change',
            'OBV': 'On Balance Volume',
            'AD': 'Chaikin A/D Line',
            'ADOSC': 'Chaikin A/D Oscillator',
            'ATR': 'Average True Range',
            'NATR': 'Normalized Average True Range',
            'CDLENGULFING': 'Engulfing Pattern',
            'CDLDOJI': 'Doji',
            'CDLHAMMER': 'Hammer'
        }""",
        """# Use mappings from file if available, or fallback to built-in descriptions
        descriptions = {}
        for func_name in talib_functions:
            if func_name in self.indicator_mappings:
                descriptions[func_name] = self.indicator_mappings[func_name]['display_name']
            else:
                descriptions[func_name] = f"{func_name.replace('_', ' ').title()} Indicator\""""
    )
    
    # Update the add_to_indicators code
    content = content.replace(
        """                # Get description
                description = descriptions.get(func_name, f"{func_name.replace('_', ' ').title()} Indicator")""",
        """                # Get description and detailed description from mappings
                display_name = descriptions.get(func_name, f"{func_name.replace('_', ' ').title()} Indicator")
                detailed_description = ""
                if func_name in self.indicator_mappings:
                    detailed_description = self.indicator_mappings[func_name].get('description', '')"""
    )
    
    content = content.replace(
        """                # Add to indicators dictionary
                indicators[func_name] = {
                    'function': func,
                    'params': params,
                    'description': description,
                    'category': category
                }""",
        """                # Add to indicators dictionary
                indicators[func_name] = {
                    'function': func,
                    'params': params,
                    'display_name': display_name,
                    'description': detailed_description,
                    'category': category,
                    'code_name': func_name  # Original code name for reference
                }"""
    )
    
    # Update all indicators in _get_default_indicators method to include display_name, description, and code_name
    for indicator_code, mapping in mappings.items():
        # We'll update each indicator in the _get_default_indicators method
        indicator_block_pattern = f"'{indicator_code}': " + r"{[\s\S]*?'category': '[^']*'"
        if indicator_code in content:
            new_block = f"""'{indicator_code}': {{
                'function': talib.{indicator_code},
                'params': [[KEEP_PARAMS]],
                'display_name': '{mapping['display_name']}',
                'description': '{mapping['description']}',
                'category': '{mapping['category']}',
                'code_name': '{indicator_code}'
            }}"""
            
            # Find the params for this indicator
            import re
            params_pattern = f"'{indicator_code}':" + r"[\s\S]*?'params': (\[[^\]]*\])"
            params_match = re.search(params_pattern, content)
            if params_match:
                params = params_match.group(1)
                new_block = new_block.replace("[[KEEP_PARAMS]]", params.strip())
            else:
                new_block = new_block.replace("[[KEEP_PARAMS]]", "['value', 'timeperiod']")
            
            # Replace the old indicator block with the new one
            pattern = f"'{indicator_code}': " + r"{[\s\S]*?},"
            match = re.search(pattern, content)
            if match:
                old_block = match.group(0)
                content = content.replace(old_block, new_block + ",")
    
    # Write updated content back to indicators.py
    try:
        with open('indicators.py', 'w') as f:
            f.write(content)
        print("Updated indicators.py successfully!")
    except Exception as e:
        print(f"Error writing updated indicators.py: {str(e)}")

if __name__ == "__main__":
    update_indicators_file()
