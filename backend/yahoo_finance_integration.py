
import pandas as pd
import yfinance as yf
import logging
from datetime import datetime, timedelta
from data_provider import DataProvider

class YahooFinanceIntegration(DataProvider):
    """Class to handle integration with Yahoo Finance API, implementing the DataProvider interface"""
    
    def __init__(self):
        """Initialize the Yahoo Finance API integration"""
        super().__init__()
        
        # Define a mapping from Zerodha symbols to Yahoo Finance symbols
        self.symbol_mapping = {
            # Indian Indices
            "NIFTY 50": "^NSEI",
            "NIFTY50": "^NSEI",
            "NIFTY": "^NSEI",
            "BANKNIFTY": "^NSEBANK",
            "SENSEX": "^BSESN",
            
            # Indian Stocks - Add more as needed
            "RELIANCE": "RELIANCE.NS",
            "TCS": "TCS.NS",
            "INFY": "INFY.NS",
            "HDFCBANK": "HDFCBANK.NS",
            "ICICIBANK": "ICICIBANK.NS",
            "KOTAKBANK": "KOTAKBANK.NS",
            
            # US Markets 
            "SPY": "SPY",
            "QQQ": "QQQ",
            "AAPL": "AAPL",
            "MSFT": "MSFT",
            "GOOGL": "GOOGL",
            "AMZN": "AMZN",
            
            # Fallback - use as is with NS suffix for NSE symbols
            "_DEFAULT_NSE_": "{}.NS",
            "_DEFAULT_BSE_": "{}.BO"
        }
        
        # Define a mapping from standard timeframes to Yahoo Finance intervals
        self.timeframe_mapping = {
            "1minute": "1m",
            "2minute": "2m",
            "5minute": "5m",
            "15minute": "15m",
            "30minute": "30m",
            "60minute": "60m",
            "1hour": "1h",
            "1day": "1d",
            "day": "1d",
            "1week": "1wk",
            "week": "1wk",
            "1month": "1mo",
            "month": "1mo"
        }
        
        # Verify yfinance is working properly
        try:
            # Test access to Yahoo Finance API
            import yfinance as yf
            # Check version
            self.logger.info(f"Using yfinance version: {yf.__version__ if hasattr(yf, '__version__') else 'unknown'}")
            # Test with a well-known symbol
            test = yf.download("SPY", period="1d")
            self.logger.debug(f"Test download successful: {not test.empty}")
        except Exception as e:
            self.logger.warning(f"Error initializing yfinance: {str(e)}")
            self.logger.warning("Yahoo Finance integration may not work properly")
            # Continue anyway - we'll handle errors during specific method calls
    
    def authenticate(self):
        """
        Yahoo Finance doesn't require authentication
        
        Returns:
            bool: Always True
        """
        self.logger.info("Yahoo Finance integration doesn't require authentication")
        return True
    
    def normalize_symbol(self, symbol, direction="to_provider"):
        """
        Convert between internal symbol format and Yahoo Finance format
        
        Args:
            symbol (str): Symbol to convert
            direction (str): 'to_provider' for internal to Yahoo, 'from_provider' for Yahoo to internal
            
        Returns:
            str: Converted symbol
        """
        # Guard against None or non-string inputs
        if symbol is None:
            self.logger.warning("Received None as symbol, using a default symbol")
            return "SPY"  # Default to a well-known symbol that should always work
        
        # Ensure symbol is a string
        if not isinstance(symbol, str):
            self.logger.warning(f"Symbol is not a string: {type(symbol)}, attempting to convert")
            try:
                symbol = str(symbol)
            except Exception as e:
                self.logger.error(f"Could not convert symbol to string: {e}")
                return "SPY"  # Default to a well-known symbol
        
        # Remove any whitespace
        symbol = symbol.strip()
        
        if direction == "to_provider":
            # Convert from internal format to Yahoo Finance format
            if symbol in self.symbol_mapping:
                return self.symbol_mapping[symbol]
            
            # Handle some common symbol formats
            # Check if it's already in Yahoo Finance format (contains a dot)
            if "." in symbol and not symbol.startswith("."):
                self.logger.debug(f"Symbol {symbol} appears to be already in Yahoo Finance format")
                return symbol
            
            # Try to guess if it's an NSE symbol (for Indian markets)
            if symbol.isupper() and not symbol.startswith("^"):
                yf_symbol = self.symbol_mapping["_DEFAULT_NSE_"].format(symbol)
                self.logger.debug(f"Converting {symbol} to NSE format: {yf_symbol}")
                return yf_symbol
            
            # Use as is for other cases
            self.logger.debug(f"Using symbol as is: {symbol}")
            return symbol
        else:
            # Convert from Yahoo Finance format to internal format
            # This is more complex and would require a reverse mapping
            # For now, just strip the exchange suffix
            if symbol.endswith(".NS"):
                return symbol[:-3]
            elif symbol.endswith(".BO"):
                return symbol[:-3]
            elif symbol.startswith("^"):
                # Handle indices
                for internal_symbol, yf_symbol in self.symbol_mapping.items():
                    if yf_symbol == symbol:
                        return internal_symbol
            
            # If no mapping found, return as is
            return symbol
    
    def standardize_timeframe(self, timeframe):
        """
        Convert standard timeframe to Yahoo Finance interval
        
        Args:
            timeframe (str): Standard timeframe
            
        Returns:
            str: Yahoo Finance interval
        """
        # Guard against None inputs
        if timeframe is None:
            self.logger.warning("Received None as timeframe, using default daily timeframe")
            return "1d"
        
        # Handle non-string inputs
        if not isinstance(timeframe, str):
            self.logger.warning(f"Timeframe is not a string: {type(timeframe)}, attempting to convert")
            try:
                timeframe = str(timeframe)
            except Exception as e:
                self.logger.error(f"Could not convert timeframe to string: {e}")
                return "1d"  # Default to daily
        
        # Normalize timeframe string
        timeframe = timeframe.lower().strip()  
        
        # Check for direct match in mapping
        if timeframe in self.timeframe_mapping:
            return self.timeframe_mapping[timeframe]
            
        # Try to interpret common formats
        # Handle cases like '1d', '5m', '1h' directly
        if len(timeframe) >= 2 and timeframe[-1] in ['m', 'h', 'd']:
            # Extract the number and unit
            try:
                number = int(timeframe[:-1])
                unit = timeframe[-1]
                
                # Map to known Yahoo Finance intervals
                if unit == 'm' and number in [1, 2, 5, 15, 30, 60, 90]:
                    return f"{number}m"
                elif unit == 'h' and number in [1, 2, 4, 6, 8]:
                    return f"{number}h"
                elif unit == 'd' and number == 1:
                    return "1d"
            except ValueError:
                pass  # Not a number format, continue to default
        
        # Special cases
        if 'min' in timeframe:
            # Handle formats like '5min', '30min'
            try:
                minutes = int(''.join(filter(str.isdigit, timeframe)))
                if minutes in [1, 2, 5, 15, 30, 60, 90]:
                    return f"{minutes}m"
            except ValueError:
                pass
        
        # Default to daily if no match found
        self.logger.warning(f"Unknown timeframe: {timeframe}, defaulting to daily")
        return "1d"  # Default to daily
    
    def get_historical_data(self, symbol, timeframe, start_date, end_date):
        """
        Get historical OHLCV data from Yahoo Finance
        
        Args:
            symbol (str): Trading symbol in internal format
            timeframe (str): Timeframe in standard format
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            
        Returns:
            pandas.DataFrame: DataFrame with OHLCV data
        """
        try:
            # Convert symbol to Yahoo Finance format
            yf_symbol = self.normalize_symbol(symbol, "to_provider")
            
            # Convert timeframe to Yahoo Finance interval
            interval = self.standardize_timeframe(timeframe)
            
            # Get historical data
            self.logger.info(f"Getting historical data for {yf_symbol} from {start_date} to {end_date} with interval {interval}")
            
            # Download data from Yahoo Finance with explicit parameters to prevent MultiIndex
            self.logger.info(f"Downloading data with multi_level_index=False and group_by='column' to prevent MultiIndex")
            df = yf.download(
                tickers=yf_symbol,
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=True,
                multi_level_index=False,  # Prevent multi-level indexing
                group_by='column',        # Group by column type instead of ticker
                actions=False             # No need for dividend/split data
            )
            
            # Log the DataFrame structure for debugging
            self.logger.debug(f"Downloaded DataFrame columns: {df.columns}")
            self.logger.debug(f"DataFrame has MultiIndex columns: {isinstance(df.columns, pd.MultiIndex)}")
            
            # Add debug logging
            self.logger.debug(f"Data type returned from yf.download: {type(df)}")
            self.logger.debug(f"Columns type: {type(df.columns)}")
            self.logger.debug(f"Columns: {df.columns}")
            
            # Explicitly handle MultiIndex if it still occurs (safety measure)
            if isinstance(df.columns, pd.MultiIndex):
                self.logger.warning("MultiIndex columns detected despite prevention parameters. Flattening columns...")
                # Create a flat column index with simple names
                new_columns = []
                for col in df.columns:
                    if isinstance(col, tuple):
                        # Just use the first level (e.g., 'Open', 'High', etc.)
                        new_columns.append(col[0])
                    else:
                        new_columns.append(col)
                
                # Set the new flat column names
                df.columns = new_columns
                self.logger.info(f"Flattened columns: {df.columns}")
            
            # Check if df is empty
            if df.empty:
                self.logger.warning(f"No data returned for {yf_symbol} from {start_date} to {end_date}")
                return pd.DataFrame()  # Return empty DataFrame
            
            # Standardize column names (convert to lowercase, ensure consistency)
            column_mapping = {
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Adj Close': 'adj_close'
            }
            
            # Create a standardized DataFrame with consistent column names
            std_df = pd.DataFrame(index=df.index)
            
            # At this point we should have flat column names, but double-check just in case
            if isinstance(df.columns, pd.MultiIndex):
                # This should not happen with our new parameters, but handle it just in case
                self.logger.warning(f"MultiIndex still detected despite prevention parameters. Converting to flat structure.")
                
                # Create a flat DataFrame with standard column names
                flat_df = pd.DataFrame(index=df.index)
                
                # For each standard column, try to extract it from the MultiIndex
                for col_name, std_name in column_mapping.items():
                    # Find matching columns in the MultiIndex that start with the column name
                    matching_cols = [c for c in df.columns if isinstance(c, tuple) and c[0] == col_name]
                    
                    if matching_cols:
                        # Use the first matching column
                        flat_df[std_name] = df[matching_cols[0]].values
                        self.logger.info(f"Extracted '{matching_cols[0]}' as '{std_name}'")
                
                # If we couldn't find the close price, use any available column
                if 'close' not in flat_df.columns and len(df.columns) > 0:
                    # For MultiIndex, find the first column that might be a price
                    price_cols = [c for c in df.columns if isinstance(c, tuple) and 
                                c[0] in ['Close', 'close', 'Adj Close', 'Price', 'price']]
                    
                    if price_cols:
                        col_to_use = price_cols[0]
                        self.logger.warning(f"Using '{col_to_use}' as 'close' price")
                        flat_df['close'] = df[col_to_use].values
                    else:
                        # Last resort: use the first column whatever it is
                        first_col = df.columns[0]
                        self.logger.warning(f"No price column found. Using '{first_col}' as 'close' data")
                        flat_df['close'] = df[first_col].values
                
                # Use our flat DataFrame
                std_df = flat_df
            else:
                # Regular DataFrame processing with simplified column mapping
                self.logger.info("Processing regular DataFrame with flat column structure")
                
                # Map columns using our standardized mapping
                for src_col, dst_col in column_mapping.items():
                    # Try original case (as in mapping)
                    if src_col in df.columns:
                        std_df[dst_col] = df[src_col]
                    # Try lowercase
                    elif src_col.lower() in df.columns:
                        std_df[dst_col] = df[src_col.lower()]
                
                # Special handling for close price - prioritize adjusted close if available
                if 'adj_close' in std_df.columns and 'close' not in std_df.columns:
                    self.logger.info("Using 'Adj Close' as 'close' price")
                    std_df['close'] = std_df['adj_close']
                
                # If we still don't have a close price, try to find any suitable column
                if 'close' not in std_df.columns and len(df.columns) > 0:
                    # Use the first available column as a last resort
                    first_col = df.columns[0]
                    self.logger.warning(f"Standard columns not found. Using '{first_col}' as 'close' data")
                    std_df['close'] = df[first_col].values
            
            # Use the standardized DataFrame for further processing
            df = std_df.copy()
            
            # Reset index to make datetime a column with more robust error handling
            try:
                df.reset_index(inplace=True)
                
                # Check what the datetime column is called
                if 'date' in df.columns:
                    df.rename(columns={'date': 'datetime'}, inplace=True)
                elif 'Date' in df.columns:
                    df.rename(columns={'Date': 'datetime'}, inplace=True)
                elif 'index' in df.columns and pd.api.types.is_datetime64_any_dtype(df['index']):
                    df.rename(columns={'index': 'datetime'}, inplace=True)
                else:
                    # If we can't find a datetime column, create one as a last resort
                    self.logger.warning(f"No datetime column found, creating one with current index")
                    df['datetime'] = pd.to_datetime(df.index)
                
                # Set datetime as index again
                df.set_index('datetime', inplace=True)
            except Exception as e:
                self.logger.error(f"Error processing datetime index: {str(e)}")
                # If we encounter an error, try to create a dataframe with the required columns
                # This is a last resort to not break the backtesting process
                self.logger.warning("Attempting to create a minimum viable dataframe")
                self.logger.debug(f"Current dataframe: {df.head()}")
            
            # Make sure we don't have any tuple values as column names
            # Convert all column names to strings
            df.columns = [str(col) if isinstance(col, tuple) else col for col in df.columns]
            
            # Ensure we have all required columns
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    # For 'close', we must have data
                    if col == 'close':
                        # This should rarely happen due to our earlier handling
                        if len(df.columns) > 0:
                            # Try to use another column for 'close' as a last resort
                            alt_col = df.columns[0]
                            self.logger.warning(f"Critical: 'close' column not found. Using '{alt_col}' as 'close' data.")
                            df['close'] = df[alt_col]
                        else:
                            self.logger.error(f"Critical error: No 'close' column available and no alternative data")
                            raise ValueError("Could not obtain price data for backtesting. Yahoo Finance integration failed.")
                    # For other columns like open, high, low - use close as a fallback
                    elif col in ['open', 'high', 'low'] and 'close' in df.columns:
                        self.logger.warning(f"Column '{col}' not found in data, using 'close' values instead")
                        df[col] = df['close']
                    else:
                        # For volume, just use zeros
                        self.logger.warning(f"Column '{col}' not found in data, adding with zeros")
                        df[col] = 0.0
            
            # Handle NaN values in volume (some symbols don't have volume data)
            if 'volume' in df.columns and df['volume'].isnull().any():
                df['volume'] = df['volume'].fillna(0)
            
            # Handle NaN values in other columns
            for col in df.columns:
                if df[col].isnull().any():
                    self.logger.warning(f"NaN values found in {col}, forward filling")
                    # For price columns, use forward/backward fill to handle gaps
                    if col in ['open', 'high', 'low', 'close']:
                        df[col] = df[col].fillna(method='ffill').fillna(method='bfill').fillna(0)
                    else:
                        # For non-price columns (like volume), just use zeros
                        df[col] = df[col].fillna(0)
            
            # Final verification: log column names and ensure all required columns are proper
            self.logger.info(f"Final DataFrame columns: {df.columns}")
            self.logger.info(f"Close column type: {type(df['close'])}")
            
            # Verify all columns are numerical (not objects or strings)
            for col in ['open', 'high', 'low', 'close']:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    self.logger.warning(f"Column '{col}' is not numeric: {df[col].dtype}. Converting to float.")
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Done - return the cleaned and verified DataFrame
            return df
        
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            self.logger.error(f"Failed to get historical data from Yahoo Finance: {str(e)}")
            self.logger.debug(f"Error traceback: {error_traceback}")
            self.logger.debug(f"Symbol: {yf_symbol}, Timeframe: {interval}, Start: {start_date}, End: {end_date}")
            
            # Create an empty DataFrame with the required structure as a fallback
            # This allows the backtesting process to continue with a warning instead of a fatal error
            self.logger.warning("Returning empty dataframe with required structure")
            empty_df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
            empty_df.index.name = 'datetime'
            
            # Re-raise the exception for proper error handling upstream
            raise ValueError(f"Failed to get historical data: {str(e)}") from e
    
    def get_instruments(self):
        """
        Get list of instruments available for trading
        Yahoo Finance doesn't provide a comprehensive list, so we return a limited set
        
        Returns:
            list: List of instruments
        """
        # Just return a subset of Indian instruments for demonstration
        instruments = []
        
        # Add indices
        for symbol in ["NIFTY 50", "BANKNIFTY", "SENSEX"]:
            yf_symbol = self.normalize_symbol(symbol, "to_provider")
            instruments.append({
                'instrument_token': hash(yf_symbol) % 10000000,  # Generate a dummy token
                'exchange_token': hash(yf_symbol) % 1000000,
                'tradingsymbol': symbol,
                'name': symbol,
                'last_price': 0,
                'expiry': '',
                'strike': 0,
                'tick_size': 0.05,
                'lot_size': 1,
                'instrument_type': 'EQ',
                'segment': 'NSE',
                'exchange': 'NSE'
            })
        
        # Add some stocks
        stocks = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "KOTAKBANK"]
        for symbol in stocks:
            yf_symbol = self.normalize_symbol(symbol, "to_provider")
            instruments.append({
                'instrument_token': hash(yf_symbol) % 10000000,
                'exchange_token': hash(yf_symbol) % 1000000,
                'tradingsymbol': symbol,
                'name': symbol,
                'last_price': 0,
                'expiry': '',
                'strike': 0,
                'tick_size': 0.05,
                'lot_size': 1,
                'instrument_type': 'EQ',
                'segment': 'NSE',
                'exchange': 'NSE'
            })
        
        return instruments
    
    def get_quote(self, symbol):
        """
        Get current market quote for a symbol
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            dict: Quote data
        """
        try:
            # Convert symbol to Yahoo Finance format
            yf_symbol = self.normalize_symbol(symbol, "to_provider")
            
            # Get ticker information
            ticker = yf.Ticker(yf_symbol)
            
            # Get quote information
            info = ticker.info
            
            # Create quote dictionary similar to Kite's format
            quote = {
                'instrument_token': hash(yf_symbol) % 10000000,
                'timestamp': datetime.now().isoformat(),
                'last_price': info.get('previousClose', 0),
                'last_quantity': 0,
                'average_price': info.get('regularMarketPreviousClose', 0),
                'volume': info.get('regularMarketVolume', 0),
                'buy_quantity': 0,
                'sell_quantity': 0,
                'ohlc': {
                    'open': info.get('regularMarketOpen', 0),
                    'high': info.get('regularMarketDayHigh', 0),
                    'low': info.get('regularMarketDayLow', 0),
                    'close': info.get('regularMarketPreviousClose', 0)
                }
            }
            
            return quote
        
        except Exception as e:
            self.logger.error(f"Failed to get quote from Yahoo Finance: {str(e)}")
            raise

# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    yahoo = YahooFinanceIntegration()
    print(yahoo.normalize_symbol("NIFTY 50", "to_provider"))  # Should print "^NSEI"
    
    # Get historical data for Nifty
    #data = yahoo.get_historical_data("NIFTY 50", "1day", "2023-01-01", "2023-01-31")
    #print(data.head())
