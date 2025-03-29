
import abc
import logging
from datetime import datetime
import pandas as pd

class DataProvider(abc.ABC):
    """
    Abstract base class for data providers.
    All market data providers must implement this interface.
    """
    
    def __init__(self):
        """Initialize the data provider"""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abc.abstractmethod
    def authenticate(self):
        """
        Authenticate with the data provider
        
        Returns:
            bool: True if authentication is successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def get_historical_data(self, symbol, timeframe, start_date, end_date):
        """
        Get historical OHLCV data for a symbol
        
        Args:
            symbol (str): Trading symbol (e.g., 'NIFTY 50', 'RELIANCE')
            timeframe (str): Timeframe ('1minute', '5minute', '15minute', '30minute', '60minute', 'day')
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            
        Returns:
            pandas.DataFrame: DataFrame with OHLCV data
        """
        pass
    
    @abc.abstractmethod
    def get_instruments(self):
        """
        Get list of instruments available for trading
        
        Returns:
            list: List of instruments
        """
        pass
    
    @abc.abstractmethod
    def get_quote(self, symbol):
        """
        Get current market quote for a symbol
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            dict: Quote data
        """
        pass
    
    def is_using_placeholders(self):
        """
        Check if the data provider is using placeholder credentials
        
        Returns:
            bool: True if using placeholders, False otherwise
        """
        return False
    
    def normalize_symbol(self, symbol, direction="to_provider"):
        """
        Normalize symbol between internal format and provider-specific format
        
        Args:
            symbol (str): Symbol to normalize
            direction (str): Direction of normalization ('to_provider' or 'from_provider')
            
        Returns:
            str: Normalized symbol
        """
        return symbol
    
    def standardize_timeframe(self, timeframe):
        """
        Standardize timeframe to provider-specific format
        
        Args:
            timeframe (str): Timeframe in standard format ('1minute', '5minute', '15minute', '30minute', '60minute', 'day')
            
        Returns:
            str: Timeframe in provider-specific format
        """
        return timeframe
    
    def standardize_ohlcv_data(self, data):
        """
        Standardize OHLCV data to a common format
        
        Args:
            data (pandas.DataFrame): Provider-specific OHLCV data
            
        Returns:
            pandas.DataFrame: Standardized OHLCV data with columns ['datetime', 'open', 'high', 'low', 'close', 'volume']
        """
        return data
