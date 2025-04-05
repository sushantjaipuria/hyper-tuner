"""
Logging configuration for the application.
This module provides centralized logging configuration with custom filters.
"""

import os
import logging
from logging.handlers import TimedRotatingFileHandler

class DateConversionFilter(logging.Filter):
    """
    Custom filter that rejects messages containing DATE_CONVERSION 
    for specific handlers (like console output).
    """
    def filter(self, record):
        # Return False to reject DATE_CONVERSION logs (for console)
        # True to accept all other logs
        
        # First check the actual message after formatting
        message = record.getMessage()
        if 'DATE_CONVERSION' in message:
            return False
        return True

def setup_logging(app_name='hyper-tuner'):
    """
    Set up logging with console handler (filtered) and file handler (unfiltered).
    
    Args:
        app_name (str): Name of the application for logger naming
        
    Returns:
        logging.Logger: Configured logger
    """
    # Ensure debug directory exists
    debug_dir = os.path.join(os.path.dirname(__file__), 'debug')
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)

    # Configure logging with both console and file handlers
    log_file_path = os.path.join(debug_dir, 'app.log')
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Configure root logger - important to disable propagation of filtered loggers
    logging.basicConfig(level=logging.INFO, format=log_format)
    
    # Get the root logger first
    root_logger = logging.getLogger()
    
    # Clear existing handlers from root logger
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Get the application logger
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent propagation to avoid duplicate logs
    
    # Clear existing handlers to avoid duplication
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 1. Console handler WITH filter (no DATE_CONVERSION logs)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(DateConversionFilter())  # Add the filter
    logger.addHandler(console_handler)

    # 2. File handler WITHOUT filter (includes DATE_CONVERSION logs)
    file_handler = TimedRotatingFileHandler(
        log_file_path, 
        when='midnight',
        backupCount=7  # Keep logs for a week
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Set up module loggers for all known modules that might use date conversion
    for module_name in ['utils', 'kite_integration', 'backtest_engine', 'app', 'data_provider_factory']:
        module_logger = logging.getLogger(module_name)
        module_logger.setLevel(logging.INFO)
        module_logger.propagate = False  # Important to prevent propagation
        
        # Clear existing handlers
        for handler in module_logger.handlers[:]:
            module_logger.removeHandler(handler)
            
        # Add filtered console handler
        module_console = logging.StreamHandler()
        module_console.setFormatter(formatter)
        module_console.addFilter(DateConversionFilter())
        module_logger.addHandler(module_console)
        
        # Add unfiltered file handler
        module_file = TimedRotatingFileHandler(
            log_file_path,
            when='midnight',
            backupCount=7
        )
        module_file.setFormatter(formatter)
        module_logger.addHandler(module_file)

    # Log setup confirmation (this will go to both handlers)
    logger.info(f"Logging configured with filtered console output and full file logging to {log_file_path}")
    logger.info(f"DATE_CONVERSION logs will only appear in the log file, not in console output")

    return logger

def get_logger(name=None):
    """
    Get a logger with the specified name, or the root logger if no name is specified.
    
    Args:
        name (str, optional): Logger name. If None, returns the root logger.
        
    Returns:
        logging.Logger: Logger instance
    """
    logger = logging.getLogger(name)
    
    # Check if this logger already has handlers (properly configured)
    if not logger.handlers:
        # If not, set up handlers for this logger with our filter
        root_logger = logging.getLogger()
        
        # If no root handlers, this logger hasn't been properly set up yet
        if not root_logger.handlers:
            # Set up the logging system first
            setup_logging()
            
        # Now get the logger again (it should be configured properly)
        logger = logging.getLogger(name)
        
    return logger
