import os
import json
import time
import pandas as pd
import logging
from kiteconnect import KiteConnect
from datetime import datetime, timedelta
from data_provider import DataProvider

class KiteAuthError(Exception):
    """Custom exception for Kite authentication errors"""
    pass

class KiteIntegration(DataProvider):
    """Class to handle integration with Zerodha Kite API, implementing the DataProvider interface"""
    
    def __init__(self):
        """Initialize the Kite API integration"""
        super().__init__()
        
        # Load configuration from config file or use environment variables as fallback
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.api_key = None
        self.api_secret = None
        self._load_config()
        
        # Path to store the access token
        self.token_path = os.path.join(os.path.dirname(__file__), 'kite_token.json')
        
        # Initialize KiteConnect client
        self.kite = KiteConnect(api_key=self.api_key)
        
        # Initialize access token
        self.access_token = None
        
        # Try to load existing token
        self._load_token()
        
    def _load_config(self):
        """Load API key and secret from config file or environment variables"""
        try:
            # First try to load from config file
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    if 'kite' in config and 'api_key' in config['kite'] and 'api_secret' in config['kite']:
                        self.api_key = config['kite']['api_key']
                        self.api_secret = config['kite']['api_secret']
                        self.logger.info("Loaded Kite API credentials from config file")
                        return
                    else:
                        self.logger.warning("Config file exists but missing kite credentials")
            else:
                self.logger.info("No config file found at: " + self.config_path)
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
        
        # Fallback to environment variables
        self.api_key = os.environ.get('KITE_API_KEY', 'your_api_key')
        self.api_secret = os.environ.get('KITE_API_SECRET', 'your_api_secret')
        self.logger.info("Using Kite API credentials from environment variables")
    
    def _load_token(self):
        """Load access token from file if it exists and set it in the client"""
        try:
            if os.path.exists(self.token_path):
                with open(self.token_path, 'r') as f:
                    token_data = json.load(f)
                    
                # Check token expiry - Kite tokens are valid until 6 AM next day
                # Be conservative and consider it expired after 20 hours
                timestamp = token_data.get('timestamp', 0)
                expiry_time = timestamp + (20 * 60 * 60)  # 20 hours in seconds
                
                if time.time() < expiry_time:
                    self.access_token = token_data.get('access_token')
                    self.kite.set_access_token(self.access_token)
                    self.logger.info("Loaded valid access token from file")
                    return True
                else:
                    self.logger.info("Stored token has expired")
                    return False
            else:
                self.logger.info("No token file found")
                return False
        except Exception as e:
            self.logger.error(f"Error loading token: {str(e)}")
            return False
    
    def _save_token(self, access_token):
        """Save access token to file with timestamp"""
        try:
            token_data = {
                'access_token': access_token,
                'timestamp': time.time()
            }
            
            with open(self.token_path, 'w') as f:
                json.dump(token_data, f)
                
            self.logger.info("Saved access token to file")
            return True
        except Exception as e:
            self.logger.error(f"Error saving token: {str(e)}")
            return False
    
    def check_token_validity(self):
        """
        Check if token is valid by making a lightweight API call
        Returns True if valid, False otherwise
        """
        if not self.access_token:
            self.logger.info("No access token available")
            return False
            
        try:
            # Try to get user profile - a lightweight call
            self.kite.profile()
            self.logger.info("Token validation successful")
            return True
        except Exception as e:
            error_str = str(e).lower()
            
            # Log specific error details for debugging
            if 'token' in error_str or 'authentication' in error_str or 'login' in error_str:
                self.logger.warning(f"Authentication error: {str(e)}")
            else:
                self.logger.error(f"API error during token validation: {str(e)}")
                
            return False
    
    def authenticate(self, request_token=None):
        """
        Authenticate with the Kite API using request token or stored access token
        Returns True if authentication is successful, False otherwise
        """
        try:
            if request_token:
                # Generate session from request token
                self.logger.info("Authenticating with request token")
                try:
                    data = self.kite.generate_session(request_token, self.api_secret)
                    self.access_token = data["access_token"]
                    self.kite.set_access_token(self.access_token)
                    
                    # Save token with timestamp
                    self._save_token(self.access_token)
                    
                    self.logger.info("Authentication successful with new request token")
                    return True
                except Exception as e:
                    error_msg = str(e)
                    if 'invalid' in error_msg.lower() and 'token' in error_msg.lower():
                        self.logger.error(f"Invalid request token: {error_msg}")
                        raise KiteAuthError(f"Invalid request token: {error_msg}")
                    else:
                        self.logger.error(f"Session generation failed: {error_msg}")
                        raise KiteAuthError(f"Session generation failed: {error_msg}")
            elif self.access_token:
                # We already have a token, validate it with API call
                self.logger.info("Using existing access token")
                self.kite.set_access_token(self.access_token)
                
                if self.check_token_validity():
                    return True
                else:
                    self.logger.warning("Existing token is invalid")
                    self.access_token = None  # Clear invalid token
                    return False
            else:
                self.logger.info("No token available for authentication")
                return False
        except KiteAuthError as e:
            # Re-raise custom auth errors
            raise
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            raise KiteAuthError(f"Authentication error: {str(e)}")
    
    def get_login_url(self):
        """Get the login URL for Kite Connect with current timestamp to prevent caching"""
        base_url = self.kite.login_url()
        # Add timestamp to prevent caching issues
        timestamp = int(time.time())
        return f"{base_url}&timestamp={timestamp}"
    
    def get_instruments(self):
        """Get list of instruments available for trading"""
        try:
            return self.kite.instruments()
        except Exception as e:
            error_str = str(e).lower()
            if ('authentication' in error_str or 'login' in error_str or 
                'token' in error_str or '401' in error_str or '403' in error_str):
                self.logger.error(f"Authentication error in get_instruments: {str(e)}")
                self.access_token = None  # Clear invalid token
                raise KiteAuthError("Authentication failed. Please log in again.")
            self.logger.error(f"Failed to get instruments: {str(e)}")
            return []
    
    def get_historical_data(self, symbol, timeframe, start_date, end_date):
        """
        Get historical OHLCV data for a symbol
        
        Args:
            symbol (str): Trading symbol (e.g., 'NIFTY 50', 'RELIANCE')
            timeframe (str): Timeframe ('minute', '15minute', 'hour', 'day')
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            
        Returns:
            pandas.DataFrame: DataFrame with OHLCV data
        """
        try:
            # Convert timeframe to Kite format
            interval_mapping = {
                '1minute': 'minute',
                '5minute': '5minute',
                '15minute': '15minute',
                '30minute': '30minute',
                '60minute': 'hour',
                '1hour': 'hour',
                'day': 'day',
                '1day': 'day'
            }
            
            kite_interval = interval_mapping.get(timeframe, timeframe)
            
            # Convert dates to datetime objects
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Get instrument token for the symbol
            instruments = self.kite.instruments()
            instrument_token = None
            
            for instrument in instruments:
                if instrument['tradingsymbol'] == symbol:
                    instrument_token = instrument['instrument_token']
                    break
            
            if not instrument_token:
                raise ValueError(f"Instrument token not found for symbol {symbol}")
            
            # For intervals less than a day, Kite API has a limit on the date range
            # We need to make multiple requests for longer periods
            if kite_interval in ['minute', '5minute', '15minute', '30minute', 'hour']:
                # Maximum date range is 60 days for intraday data
                max_days = 60
                date_chunks = []
                current_date = start_date_obj
                
                while current_date < end_date_obj:
                    chunk_end = min(current_date + timedelta(days=max_days), end_date_obj)
                    date_chunks.append((current_date, chunk_end))
                    current_date = chunk_end + timedelta(days=1)
                
                # Get data for each chunk and concatenate
                all_data = []
                for chunk_start, chunk_end in date_chunks:
                    chunk_data = self.kite.historical_data(
                        instrument_token,
                        from_date=chunk_start.strftime('%Y-%m-%d'),
                        to_date=chunk_end.strftime('%Y-%m-%d'),
                        interval=kite_interval
                    )
                    all_data.extend(chunk_data)
            else:
                # For daily data, we can make a single request
                all_data = self.kite.historical_data(
                    instrument_token,
                    from_date=start_date,
                    to_date=end_date,
                    interval=kite_interval
                )
            
            # Convert to DataFrame
            df = pd.DataFrame(all_data)
            
            # Rename columns to standard OHLCV format
            df.rename(columns={
                'date': 'datetime',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }, inplace=True)
            
            # Set datetime as index
            df.set_index('datetime', inplace=True)
            
            return df
        
        except Exception as e:
            error_str = str(e).lower()
            if ('authentication' in error_str or 'login' in error_str or 
                'token' in error_str or '401' in error_str or '403' in error_str):
                self.logger.error(f"Authentication error in get_historical_data: {str(e)}")
                self.access_token = None  # Clear invalid token
                raise KiteAuthError("Authentication failed. Please log in again.")
            self.logger.error(f"Failed to get historical data: {str(e)}")
            raise
    
    def get_quote(self, symbol):
        """Get current market quote for a symbol"""
        try:
            # Get instrument token for the symbol
            instruments = self.kite.instruments()
            instrument_token = None
            
            for instrument in instruments:
                if instrument['tradingsymbol'] == symbol:
                    instrument_token = instrument['instrument_token']
                    break
            
            if not instrument_token:
                raise ValueError(f"Instrument token not found for symbol {symbol}")
            
            # Get quote
            return self.kite.quote(instrument_token)
        
        except Exception as e:
            error_str = str(e).lower()
            if ('authentication' in error_str or 'login' in error_str or 
                'token' in error_str or '401' in error_str or '403' in error_str):
                self.logger.error(f"Authentication error in get_quote: {str(e)}")
                self.access_token = None  # Clear invalid token
                raise KiteAuthError("Authentication failed. Please log in again.")
            self.logger.error(f"Failed to get quote: {str(e)}")
            raise

    def is_using_placeholders(self):
        """Check if using placeholder credentials"""
        return self.api_key == "your_api_key" or self.api_secret == "your_api_secret"

# Example usage:
if __name__ == "__main__":
    kite = KiteIntegration()
    # Note: This won't work until you authenticate with a request token
    # print(kite.get_login_url())
    print(f"Using placeholders: {kite.is_using_placeholders()}")
