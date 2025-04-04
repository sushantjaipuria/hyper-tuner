# Debug Logs

This directory contains log files and debug information for the Hyper-Tuner application. These files are useful for diagnosing issues, particularly related to date handling and API requests.

## Log Files

- `app.log` - Main application log file that captures all console logs
- `app.log.YYYY-MM-DD` - Rotated log files (one per day)

## Log Filtering System

The application uses a special logging configuration that filters certain log messages:

- **Console Output**: All logs EXCEPT those containing "DATE_CONVERSION" are displayed in the console. This provides a cleaner development experience by reducing console noise.
- **Log Files**: ALL logs, including "DATE_CONVERSION" messages, are saved to the log files for comprehensive debugging.

This means that date conversion logs are only visible in the log files, not in the console.

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

- `DATE_DEBUG` - Date-related debugging information (visible in console and log file)
- `DATE_CONVERSION` - Logs from the date conversion utility (only visible in log file)
- `KITE DATE FIX` - Information about date adjustments for Kite API
- `KITE API REQUEST` - Details of requests to the Kite API

## Adding Useful Debug Information

When working with dates and times, please use the utility functions in `utils.py`:

- `safe_strptime()` - For converting strings to datetime objects
- `safe_strftime()` - For converting datetime objects to strings
- `format_date_for_api()` - For formatting dates specifically for API use
- `log_date_conversion()` - Low-level function for logging date conversions

These functions will automatically add useful context to the logs.

## Testing the Logging Configuration

You can verify the logging configuration is working correctly by running:

```
python3 test_logging.py
```

This will generate various log messages, including DATE_CONVERSION logs that will only appear in the log file. 