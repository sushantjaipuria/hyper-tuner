import pandas as pd
import logging
from kiteconnect import KiteConnect
from datetime import datetime, timedelta
from data_provider import DataProvider
from config import load_kite_config, save_kite_config, update_kite_access_token

class KiteIntegration(DataProvider):
    """Class to handle integration with Zerodha Kite API, implementing the DataProvider interface"""
    
    def __init__(self):
        """Initialize the Kite API integration"""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Load configuration from file
        self.config = load_kite_config()
        self.api_key = self.config.get("api_key", "")
        self.api_secret = self.config.get("api_secret", "")
        self.access_token = self.config.get("access_token", "")
        
        # Initialize KiteConnect client (not authenticated yet)
        self.kite = KiteConnect(api_key=self.api_key)
        
        # Set access token if available
        if self.access_token:
            self.logger.info("Setting access token from configuration")
            try:
                self.kite.set_access_token(self.access_token)
            except Exception as e:
                self.logger.error(f"Failed to set access token: {str(e)}")
    
    def authenticate(self, request_token=None):
        """Authenticate with the Kite API using request token or stored access token"""
        try:
            if request_token:
                # Generate access token using request token
                self.logger.info(f"Authenticating with request token: {request_token[:5] if request_token else ''}...")
                data = self.kite.generate_session(request_token, self.api_secret)
                self.access_token = data["access_token"]
                self.kite.set_access_token(self.access_token)
                
                # Save access token to configuration
                self.logger.info("Saving new access token to configuration")
                update_kite_access_token(self.access_token)
                
                return True
            elif self.access_token:
                # Use stored access token
                self.logger.info(f"Using stored access token: {self.access_token[:5] if self.access_token else ''}...")
                self.kite.set_access_token(self.access_token)
                return True
            else:
                self.logger.error("No request token or access token available")
                return False
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            return False
    
    def verify_token(self):
        """Verify if the access token is valid by making a lightweight API call"""
        try:
            self.logger.info("Verifying Kite API token validity")
            # Get user profile - lightweight API call
            user_profile = self.kite.profile()
            self.logger.info(f"Token verified successfully. User: {user_profile.get('user_name', 'Unknown')}")
            return True
        except Exception as e:
            self.logger.error(f"Token verification failed: {str(e)}")
            return False
    
    def get_login_url(self):
        """Get the login URL for Kite Connect"""
        return self.kite.login_url()
    
    def get_instruments(self):
        """Get list of instruments available for trading"""
        try:
            return self.kite.instruments()
        except Exception as e:
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
            self.logger.error(f"Failed to get quote: {str(e)}")
            raise

    def is_using_placeholders(self):
        """Check if using placeholder credentials"""
        return not self.api_key or not self.api_secret or self.api_key == "your_api_key" or self.api_secret == "your_api_secret"

# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    kite = KiteIntegration()
    print(f"Using placeholders: {kite.is_using_placeholders()}")
    print(f"Login URL: {kite.get_login_url()}")
