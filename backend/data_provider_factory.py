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
            self.logger.info(f"Forcing data provider: {force_provider}")
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
                self.logger.warning(f"Unknown provider: {force_provider}, falling back to default (Yahoo Finance)")
        
        # Default to Yahoo Finance as per requirements
        self.logger.info("Using Yahoo Finance as default data provider")
        self._provider = YahooFinanceIntegration()
        self._provider_name = 'yahoo'
        return self._provider
    
    def get_provider_name(self):
        """Get the name of the current provider"""
        if self._provider_name is None:
            self.get_provider()  # This will set the provider name
        return self._provider_name
    
    def test_provider(self, provider_name):
        """
        Test if a specific provider works
        
        Args:
            provider_name (str): Provider to test ('kite' or 'yahoo')
            
        Returns:
            bool: True if the provider works, False otherwise
        """
        try:
            if provider_name.lower() == 'kite':
                provider = KiteIntegration()
                return provider.verify_token()
            elif provider_name.lower() == 'yahoo':
                provider = YahooFinanceIntegration()
                # Test with a commonly available symbol
                test_data = provider.get_historical_data(
                    "SPY", "1day", 
                    (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"), 
                    datetime.now().strftime("%Y-%m-%d")
                )
                return test_data is not None and not test_data.empty
            else:
                self.logger.warning(f"Unknown provider for testing: {provider_name}")
                return False
        except Exception as e:
            self.logger.error(f"Error testing provider {provider_name}: {str(e)}")
            return False

# Create a singleton instance
provider_factory = DataProviderFactory()

# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    provider = provider_factory.get_provider()
    print(f"Using provider: {provider_factory.get_provider_name()}")
