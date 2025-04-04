import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { formatLocalDate, getDateDebugInfo } from './utils/dateUtils';
import { runDateTests } from './utils/dateUtils.test';

// Add global error handler for debugging
if (process.env.NODE_ENV === 'development') {
  window.addEventListener('error', function(event) {
    console.error('%c[GLOBAL ERROR DETECTED]', 'background: #d32f2f; color: white; padding: 4px; border-radius: 2px;', {
      message: event.message,
      source: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      error: event.error,
      timestamp: new Date().toISOString()
    });
    
    // Store in session storage for debugging
    try {
      const errors = JSON.parse(sessionStorage.getItem('errorLog') || '[]');
      errors.push({
        message: event.message,
        source: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
        timestamp: new Date().toISOString()
      });
      if (errors.length > 20) errors.shift();
      sessionStorage.setItem('errorLog', JSON.stringify(errors));
    } catch (e) {
      console.error('Failed to log error to sessionStorage:', e);
    }
  });
  
  // Add unhandled rejection handler
  window.addEventListener('unhandledrejection', function(event) {
    console.error('%c[UNHANDLED PROMISE REJECTION]', 'background: #d32f2f; color: white; padding: 4px; border-radius: 2px;', {
      reason: event.reason,
      promise: event.promise,
      timestamp: new Date().toISOString()
    });
    
    // Store in session storage
    try {
      const rejections = JSON.parse(sessionStorage.getItem('rejectionLog') || '[]');
      rejections.push({
        message: event.reason?.message || String(event.reason),
        stack: event.reason?.stack,
        timestamp: new Date().toISOString()
      });
      if (rejections.length > 20) rejections.shift();
      sessionStorage.setItem('rejectionLog', JSON.stringify(rejections));
    } catch (e) {
      console.error('Failed to log rejection to sessionStorage:', e);
    }
  });
  
  // Add global access to debug logs
  window.debugLogs = {
    getErrors: () => JSON.parse(sessionStorage.getItem('errorLog') || '[]'),
    getRejections: () => JSON.parse(sessionStorage.getItem('rejectionLog') || '[]'),
    getKiteAuthLogs: () => JSON.parse(sessionStorage.getItem('kiteAuthLogs') || '[]'),
    getAllLogs: () => ({
      errors: JSON.parse(sessionStorage.getItem('errorLog') || '[]'),
      rejections: JSON.parse(sessionStorage.getItem('rejectionLog') || '[]'),
      kiteAuthLogs: JSON.parse(sessionStorage.getItem('kiteAuthLogs') || '[]'),
      modalLogs: JSON.parse(sessionStorage.getItem('kiteAuthModalLogs') || '[]')
    }),
    clearAll: () => {
      sessionStorage.removeItem('errorLog');
      sessionStorage.removeItem('rejectionLog');
      sessionStorage.removeItem('kiteAuthLogs');
      sessionStorage.removeItem('kiteAuthModalLogs');
      console.log('%c[DEBUG LOGS CLEARED]', 'background: #2e7d32; color: white; padding: 4px; border-radius: 2px;');
    }
  };
  
  // Add global access to date utilities for debugging
  window.dateUtils = {
    formatLocalDate,
    getDateDebugInfo,
    runTests: runDateTests,
    compareFormats: (date) => {
      if (!date) date = new Date();
      return {
        date: date,
        localFormatted: formatLocalDate(date),
        isoFormatted: date.toISOString().split('T')[0],
        debugInfo: getDateDebugInfo(date)
      };
    },
    // Helper to test a specific date
    testDate: (year, month, day) => {
      const date = new Date(year, month - 1, day); // Adjust month (0-indexed)
      return window.dateUtils.compareFormats(date);
    }
  };
  
  console.log('%c[DEBUG LOGGING ENABLED]', 'background: #2e7d32; color: white; padding: 4px; border-radius: 2px;', 
    'Access logs with window.debugLogs and date utilities with window.dateUtils');
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
