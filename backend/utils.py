"""Utility functions for the application"""
import logging
import inspect
from datetime import datetime, date
import traceback

logger = logging.getLogger(__name__)

def log_date_conversion(input_value, output_value, conversion_type, location=None, extra_info=None):
    """
    Log a date conversion operation with detailed input and output information.
    
    Args:
        input_value: The input value before conversion
        output_value: The output value after conversion
        conversion_type: Type of conversion (e.g., 'strptime', 'strftime', 'format')
        location: Optional location information
        extra_info: Optional additional context information
    """
    if location is None:
        # Try to automatically determine the calling function and location
        stack = inspect.stack()
        if len(stack) > 1:
            caller = stack[1]
            location = f"{caller.filename.split('/')[-1]}:{caller.lineno} in {caller.function}"
        else:
            location = "unknown"
            
    # Format input and output values with type information
    input_type = type(input_value).__name__
    output_type = type(output_value).__name__
    
    # Create log message
    log_message = f"DATE_CONVERSION - {conversion_type} at {location}:"
    log_message += f"\n  Input: {input_value} (type: {input_type})"
    log_message += f"\n  Output: {output_value} (type: {output_type})"
    
    if extra_info:
        log_message += f"\n  Context: {extra_info}"
    
    # Add timezone information if available for datetime objects
    if isinstance(input_value, datetime):
        log_message += f"\n  Input timezone info: {input_value.tzinfo}"
    if isinstance(output_value, datetime):
        log_message += f"\n  Output timezone info: {output_value.tzinfo}"
        
    # Log the message
    logger.info(log_message)
    
    return output_value  # Return the output value to allow chaining

def safe_strptime(date_string, format_string, extra_info=None):
    """
    Safely convert a string to a datetime object with logging.
    
    Args:
        date_string (str): The string to convert
        format_string (str): The format string
        extra_info (dict, optional): Additional context information
        
    Returns:
        datetime: The parsed datetime object
    """
    try:
        result = datetime.strptime(date_string, format_string)
        return log_date_conversion(
            date_string, 
            result, 
            f"strptime with format '{format_string}'",
            extra_info=extra_info
        )
    except Exception as e:
        logger.error(f"DATE_CONVERSION_ERROR - Failed to parse '{date_string}' with format '{format_string}': {str(e)}")
        logger.debug(traceback.format_exc())
        raise

def safe_strftime(dt_object, format_string, extra_info=None):
    """
    Safely convert a datetime object to a string with logging.
    
    Args:
        dt_object (datetime): The datetime object to convert
        format_string (str): The format string
        extra_info (dict, optional): Additional context information
        
    Returns:
        str: The formatted date string
    """
    try:
        result = dt_object.strftime(format_string)
        return log_date_conversion(
            dt_object, 
            result, 
            f"strftime with format '{format_string}'",
            extra_info=extra_info
        )
    except Exception as e:
        logger.error(f"DATE_CONVERSION_ERROR - Failed to format datetime with format '{format_string}': {str(e)}")
        logger.debug(traceback.format_exc())
        raise

def format_date_for_api(date_obj, format_string='%Y-%m-%d', extra_info=None):
    """
    Format a date object for API use with logging.
    
    Args:
        date_obj (datetime or date): The date to format
        format_string (str): The format string to use
        extra_info (dict, optional): Additional context information
        
    Returns:
        str: The formatted date string
    """
    try:
        # Handle both datetime and date objects
        if isinstance(date_obj, (datetime, date)):
            result = date_obj.strftime(format_string)
            return log_date_conversion(
                date_obj,
                result,
                f"API date formatting with '{format_string}'",
                extra_info=extra_info
            )
        # Handle string input (already formatted)
        elif isinstance(date_obj, str):
            logger.info(f"DATE_CONVERSION - String date already formatted: {date_obj}")
            return date_obj
        else:
            logger.warning(f"DATE_CONVERSION - Unexpected date type: {type(date_obj).__name__}")
            return str(date_obj)
    except Exception as e:
        logger.error(f"DATE_CONVERSION_ERROR - Failed to format date for API: {str(e)}")
        logger.debug(traceback.format_exc())
        raise 