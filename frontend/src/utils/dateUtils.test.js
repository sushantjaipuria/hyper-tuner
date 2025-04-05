/**
 * Simple tests for the date utility functions
 * Run this in the console to verify the functionality
 */

import { formatLocalDate, getDateDebugInfo } from './dateUtils';

/**
 * Test formatLocalDate function
 */
function testFormatLocalDate() {
  console.log('=== Testing formatLocalDate ===');
  
  // Create dates at different times of day
  const morningDate = new Date(2023, 3, 15, 9, 30); // April 15, 2023, 9:30 AM
  const eveningDate = new Date(2023, 3, 15, 21, 30); // April 15, 2023, 9:30 PM
  
  // Test formatting
  console.log('Morning date:', morningDate);
  console.log('Morning date formatted:', formatLocalDate(morningDate));
  console.log('Morning date with ISO:', morningDate.toISOString().split('T')[0]);
  
  console.log('Evening date:', eveningDate);
  console.log('Evening date formatted:', formatLocalDate(eveningDate));
  console.log('Evening date with ISO:', eveningDate.toISOString().split('T')[0]);
  
  // Test dates near timezone boundaries
  const boundaryDate = new Date(2023, 0, 1, 23, 30); // Jan 1, 2023, 11:30 PM
  console.log('Boundary date:', boundaryDate);
  console.log('Boundary date formatted:', formatLocalDate(boundaryDate));
  console.log('Boundary date with ISO:', boundaryDate.toISOString().split('T')[0]);
}

/**
 * Test getDateDebugInfo function
 */
function testGetDateDebugInfo() {
  console.log('=== Testing getDateDebugInfo ===');
  
  const testDate = new Date(2023, 3, 15, 9, 30); // April 15, 2023, 9:30 AM
  const debugInfo = getDateDebugInfo(testDate);
  
  console.log('Debug info for test date:', debugInfo);
  console.log('Local components vs UTC components difference:', {
    yearDiff: debugInfo.localComponents.year - debugInfo.utcComponents.year,
    monthDiff: debugInfo.localComponents.month - debugInfo.utcComponents.month,
    dayDiff: debugInfo.localComponents.day - debugInfo.utcComponents.day
  });
}

// Export tests for potential use in the app
export const runDateTests = () => {
  console.log('Running date utility tests...');
  testFormatLocalDate();
  testGetDateDebugInfo();
  console.log('Tests completed.');
};

// Automatically run tests when in development mode
if (process.env.NODE_ENV === 'development') {
  // Defer execution to ensure console clarity
  setTimeout(() => {
    console.log('%c[DATE UTILS TESTS]', 'background: #4caf50; color: white; padding: 2px 4px; border-radius: 2px;');
    runDateTests();
  }, 1000);
} 