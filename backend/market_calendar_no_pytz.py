"""
Market Calendar Utility Functions (No PyTZ Version)

This module provides utilities for handling market hours and dates for the Indian stock market.
It helps validate if a given timestamp is within market hours and find the next valid market time.
This version does not require the pytz library.
"""

import logging
from datetime import datetime, time, timedelta, timezone

# Configure logging
logger = logging.getLogger(__name__)

# Constants for Indian market hours
MARKET_OPEN_TIME = time(9, 15, 0)  # 9:15 AM
MARKET_CLOSE_TIME = time(15, 15, 0)  # 3:15 PM
IST_OFFSET = timedelta(hours=5, minutes=30)  # UTC+5:30 for IST
IST_TIMEZONE = timezone(IST_OFFSET)

def is_market_hours(timestamp):
    """
    Check if a timestamp falls within Indian market hours (9:15 AM - 3:15 PM IST, Monday-Friday).
    
    Args:
        timestamp (datetime): The timestamp to check (timezone-aware or naive)
        
    Returns:
        bool: True if the timestamp is within market hours, False otherwise
    """
    try:
        # Convert to timezone-aware datetime if it's not already
        if timestamp.tzinfo is None:
            # Assume IST for naive datetimes
            timestamp = timestamp.replace(tzinfo=IST_TIMEZONE)
        else:
            # Ensure timestamp is in IST
            timestamp = timestamp.astimezone(IST_TIMEZONE)
            
        # Check if it's a weekday (0 = Monday, 4 = Friday, 5-6 = Weekend)
        if timestamp.weekday() >= 5:  # Weekend
            return False
            
        # Check if time is within market hours
        current_time = timestamp.time()
        return MARKET_OPEN_TIME <= current_time <= MARKET_CLOSE_TIME
        
    except Exception as e:
        logger.error(f"Error checking market hours for {timestamp}: {str(e)}")
        # Default to False on error to be safe
        return False

def next_valid_market_time(timestamp):
    """
    Get the next valid market timestamp from a given timestamp.
    If the timestamp is already within market hours, it is returned unchanged.
    
    Args:
        timestamp (datetime): The timestamp to adjust
        
    Returns:
        datetime: The next valid market timestamp
    """
    try:
        # Convert to timezone-aware datetime if it's not already
        if timestamp.tzinfo is None:
            # Assume IST for naive datetimes
            timestamp = timestamp.replace(tzinfo=IST_TIMEZONE)
        else:
            # Ensure timestamp is in IST
            timestamp = timestamp.astimezone(IST_TIMEZONE)
            
        # If already within market hours, return as is
        if is_market_hours(timestamp):
            return timestamp
            
        # Get day of week
        weekday = timestamp.weekday()
        current_time = timestamp.time()
        
        # Calculate the next valid time
        if weekday >= 5:  # Weekend
            # Calculate days until Monday
            days_until_monday = (7 - weekday) % 7
            # Go to next Monday at market open
            next_day = timestamp.date() + timedelta(days=days_until_monday)
            next_time = datetime.combine(
                next_day,
                MARKET_OPEN_TIME,
                tzinfo=IST_TIMEZONE
            )
        elif current_time < MARKET_OPEN_TIME:
            # Same day but before market open
            next_time = datetime.combine(
                timestamp.date(),
                MARKET_OPEN_TIME,
                tzinfo=IST_TIMEZONE
            )
        elif current_time > MARKET_CLOSE_TIME:
            # After market close, go to next business day
            next_day = timestamp.date() + timedelta(days=1)
            # If next day is weekend, go to Monday
            if next_day.weekday() >= 5:
                next_day = next_day + timedelta(days=(7 - next_day.weekday()) % 7)
            next_time = datetime.combine(
                next_day, 
                MARKET_OPEN_TIME,
                tzinfo=IST_TIMEZONE
            )
        else:
            # Should not reach here if input validation is correct
            next_time = timestamp
            
        return next_time
        
    except Exception as e:
        logger.error(f"Error finding next valid market time for {timestamp}: {str(e)}")
        # Return original timestamp on error to avoid crashing
        return timestamp

def format_market_time(timestamp, with_tz=True):
    """
    Format a timestamp for display in logs and reports with proper timezone.
    
    Args:
        timestamp (datetime): The timestamp to format
        with_tz (bool): Whether to include timezone in output
        
    Returns:
        str: Formatted timestamp string
    """
    try:
        if timestamp is None:
            return "None"
            
        # Convert to timezone-aware datetime if it's not already
        if timestamp.tzinfo is None:
            # Assume IST for naive datetimes
            timestamp = timestamp.replace(tzinfo=IST_TIMEZONE)
        else:
            # Ensure timestamp is in IST
            timestamp = timestamp.astimezone(IST_TIMEZONE)
            
        # Format with or without timezone
        if with_tz:
            return timestamp.strftime('%Y-%m-%d %H:%M:%S') + " IST"
        else:
            return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    except Exception as e:
        logger.error(f"Error formatting timestamp {timestamp}: {str(e)}")
        return str(timestamp)

def parse_market_time(time_str):
    """
    Parse a timestamp string into a datetime object with IST timezone.
    Handles various timestamp formats.
    
    Args:
        time_str (str): Timestamp string
        
    Returns:
        datetime: Timezone-aware datetime