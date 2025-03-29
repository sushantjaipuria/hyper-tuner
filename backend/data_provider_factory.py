
import logging
from datetime import datetime, timedelta
from kite_integration import KiteIntegration
from yahoo_finance_integration import YahooFinanceIntegration

class DataProviderFactory:
    """Factory class for creating data providers"""
    
    def __init__(self):
        """Initialize the factory"""
        self.logger = logging.getLogger(__name__)
        self._provider = None
        self._provider_name = None
    
    def get_provider(self, force_provider=None):
        """
        Get the appropriate data provider
        
        Args:
            force_provider (str, optional): Force a specific provider ('kite' or 'yahoo')
            
        Returns:
            DataProvider: An instance of DataProvider
        """
        # If we already have a provider and aren't forcing a change, return it
        if self._provider is not None and force_provider is None:
            return self._provider
        
        # If forcing a specific provider
        if force_provider is not None:
            if force_provider.lower() == 'kite':
                self._provider = KiteIntegration()
                self._provider_name = 'kite'
                self.logger.info("Using Zerodha Kite data provider (forced)")
                return self._provider
            elif force_provider.lower() == 'yahoo':
                self._provider = YahooFinanceIntegration()
                self._provider_name = 'yahoo'
                self.logger.info("Using Yahoo Finance data provider (forced)")
                return self._provider
            else:
                self.logger.warning(f"Unknown provider: {force_provider}, falling back to auto-selection")
        
        # Try Kite first
        kite = KiteIntegration()
        
        # If using placeholders, switch to Yahoo Finance
        if kite.is_using_placeholders():
            self.logger.info("Detected Kite API placeholder credentials, using Yahoo Finance")
            try:
                yahoo = YahooFinanceIntegration()
                # Verify Yahoo Finance is working by getting some test data
                test_data = yahoo.get_historical_data("NIFTY 50", "1day", 
                                                  (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"), 
                                                  datetime.now().strftime("%Y-%m-%d"))
                if test_data is not None and not test_data.empty:
                    self.logger.info("Successfully connected to Yahoo Finance")
                    self._provider = yahoo
                    self._provider_name = 'yahoo'
                    return self._provider
                else:
                    self.logger.warning("Yahoo Finance returned empty data, will try Kite anyway")
            except Exception as e:
                self.logger.warning(f"Error initializing Yahoo Finance: {str(e)}")
                self.logger.warning("Will try Kite API even with placeholder credentials")
        
        # Try authenticating with Kite
        try:
            if kite.authenticate():
                self.logger.info("Successfully authenticated with Kite API")
                self._provider = kite
                self._provider_name = 'kite'
                return self._provider
        except Exception as e:
            self.logger.warning(f"Failed to authenticate with Kite API: {str(e)}")
        
        # Fall back to Yahoo Finance with better error handling
        self.logger.info("Falling back to Yahoo Finance data provider")
        try:
            yahoo = YahooFinanceIntegration()
            # Test connection with a US symbol first (more reliable)
            self.logger.info("Testing Yahoo Finance connection with a US symbol...")
            try:
                # SPY is a widely traded ETF that should be available
                test_data = yahoo.get_historical_data("SPY", "1day", 
                                                  (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"), 
                                                  datetime.now().strftime("%Y-%m-%d"))
                if test_data is not None and not test_data.empty:
                    self.logger.info("Successfully connected to Yahoo Finance with US symbol")
                    self._provider = yahoo
                    self._provider_name = 'yahoo'
                    return self._provider
            except Exception as e:
                self.logger.warning(f"Failed to get US symbol data from Yahoo Finance: {str(e)}")
            
            # Try with an Indian symbol
            self.logger.info("Testing Yahoo Finance connection with an Indian symbol...")
            try:
                test_data = yahoo.get_historical_data("NIFTY 50", "1day", 
                                                  (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"), 
                                                  datetime.now().strftime("%Y-%m-%d"))
                if test_data is not None and not test_data.empty:
                    self.logger.info("Successfully connected to Yahoo Finance with Indian symbol")
                    self._provider = yahoo
                    self._provider_name = 'yahoo'
                    return self._provider
                else:
                    self.logger.warning("Yahoo Finance returned empty data for Indian symbol")
            except Exception as e:
                self.logger.warning(f"Failed to get Indian symbol data from Yahoo Finance: {str(e)}")
                
            # Last resort: try with RELIANCE which is a major Indian stock
            self.logger.info("Trying one more time with RELIANCE stock...")
            try:
                test_data = yahoo.get_historical_data("RELIANCE", "1day", 
                                                  (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"), 
                                                  datetime.now().strftime("%Y-%m-%d"))
                if test_data is not None and not test_data.empty:
                    self.logger.info("Successfully connected to Yahoo Finance with RELIANCE")
                    self._provider = yahoo
                    self._provider_name = 'yahoo'
                    return self._provider
                else:
                    raise ValueError("Yahoo Finance returned empty data for all test symbols")
            except Exception as e:
                self.logger.error(f"Final test failed: {str(e)}")
                raise
                
        except Exception as e:
            import traceback
            self.logger.error(f"Failed to initialize Yahoo Finance: {str(e)}")
            self.logger.debug(f"Error traceback: {traceback.format_exc()}")
            self.logger.error("Both data providers failed. The application may not work correctly.")
            # As a last resort, still return Yahoo but log the error
            self.logger.warning("Using Yahoo Finance provider despite initialization failure")
            self._provider = YahooFinanceIntegration()
            self._provider_name = 'yahoo'
            return self._provider
    
    def get_provider_name(self):
        """Get the name of the current provider"""
        if self._provider_name is None:
            self.get_provider()  # This will set the provider name
        return self._provider_name

# Create a singleton instance
provider_factory = DataProviderFactory()

# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    provider = provider_factory.get_provider()
    print(f"Using provider: {provider_factory.get_provider_name()}")
