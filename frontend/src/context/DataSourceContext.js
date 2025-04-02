import React, { createContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export const DataSourceContext = createContext();

export const DataSourceProvider = ({ children }) => {
  const [dataProvider, setDataProvider] = useState('yahoo');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [requiresAuth, setRequiresAuth] = useState(false);
  const [tokenValid, setTokenValid] = useState(false);
  const [lastTokenCheck, setLastTokenCheck] = useState(null);
  
  // Fetch initial data provider info
  useEffect(() => {
    const fetchDataProviderInfo = async () => {
      try {
        console.log("Fetching initial data provider info...");
        setLoading(true);
        
        const info = await api.getDataProviderInfo();
        console.log("Received data provider info:", info);
        
        setDataProvider(info.provider);
        
        // Check token validity if Kite is selected
        if (info.provider === 'kite') {
          await checkKiteToken();
        }
      } catch (err) {
        console.error("Failed to fetch data provider info:", err);
        setError('Failed to connect to backend');
      } finally {
        setLoading(false);
      }
    };

    fetchDataProviderInfo();
  }, []);
  
  // Change data provider
  const changeDataProvider = async (provider) => {
    try {
      setLoading(true);
      setError(null);
      
      console.log(`Changing data provider to: ${provider}`);
      
      const response = await api.setDataProvider(provider);
      
      if (response.success) {
        setDataProvider(response.provider);
        setRequiresAuth(response.requires_auth);
        
        // If provider is Kite and authentication is required, set state
        if (provider === 'kite') {
          setTokenValid(!response.requires_auth);
        }
      } else {
        setError(response.error || 'Failed to change data provider');
      }
    } catch (err) {
      console.error("Error changing data provider:", err);
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  // Check Kite token validity with enhanced debugging
  const checkKiteToken = async (force = false) => {
    try {
      // Add to session storage debug log
      logDebug(`Checking Kite token validity (force=${force})`);
      
      // Check if we need to revalidate based on time
      const now = new Date();
      if (!force && lastTokenCheck) {
        const timeSinceLastCheck = now - lastTokenCheck;
        const timeSinceLastCheckMinutes = Math.floor(timeSinceLastCheck / 60000);
        
        // Don't check more than once per hour unless forced
        if (timeSinceLastCheck < 3600000) { // 1 hour in milliseconds
          logDebug(`Skipping token check - checked ${timeSinceLastCheckMinutes} minutes ago`);
          return tokenValid;
        }
      }
      
      logDebug("Making API call to verify Kite token");
      const startTime = performance.now();
      const response = await api.verifyKiteToken();
      const endTime = performance.now();
      
      // Log API call performance
      logDebug(`Token verification API call completed in ${Math.round(endTime - startTime)}ms`, response);
      
      if (response.success) {
        logDebug(`Token verification result: ${response.valid}`);
        
        // Track state change
        const oldState = { tokenValid, requiresAuth };
        
        setTokenValid(response.valid);
        setRequiresAuth(!response.valid);
        setLastTokenCheck(now);
        
        logDebug('Updated token state', {
          previous: oldState,
          current: { tokenValid: response.valid, requiresAuth: !response.valid },
          changed: (oldState.tokenValid !== response.valid || oldState.requiresAuth === response.valid)
        });
        
        return response.valid;
      } else {
        logDebug(`Token verification failed: ${response.error}`);
        setTokenValid(false);
        setRequiresAuth(true);
        setLastTokenCheck(now);
        return false;
      }
    } catch (err) {
      logDebug('Error checking Kite token:', err.message);
      
      // Log error details
      const errorInfo = {
        message: err.message,
        name: err.name,
        stack: err.stack ? err.stack.split('\n')[0] : 'No stack trace'
      };
      logDebug('Detailed error info', errorInfo);
      
      setTokenValid(false);
      setRequiresAuth(true);
      setLastTokenCheck(new Date());
      return false;
    }
  };
  
  // Check if token needs verification based on trading hours
  const shouldVerifyToken = () => {
    // Get current time in IST (UTC+5:30)
    const now = new Date();
    const istOffset = 330; // IST is UTC+5:30 (330 minutes)
    const istTime = new Date(now.getTime() + (istOffset - now.getTimezoneOffset()) * 60000);
    
    // Check if it's after 3:30:05 PM IST
    const isPastTradingHours = istTime.getHours() > 15 || 
                              (istTime.getHours() === 15 && istTime.getMinutes() >= 30 && istTime.getSeconds() >= 5);
    
    // If past trading hours and we're using Kite, we should verify
    return dataProvider === 'kite' && isPastTradingHours;
  };
  
  // Add logging helpers and debugging flags
  const logDebug = (message, data = null) => {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}`;
    console.log('%c[DataSourceContext]', 'color: #9c27b0; font-weight: bold', logMessage, data || '');
    
    // Save to session storage for persistence
    const logs = JSON.parse(sessionStorage.getItem('kiteAuthLogs') || '[]');
    logs.push({ timestamp, message, data: data ? JSON.stringify(data) : null });
    // Keep only last 50 logs
    if (logs.length > 50) logs.shift();
    sessionStorage.setItem('kiteAuthLogs', JSON.stringify(logs));
  };
  
  // Debug function to check if listener is active
  const checkListenerActive = () => {
    try {
      // Use a unique event ID for testing
      const testEventId = `test_${Date.now()}`;
      
      // Set a flag that we're going to test the listener
      sessionStorage.setItem('kiteAuthListenerTest', testEventId);
      
      // Dispatch a test message event
      window.dispatchEvent(new MessageEvent('message', {
        data: { type: 'listenerTest', id: testEventId }
      }));
      
      logDebug('Dispatched test message event to check if listener is active');
      return true;
    } catch (e) {
      logDebug('Error testing message listener', e.message);
      return false;
    }
  };
  
  // Global listener outside of React lifecycle for backup
  useEffect(() => {
    // Create a global backup listener
    const globalBackupListener = (event) => {
      try {
        if (!event.data) return;
        
        // Log test events but don't process them further
        if (event.data.type === 'listenerTest') {
          const testId = sessionStorage.getItem('kiteAuthListenerTest');
          logDebug(`Test listener received message: ${event.data.id}`, { 
            matchesExpected: event.data.id === testId
          });
          return;
        }
        
        // Only log Kite auth-related messages to avoid noise
        if (event.data.status && (event.data.provider === 'kite' || event.data.reason)) {
          logDebug('GLOBAL BACKUP LISTENER received message', {
            data: event.data,
            origin: event.origin,
            source: event.source ? 'Window object' : 'null',
            hasOpener: window.opener !== null,
            timestamp: new Date().toISOString()
          });
          
          // Store the message for debugging purposes
          sessionStorage.setItem('lastKiteAuthMessage', JSON.stringify({
            data: event.data,
            origin: event.origin,
            time: new Date().toISOString()
          }));
        }
      } catch (e) {
        console.error('Error in global backup listener:', e);
      }
    };
    
    // Add the global listener
    window.addEventListener('message', globalBackupListener);
    logDebug('Installed global backup message listener');
    
    // Set a flag that the backup listener is active
    sessionStorage.setItem('kiteAuthBackupListener', 'active');
    
    return () => {
      window.removeEventListener('message', globalBackupListener);
      sessionStorage.setItem('kiteAuthBackupListener', 'inactive');
      logDebug('Removed global backup message listener');
    };
  }, []);
  
  // Handle messages from popup window with enhanced debugging
  const handleAuthMessage = useCallback(async (event) => {
    // Log detailed message information
    const messageInfo = {
      hasData: !!event.data,
      dataType: event.data ? typeof event.data : 'undefined',
      origin: event.origin,
      eventType: event.type,
      source: event.source ? 'Window object' : 'null',
      timestamp: new Date().toISOString(),
      dataProvider: dataProvider,
      tokenValid: tokenValid,
      requiresAuth: requiresAuth
    };
    
    logDebug('Received message event', messageInfo);
    
    // Track in session storage that we received a message
    const messageCount = parseInt(sessionStorage.getItem('kiteAuthMessageCount') || '0');
    sessionStorage.setItem('kiteAuthMessageCount', messageCount + 1);
    
    // Log the actual message data if it exists
    if (event.data) {
      logDebug('Message data content', event.data);
    }
    
    // Check for test events
    if (event.data && event.data.type === 'listenerTest') {
      const testId = sessionStorage.getItem('kiteAuthListenerTest');
      logDebug(`Component listener received test: ${event.data.id}`, {
        matchesExpected: event.data.id === testId
      });
      return;
    }
    
    if (!event.data || typeof event.data !== 'object') {
      logDebug('Ignoring message - invalid data format');
      return;
    }
    
    // Process actual authentication messages
    if (event.data.status === 'success' && event.data.provider === 'kite') {
      logDebug('Authentication successful message received', event.data);
      
      // Store the successful message for debugging
      sessionStorage.setItem('lastKiteAuthSuccess', JSON.stringify({
        data: event.data,
        time: new Date().toISOString(),
        origin: event.origin
      }));
      
      // Set as Kite provider and update token status
      logDebug('Updating state after successful authentication');
      setDataProvider('kite');
      setTokenValid(true);
      setRequiresAuth(false);
      setError(null);
      
      // Verify token to ensure everything is properly set up
      logDebug('Verifying token after authentication');
      try {
        const result = await checkKiteToken(true);
        logDebug('Token verification result', { result });
      } catch (error) {
        logDebug('Error verifying token', { error: error.message });
      }
      
      // Log final state
      logDebug('Authentication process completed', {
        provider: 'kite',
        tokenValid: true,
        requiresAuth: false
      });
      
    } else if (event.data.status === 'failed' || event.data.status === 'error') {
      const reason = event.data.reason || 'Unknown error';
      logDebug('Authentication failed message received', { status: event.data.status, reason });
      
      // Store the failure message for debugging
      sessionStorage.setItem('lastKiteAuthFailure', JSON.stringify({
        data: event.data,
        time: new Date().toISOString(),
        origin: event.origin
      }));
      
      setError(`Authentication failed: ${reason}`);
      
      // Keep existing provider, but update token status if provider is Kite
      if (dataProvider === 'kite') {
        logDebug('Updating Kite provider state after authentication failure');
        setTokenValid(false);
        setRequiresAuth(true);
      }
    } else {
      logDebug('Unrecognized message format', event.data);
    }
  }, [dataProvider, tokenValid, requiresAuth, checkKiteToken]);
  
  // Set up event listener for popup messages with detailed logging
  useEffect(() => {
    logDebug('Setting up component message event listener for auth popup');
    
    // Check if the provider is Kite - this helps with debugging
    logDebug('Current data provider state', { 
      provider: dataProvider, 
      tokenValid, 
      requiresAuth,
      listenerCount: parseInt(sessionStorage.getItem('kiteAuthListenerCount') || '0') + 1,
    });
    
    // Update listener count in session storage
    const listenerCount = parseInt(sessionStorage.getItem('kiteAuthListenerCount') || '0');
    sessionStorage.setItem('kiteAuthListenerCount', listenerCount + 1);
    
    // Set a timestamp for when the listener was added
    sessionStorage.setItem('kiteAuthListenerTimestamp', new Date().toISOString());
    sessionStorage.setItem('kiteAuthListenerActive', 'true');
    
    // Add the event listener
    window.addEventListener('message', handleAuthMessage);
    
    // Test if the listener is active
    setTimeout(() => {
      checkListenerActive();
    }, 500);
    
    // Clean up function
    return () => {
      logDebug('Removing component message event listener');
      sessionStorage.setItem('kiteAuthListenerActive', 'false');
      window.removeEventListener('message', handleAuthMessage);
    };
  }, [handleAuthMessage]);
  
  // Expose the debug helpers for external use
  useEffect(() => {
    window.kiteAuthDebug = {
      checkListener: checkListenerActive,
      getLogs: () => JSON.parse(sessionStorage.getItem('kiteAuthLogs') || '[]'),
      getLastMessage: () => JSON.parse(sessionStorage.getItem('lastKiteAuthMessage') || 'null'),
      getState: () => ({
        dataProvider,
        tokenValid,
        requiresAuth,
        error,
        listenerActive: sessionStorage.getItem('kiteAuthListenerActive') === 'true',
        backupListenerActive: sessionStorage.getItem('kiteAuthBackupListener') === 'active',
        messageCount: parseInt(sessionStorage.getItem('kiteAuthMessageCount') || '0'),
        listenerCount: parseInt(sessionStorage.getItem('kiteAuthListenerCount') || '0')
      }),
      clearLogs: () => sessionStorage.removeItem('kiteAuthLogs'),
      testListener: checkListenerActive
    };
    
    return () => {
      delete window.kiteAuthDebug;
    };
  }, [dataProvider, tokenValid, requiresAuth, error]);
  
  // Initiate Kite authentication with enhanced debugging
  const initiateKiteAuth = async () => {
    try {
      setLoading(true);
      logDebug("Initiating Kite authentication...");
      
      // Log current state before initiating auth
      logDebug("Current state before authentication", {
        dataProvider,
        tokenValid,
        requiresAuth,
        listenerActive: sessionStorage.getItem('kiteAuthListenerActive') === 'true'
      });
      
      // Clear previous authentication tracking
      sessionStorage.setItem('kiteAuthStarted', new Date().toISOString());
      sessionStorage.removeItem('lastKiteAuthSuccess');
      sessionStorage.removeItem('lastKiteAuthFailure');
      
      // Ensure the message event listener is active before proceeding
      const listenerActive = checkListenerActive();
      logDebug(`Message listener active check: ${listenerActive}`);
      
      // If listener is not active, try re-mounting it
      if (!listenerActive && sessionStorage.getItem('kiteAuthListenerActive') !== 'true') {
        logDebug("Listener appears inactive, attempting recovery");
        window.removeEventListener('message', handleAuthMessage);
        window.addEventListener('message', handleAuthMessage);
        sessionStorage.setItem('kiteAuthListenerActive', 'true');
        logDebug("Re-added message event listener");
      }
      
      const response = await api.getKiteLoginUrl();
      
      if (response.success) {
        logDebug("Opening Kite login URL", response.login_url);
        
        // Store that we're initiating auth
        sessionStorage.setItem('kiteAuthPopupOpened', new Date().toISOString());
        
        // Open login URL in a new window with debug info
        const authWindow = window.open(response.login_url, '_blank', 'width=800,height=600');
        
        // Check if popup was blocked
        if (!authWindow) {
          logDebug("Popup was blocked by browser");
          setError('Popup was blocked. Please allow popups for this site and try again.');
          return;
        }
        
        logDebug("Auth popup window opened successfully");
        
        // Add a check to see if the popup gets closed without sending a message
        const popupChecker = setInterval(() => {
          if (authWindow.closed) {
            logDebug("Detected auth popup was closed");
            clearInterval(popupChecker);
            
            // Check if we received any auth message
            const lastSuccess = sessionStorage.getItem('lastKiteAuthSuccess');
            const lastFailure = sessionStorage.getItem('lastKiteAuthFailure');
            
            if (!lastSuccess && !lastFailure) {
              logDebug("Popup closed without receiving auth message");
              // Check token status after a delay
              setTimeout(async () => {
                logDebug("Checking token status after popup closed");
                const isValid = await checkKiteToken(true);
                logDebug(`Token check after popup close: ${isValid ? 'valid' : 'invalid'}`);
              }, 1000);
            }
          }
        }, 1000);
        
      } else {
        logDebug("Failed to get Kite login URL", response.error);
        setError(response.error || 'Failed to get Kite login URL');
      }
    } catch (err) {
      logDebug("Error initiating Kite authentication", err.message);
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <DataSourceContext.Provider
      value={{
        dataProvider,
        loading,
        error,
        requiresAuth,
        tokenValid,
        changeDataProvider,
        checkKiteToken,
        initiateKiteAuth,
        shouldVerifyToken
      }}
    >
      {children}
    </DataSourceContext.Provider>
  );
};
