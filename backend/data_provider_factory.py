import logging
from datetime import datetime, timedelta
from kite_integration import KiteIntegration, DEFAULT_KITE_USER
from yahoo_finance_integration import YahooFinanceIntegration

class DataProviderFactory:
    """Factory class for creating data providers"""
    
    def __init__(self):
        """Initialize the factory"""
        self.logger = logging.getLogger(__name__)
        self._provider = None
        self._provider_name = None
        self._provider_user = None  # Add tracking for user ID
    
    def get_provider(self, force_provider=None, user_id=None):
        """
        Get the appropriate data provider
        
        Args:
            force_provider (str, optional): Force a specific provider ('kite' or 'yahoo')
            user_id (str, optional): User identifier for Kite provider
            
        Returns:
            DataProvider: An instance of DataProvider
        """
        # Enhanced debugging for parameters
        self.logger.info(f"get_provider called with force_provider: '{force_provider}', user_id: '{user_id}' (type: {type(user_id).__name__})")
        
        # If forcing a specific provider
        if force_provider is not None:
            self.logger.info(f"Forcing data provider: {force_provider}" + 
                           (f" for user '{user_id}'" if user_id and force_provider.lower() == 'kite' else ""))
            
            if force_provider.lower() == 'kite':
                # For Kite provider, use the specified user ID (default to current user or "sushant")
                current_user = user_id or self._provider_user or DEFAULT_KITE_USER
                self.logger.info(f"Creating Kite provider with user_id: '{current_user}' (type: {type(current_user).__name__})")
                self.logger.info(f"Original user_id: '{user_id}' (type: {type(user_id).__name__}), _provider_user: '{self._provider_user}', DEFAULT: '{DEFAULT_KITE_USER}'")
                self._provider = KiteIntegration(user_id=current_user)
                self._provider_name = 'kite'
                self._provider_user = current_user
                self.logger.info(f"Using Zerodha Kite data provider for user '{current_user}' (forced)")
                return self._provider
            elif force_provider.lower() == 'yahoo':
                self._provider = YahooFinanceIntegration()
                self._provider_name = 'yahoo'
                self._provider_user = None  # Yahoo doesn't use user IDs
                self.logger.info("Using Yahoo Finance data provider (forced)")
                return self._provider
            elif force_provider.lower().startswith('kite-'):
                # Parse user ID from provider name (e.g., 'kite-satyam' -> 'satyam')
                current_user = force_provider.lower().split('-', 1)[1]
                self.logger.info(f"Extracted user '{current_user}' from provider name '{force_provider}'")
                self.logger.info(f"Extracted user_id type: {type(current_user).__name__}")
                self._provider = KiteIntegration(user_id=current_user)
                self._provider_name = 'kite'
                self._provider_user = current_user
                self.logger.info(f"Using Zerodha Kite data provider for user '{current_user}' (from provider name)")
                return self._provider
            else:
                self.logger.warning(f"Unknown provider: {force_provider}, falling back to default (Yahoo Finance)")
        
        # If we already have a provider and aren't forcing a change
        if self._provider is not None:
            # Fix: Always maintain the current Kite user, even when called without parameters
            if self._provider_name == 'kite' and self._provider_user:
                self.logger.debug(f"Reusing existing Kite provider for user '{self._provider_user}'")
            else:
                self.logger.debug(f"Reusing existing provider: {self._provider_name}")
            return self._provider
            
        # Default to Yahoo Finance as per requirements
        self.logger.info("Using Yahoo Finance as default data provider")
        self._provider = YahooFinanceIntegration()
        self._provider_name = 'yahoo'
        self._provider_user = None  # Yahoo doesn't use user IDs
        return self._provider
    
    def get_provider_name(self):
        """Get the name of the current provider"""
        if self._provider_name is None:
            self.get_provider()  # This will set the provider name
        return self._provider_name
    
    def get_provider_info(self):
        """Get detailed info about the current provider including user if applicable"""
        if self._provider_name is None:
            self.get_provider()  # This will set the provider info
        
        info = {
            "name": self._provider_name
        }
        
        # Add user info for Kite provider
        if self._provider_name == 'kite' and self._provider_user:
            self.logger.info(f"Adding user_id to provider info: '{self._provider_user}' (type: {type(self._provider_user).__name__})")
            info["user_id"] = self._provider_user
            info["display_name"] = f"Kite-{self._provider_user.capitalize()}"
            
            # Add diagnostic info for troubleshooting
            self.logger.info(f"Current provider info - Name: {self._provider_name}, User: {self._provider_user}")
        
        self.logger.info(f"Returning provider info: {info}")
        return info
    
    def test_provider(self, provider_name, user_id=None):
        """
        Test if a specific provider works
        
        Args:
            provider_name (str): Provider to test ('kite' or 'yahoo')
            user_id (str, optional): User identifier for Kite provider
            
        Returns:
            bool: True if the provider works, False otherwise
        """
        try:
            if provider_name.lower() == 'kite':
                provider = KiteIntegration(user_id=user_id or DEFAULT_KITE_USER)
                return provider.verify_token()
            elif provider_name.lower().startswith('kite-'):
                # Extract user ID from provider name
                parsed_user_id = provider_name.lower().split('-', 1)[1]
                current_user = user_id or parsed_user_id
                provider = KiteIntegration(user_id=current_user)
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
            self.logger.error(f"Error testing provider {provider_name}{f' for user {user_id}' if user_id else ''}: {str(e)}")
            return False

# Create a singleton instance
provider_factory = DataProviderFactory()

# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    provider = provider_factory.get_provider()
    print(f"Using provider: {provider_factory.get_provider_name()}")
    
    # Test with a specific user
    kite_provider = provider_factory.get_provider(force_provider='kite', user_id='sushant')
    print(f"Provider info: {provider_factory.get_provider_info()}")
