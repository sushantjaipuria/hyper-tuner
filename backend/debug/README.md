# Debug Logs

This directory contains log files and debug information for the Hyper-Tuner application. These files are useful for diagnosing issues, particularly related to date handling and API requests.

## Log Files

- `app.log` - Main application log file that captures all console logs
- `app.log.YYYY-MM-DD` - Rotated log files (one per day)

## Debug Files

Several types of debug files are generated automatically:

- `backtest_request_debug_*.json` - Request data for backtest API calls
- `backtest_results_debug_*.json` - Results from backtest operations
- `kite_raw_response_*.json` - Raw responses from Kite API calls

## Date Conversion Logging

All date/datetime conversions are logged in detail with:
- Input and output values
- Type information
- Source location
- Context information
- Timezone details

## Special Debugging Features

The following markers in logs indicate special debugging information:

- `DATE_DEBUG` - Date-related debugging information
- `DATE_CONVERSION` - Logs from the date conversion utility
- `KITE DATE FIX` - Information about date adjustments for Kite API
- `KITE API REQUEST` - Details of requests to the Kite API

## Adding Useful Debug Information

When working with dates and times, please use the utility functions in `utils.py`:

- `safe_strptime()` - For converting strings to datetime objects
- `safe_strftime()` - For converting datetime objects to strings
- `format_date_for_api()` - For formatting dates specifically for API use
- `log_date_conversion()` - Low-level function for logging date conversions

These functions will automatically add useful context to the logs. 