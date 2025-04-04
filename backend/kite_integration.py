import pandas as pd
import logging
import os
import json
from kiteconnect import KiteConnect
from datetime import datetime, timedelta
from data_provider import DataProvider
from config import load_kite_config, save_kite_config, update_kite_access_token, DEFAULT_KITE_USER

class KiteIntegration(DataProvider):
    """Class to handle integration with Zerodha Kite API, implementing the DataProvider interface"""
    
    def __init__(self, user_id=DEFAULT_KITE_USER):
        """
        Initialize the Kite API integration for a specific user
        
        Args:
            user_id (str): User identifier (default: "satyam")
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_id = user_id
        
        # Load configuration from file
        self.config = load_kite_config(user_id)
        self.api_key = self.config.get("api_key", "")
        self.api_secret = self.config.get("api_secret", "")
        self.access_token = self.config.get("access_token", "")
        
        # Initialize KiteConnect client (not authenticated yet)
        self.kite = KiteConnect(api_key=self.api_key)
        
        # Set access token if available
        if self.access_token:
            self.logger.info(f"Setting access token from configuration for user '{user_id}'")
            try:
                self.kite.set_access_token(self.access_token)
            except Exception as e:
                self.logger.error(f"Failed to set access token for user '{user_id}': {str(e)}")
    
    def authenticate(self, request_token=None):
        """Authenticate with the Kite API using request token or stored access token"""
        try:
            if request_token:
                # Generate access token using request token
                self.logger.info(f"Authenticating user '{self.user_id}' with request token: {request_token[:5] if request_token else ''}...")
                data = self.kite.generate_session(request_token, self.api_secret)
                self.access_token = data["access_token"]
                self.kite.set_access_token(self.access_token)
                
                # Save access token to configuration
                self.logger.info(f"Saving new access token for user '{self.user_id}' to configuration")
                update_kite_access_token(self.access_token, self.user_id)
                
                return True
            elif self.access_token:
                # Use stored access token
                self.logger.info(f"Using stored access token for user '{self.user_id}': {self.access_token[:5] if self.access_token else ''}...")
                self.kite.set_access_token(self.access_token)
                return True
            else:
                self.logger.error(f"No request token or access token available for user '{self.user_id}'")
                return False
        except Exception as e:
            self.logger.error(f"Authentication failed for user '{self.user_id}': {str(e)}")
            return False
    
    def verify_token(self):
        """Verify if the access token is valid by making a lightweight API call"""
        try:
            self.logger.info(f"Verifying Kite API token validity for user '{self.user_id}'")
            # Get user profile - lightweight API call
            user_profile = self.kite.profile()
            self.logger.info(f"Token verified successfully for user '{self.user_id}'. Kite username: {user_profile.get('user_name', 'Unknown')}")
            return True
        except Exception as e:
            self.logger.error(f"Token verification failed for user '{self.user_id}': {str(e)}")
            return False
    
    def get_login_url(self):
        """Get the login URL for Kite Connect"""
        # Base login URL
        base_url = self.kite.login_url()
        
        # Optionally add user_id as a query parameter to help with callback routing
        # This isn't used by Kite but will be passed back to our callback
        return f"{base_url}&kite_user_id={self.user_id}"
    
    def get_instruments(self):
        """Get list of instruments available for trading"""
        try:
            return self.kite.instruments()
        except Exception as e:
            self.logger.error(f"Failed to get instruments for user '{self.user_id}': {str(e)}")
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
            
            # Add market hours time components for Kite API format
            # Indian market opens at 09:15 and closes at 15:15
            start_date_time = start_date_obj.strftime('%Y-%m-%d') + ' 09:15:00'  # Market open time
            end_date_time = end_date_obj.strftime('%Y-%m-%d') + ' 15:15:00'  # Market close time
            
            self.logger.info(f"KITE DATE FORMAT: Converting dates from {start_date}/{end_date} to {start_date_time}/{end_date_time}")
            
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
                debug_responses = []  # Store individual API responses for debugging
                
                for chunk_start, chunk_end in date_chunks:
                    # Format dates with market hours (09:15 for start, 15:15 for end)
                    chunk_start_str = chunk_start.strftime('%Y-%m-%d') + ' 09:15:00'  # Market open time
                    chunk_end_str = chunk_end.strftime('%Y-%m-%d') + ' 15:15:00'    # Market close time
                    
                    self.logger.info(f"KITE API REQUEST: Requesting data for {symbol} from {chunk_start_str} to {chunk_end_str}")
                    
                    chunk_data = self.kite.historical_data(
                        instrument_token,
                        from_date=chunk_start_str,
                        to_date=chunk_end_str,
                        interval=kite_interval
                    )
                    
                    # Store response details for debugging
                    debug_responses.append({
                        "request": {
                            "from_date": chunk_start_str,
                            "to_date": chunk_end_str,
                            "interval": kite_interval,
                            "original_date_range": f"{chunk_start.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}"
                        },
                        "response_info": {
                            "data_points": len(chunk_data),
                            "first_date": chunk_data[0]["date"] if chunk_data else None,
                            "last_date": chunk_data[-1]["date"] if chunk_data else None
                        },
                        "response_data": chunk_data  # Store actual response
                    })
                    
                    all_data.extend(chunk_data)
            else:
                # For daily data, we can make a single request
                debug_responses = []  # Initialize debug responses array
                
                self.logger.info(f"KITE API REQUEST: Requesting data for {symbol} from {start_date_time} to {end_date_time}")
                
                all_data = self.kite.historical_data(
                    instrument_token,
                    from_date=start_date_time,
                    to_date=end_date_time,
                    interval=kite_interval
                )
                
                # Store response details for debugging
                debug_responses.append({
                    "request": {
                        "from_date": start_date_time,
                        "to_date": end_date_time,
                        "interval": kite_interval,
                        "original_date_range": f"{start_date} to {end_date}"
                    },
                    "response_info": {
                        "data_points": len(all_data),
                        "first_date": all_data[0]["date"] if all_data else None,
                        "last_date": all_data[-1]["date"] if all_data else None
                    },
                    "response_data": all_data  # Store actual response
                })
                
            # Create debug directory if it doesn't exist
            debug_dir = os.path.join(os.path.dirname(__file__), 'debug')
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
                
            # Save raw API responses to JSON file
            sanitized_symbol = ''.join(c if c.isalnum() else '_' for c in symbol)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = os.path.join(debug_dir, f"kite_raw_response_{sanitized_symbol}_{start_date}_to_{end_date}.json")
            
            with open(debug_file, 'w') as f:
                json.dump({
                    "request_details": {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "start_date": start_date,
                        "end_date": end_date,
                        "kite_interval": kite_interval,
                        "formatted_start_date": start_date_time,
                        "formatted_end_date": end_date_time
                    },
                    "responses": debug_responses
                }, f, indent=2, default=str)  # Use default=str to handle datetime objects
                
            self.logger.info(f"KITE API DEBUG: Raw API responses saved to {debug_file}")
            
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
            
            # Debug: Log actual date range
            if not df.empty:
                actual_start = df.index.min().strftime('%Y-%m-%d %H:%M:%S') if hasattr(df.index.min(), 'strftime') else str(df.index.min())
                actual_end = df.index.max().strftime('%Y-%m-%d %H:%M:%S') if hasattr(df.index.max(), 'strftime') else str(df.index.max())
                self.logger.info(f"KITE DATA RANGE: Requested period from {start_date} to {end_date}")
                self.logger.info(f"KITE DATA RANGE: With time components, requested {start_date_time} to {end_date_time}")
                self.logger.info(f"KITE DATA RANGE: Actual data received from {actual_start} to {actual_end}")
                
                # Calculate expected vs actual data points for debugging
                if timeframe in ['minute', '5minute', '15minute', '30minute', 'hour']:
                    self.logger.info(f"KITE DATA STATS: Received {len(df)} data points for {symbol} with {timeframe} timeframe")
            
            return df
        
        except Exception as e:
            self.logger.error(f"Failed to get historical data for user '{self.user_id}': {str(e)}")
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
            self.logger.error(f"Failed to get quote for user '{self.user_id}': {str(e)}")
            raise

    def is_using_placeholders(self):
        """Check if using placeholder credentials"""
        return not self.api_key or not self.api_secret or self.api_key == "your_api_key" or self.api_secret == "your_api_secret"
    
    def get_user_info(self):
        """Get information about the current user"""
        return {
            "user_id": self.user_id,
            "display_name": f"Kite-{self.user_id.capitalize()}",
            "is_using_placeholders": self.is_using_placeholders()
        }

# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    kite = KiteIntegration(user_id="satyam")
    print(f"User info: {kite.get_user_info()}")
    print(f"Using placeholders: {kite.is_using_placeholders()}")
    print(f"Login URL: {kite.get_login_url()}")