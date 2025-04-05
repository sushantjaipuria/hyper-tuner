# Frontend Utilities

This directory contains utility functions used throughout the frontend application.

## Date Utilities (`dateUtils.js`)

This module provides consistent date handling that properly manages timezone issues.

### Problem Solved

When using JavaScript's native `toISOString()` method to format dates, the date can sometimes shift due to timezone conversion. This happens because:

1. `toISOString()` converts local dates to UTC
2. This can cause the date to shift backwards by a day depending on your timezone
3. When the backend receives this UTC date, it may interpret it differently than intended

### Solution

The date utility functions in this file use local date components to ensure dates are properly preserved regardless of timezone:

```javascript
// AVOID this approach (potential timezone issues)
const formattedDate = date.toISOString().split('T')[0];

// USE this approach instead (preserves local date)
const formattedDate = formatLocalDate(date);
```

### Available Functions

| Function | Description |
|----------|-------------|
| `formatLocalDate(date)` | Formats a Date to YYYY-MM-DD using local components |
| `getDateDebugInfo(date)` | Returns detailed debug information about a date |

### Usage Example

```javascript
import { formatLocalDate } from '../utils/dateUtils';

// User selects April 15, 2023 in the datepicker
const selectedDate = new Date(2023, 3, 15);

// Format it for API/backend use
const formattedDate = formatLocalDate(selectedDate); // "2023-04-15"
```

### Testing

A test file (`dateUtils.test.js`) is included to verify proper functioning of these utilities. Open your browser console to see the test results in development mode. 