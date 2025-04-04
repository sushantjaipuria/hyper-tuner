/**
 * Date utility functions for handling timezone-safe date conversions
 */

/**
 * Format a Date object to YYYY-MM-DD format preserving the local date
 * regardless of timezone
 *
 * @param {Date} date - The date object to format
 * @returns {string} Date in YYYY-MM-DD format
 */
export const formatLocalDate = (date) => {
  if (!date || !(date instanceof Date)) {
    console.error('Invalid date passed to formatLocalDate:', date);
    return '';
  }
  
  // Use local date components rather than UTC ones
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  
  return `${year}-${month}-${day}`;
};

/**
 * Get debug information about a date object
 *
 * @param {Date} date - The date to debug
 * @returns {Object} Debug information
 */
export const getDateDebugInfo = (date) => {
  if (!date || !(date instanceof Date)) {
    return { error: 'Invalid date object' };
  }
  
  return {
    isoString: date.toISOString(),
    localString: date.toString(),
    localeDateString: date.toLocaleDateString(),
    localComponents: {
      year: date.getFullYear(),
      month: date.getMonth() + 1,
      day: date.getDate(),
    },
    utcComponents: {
      year: date.getUTCFullYear(),
      month: date.getUTCMonth() + 1,
      day: date.getUTCDate(),
    },
    formattedLocal: formatLocalDate(date),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    timezoneOffset: date.getTimezoneOffset(),
  };
};
