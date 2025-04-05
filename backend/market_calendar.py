"""
Market Calendar Utility Functions

This module provides utilities for handling market hours and dates for the Indian stock market.
It helps validate if a given timestamp is within market hours and find the next valid market time.
"""

import logging
from datetime import datetime, time, timedelta
import pytz

# Configure logging
logger = logging.getLogger(__name__)

# Constants for Indian market hours
MARKET_OPEN_TIME = time(9, 15, 0)  # 9:15 AM
MARKET_CLOSE_TIME = time(15, 15, 0)  # 3:15 PM
IST_TIMEZONE = pytz.timezone('Asia/Kolkata')

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
            timestamp = IST_TIMEZONE.localize(timestamp)
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
            timestamp = IST_TIMEZONE.localize(timestamp)
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
            next_time = datetime.combine(
                timestamp.date() + timedelta(days=days_until_monday),
                MARKET_OPEN_TIME
            )
            next_time = IST_TIMEZONE.localize(next_time)
        elif current_time < MARKET_OPEN_TIME:
            # Same day but before market open
            next_time = datetime.combine(
                timestamp.date(),
                MARKET_OPEN_TIME
            )
            next_time = IST_TIMEZONE.localize(next_time)
        elif current_time > MARKET_CLOSE_TIME:
            # After market close, go to next business day
            next_day = timestamp.date() + timedelta(days=1)
            # If next day is weekend, go to Monday
            if next_day.weekday() >= 5:
                next_day = next_day + timedelta(days=(7 - next_day.weekday()) % 7)
            next_time = datetime.combine(next_day, MARKET_OPEN_TIME)
            next_time = IST_TIMEZONE.localize(next_time)
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
            timestamp = IST_TIMEZONE.localize(timestamp)
        else:
            # Ensure timestamp is in IST
            timestamp = timestamp.astimezone(IST_TIMEZONE)
            
        # Format with or without timezone
        if with_tz:
            return timestamp.strftime('%Y-%m-%d %H:%M:%S IST')
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
        datetime: Timezone-aware datetime object
    """
    try:
        # First, try with timezone info
        if ' IST' in time_str:
            # Parse datetime with IST timezone
            dt = datetime.strptime(time_str.replace(' IST', ''), '%Y-%m-%d %H:%M:%S')
            return IST_TIMEZONE.localize(dt)
        elif '+05:30' in time_str:
            # Parse datetime with +05:30 timezone
            dt = datetime.strptime(time_str.replace('+05:30', ''), '%Y-%m-%d %H:%M:%S')
            return IST_TIMEZONE.localize(dt)
        else:
            # Assume IST for timestamps without timezone
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%d-%m-%Y %H:%M:%S',
                '%d-%m-%Y'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(time_str, fmt)
                    return IST_TIMEZONE.localize(dt)
                except ValueError:
                    continue
                    
            # If all formats fail, raise an exception
            raise ValueError(f"Could not parse timestamp string: {time_str}")
    
    except Exception as e:
        logger.error(f"Error parsing timestamp string {time_str}: {str(e)}")
        raise

# Testing code
if __name__ == "__main__":
    # Test with various timestamps
    test_timestamps = [
        datetime(2025, 1, 6, 9, 15, 0),  # Monday, market open
        datetime(2025, 1, 6, 15, 15, 0),  # Monday, market close
        datetime(2025, 1, 6, 8, 30, 0),  # Monday, before market open
        datetime(2025, 1, 6, 16, 0, 0),  # Monday, after market close
        datetime(2025, 1, 4, 12, 0, 0),  # Saturday
        datetime(2025, 1, 5, 12, 0, 0),  # Sunday
    ]
    
    for ts in test_timestamps:
        ist_ts = IST_TIMEZONE.localize(ts)
        is_valid = is_market_hours(ist_ts)
        next_time = next_valid_market_time(ist_ts)
        print(f"Timestamp: {format_market_time(ist_ts)}")
        print(f"Is market hours: {is_valid}")
        print(f"Next valid market time: {format_market_time(next_time)}")
        print("---")
