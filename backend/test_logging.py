"""
Test script to verify the logging configuration works correctly.
This script will generate different types of log messages to test
that DATE_CONVERSION logs go to the file but not to the console.
"""

import logging
from datetime import datetime
from logging_config import setup_logging, get_logger
from utils import log_date_conversion, safe_strptime, safe_strftime

# Set up logging
logger = setup_logging('test-logger')

def run_test():
    """Run a series of test logs to verify filtering works correctly"""
    
    # Regular logs (should appear in both console and file)
    logger.info("TEST - Regular INFO log message (should appear in console and file)")
    logger.warning("TEST - Regular WARNING log message (should appear in console and file)")
    logger.error("TEST - Regular ERROR log message (should appear in console and file)")
    
    # DATE_CONVERSION logs (should only appear in file, not console)
    test_date = datetime.now()
    
    # Use the utility functions
    logger.info("TEST - About to log date conversions (these should only appear in the log file)")
    
    # Test direct date conversion log
    log_date_conversion(
        "2023-04-05",
        datetime(2023, 4, 5),
        "Test DATE_CONVERSION direct",
        extra_info={"test": "direct conversion log"}
    )
    
    # Test via strptime
    parsed_date = safe_strptime("2023-04-05", "%Y-%m-%d", 
                               extra_info={"test": "via safe_strptime"})
    
    # Test via strftime
    formatted_date = safe_strftime(parsed_date, "%Y-%m-%d", 
                                  extra_info={"test": "via safe_strftime"})
    
    # Regular log after date conversions
    logger.info(f"TEST - Completed date conversion tests with result: {formatted_date}")
    
    # Message to check the log file
    logger.info("TEST - Check the app.log file to verify DATE_CONVERSION logs are there")
    logger.info("TEST - PATH: backend/debug/app.log")

if __name__ == "__main__":
    run_test() 