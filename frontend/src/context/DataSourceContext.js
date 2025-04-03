import React, { createContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export const DataSourceContext = createContext();

export const DataSourceProvider = ({ children }) => {
  const [dataProvider, setDataProvider] = useState('yahoo');
  const [dataProviderDisplayName, setDataProviderDisplayName] = useState('Yahoo Finance');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [requiresAuth, setRequiresAuth] = useState(false);
  const [tokenValid, setTokenValid] = useState(false);
  const [lastTokenCheck, setLastTokenCheck] = useState(null);
  const [kiteUsers, setKiteUsers] = useState([]);
  const [currentKiteUser, setCurrentKiteUser] = useState(null);
  const [kiteUsersLoaded, setKiteUsersLoaded] = useState(false);
  
  // Log helper with enhanced debugging and colors
  const logDebug = (message, data = null) => {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}`;
    console.log('%c[DataSourceContext]', 'color: #9c27b0; font-weight: bold', logMessage, data || '');
    
    // Save to session storage for persistence
    const logs = JSON.parse(sessionStorage.getItem('kiteAuthLogs') || '[]');
    logs.push({ timestamp, message, data: data ? JSON.stringify(data) : null });
    // Keep only last 100 logs (increased from 50)
    if (logs.length > 100) logs.shift();
    sessionStorage.setItem('kiteAuthLogs', JSON.stringify(logs));
  };
  
  // Add a higher visibility error logger
  const logError = (message, data = null) => {
    const timestamp = new Date().toISOString();
    console.error('%c[DataSourceContext ERROR]', 'color: #f44336; font-weight: bold; background: #ffebee; padding: 2px 4px; border-radius: 2px;', `[${timestamp}] ${message}`, data || '');
    
    // Save to session storage with error flag
    const logs = JSON.parse(sessionStorage.getItem('kiteAuthLogs') || '[]');
    logs.push({ timestamp, message, data: data ? JSON.stringify(data) : null, level: 'error' });
    sessionStorage.setItem('kiteAuthLogs', JSON.stringify(logs));
  };
  
  // Enhanced session storage debugging helper
  const debugSessionStorage = (key, value) => {
    try {
      const data = {
        timestamp: new Date().toISOString(),
        value: value
      };
      sessionStorage.setItem(key, JSON.stringify(data));
      logDebug(`Stored in sessionStorage: ${key}`, { value: typeof value === 'object' ? '(object)' : value });
      return true;
    } catch (e) {
      logError(`Failed to store in sessionStorage: ${key}`, e.message);
      return false;
    }
  };

  // Fetch list of available Kite users
  const fetchKiteUsers = async () => {
    try {
      logDebug("Fetching available Kite users...");
      setLoading(true);
      
      const response = await api.getKiteUsers();
      
      if (response.success) {
        logDebug("Received Kite users", response.users);
        setKiteUsers(response.users);
        return response.users;
      } else {
        logDebug("Failed to fetch Kite users", response.error);
        setError(response.error || 'Failed to fetch Kite users');
        return [];
      }
    } catch (err) {
      logDebug("Error fetching Kite users", err.message);
      setError(err.message || 'An error occurred');
      return [];
    } finally {
      setKiteUsersLoaded(true);
      setLoading(false);
    }
  };
  
  // Fetch initial data provider info
  useEffect(() => {
    const fetchDataProviderInfo = async () => {
      try {
        logDebug("Fetching initial data provider info...");
        setLoading(true);
        
        // Fetch available Kite users
        const userList = await fetchKiteUsers();
        
        const info = await api.getDataProviderInfo();
        logDebug("Received data provider info:", info);
        
        // Enhanced debugging for user selection
        if (info.provider === 'kite' && info.user_id) {
          logDebug(`Setting Kite user to '${info.user_id}' with display name '${info.display_name}'`);
        }
        
        setDataProvider(info.provider);
        
        // Set display name with better validation
        if (info.display_name) {
          setDataProviderDisplayName(info.display_name);
        } else if (info.provider === 'kite' && info.user_id) {
          const capitalizedUser = info.user_id.charAt(0).toUpperCase() + info.user_id.slice(1);
          setDataProviderDisplayName(`Kite-${capitalizedUser}`);
        } else if (info.provider === 'kite') {
          setDataProviderDisplayName('Zerodha Kite');
        } else {
          setDataProviderDisplayName('Yahoo Finance');
        }
        
        // Set current Kite user if available
        if (info.user_id) {
          setCurrentKiteUser(info.user_id);
          logDebug(`Current Kite user set to '${info.user_id}'`);
        }
        
        // Check token validity if Kite is selected
        if (info.provider === 'kite') {
          await checkKiteToken(info.user_id);
        }
      } catch (err) {
        logDebug("Failed to fetch data provider info:", err.message);
        setError('Failed to connect to backend');
      } finally {
        setLoading(false);
      }
    };

    fetchDataProviderInfo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  
  // Generate provider options for the dropdown
  const getDataProviderOptions = useCallback(() => {
    const options = [
      { value: 'yahoo', label: 'Yahoo Finance' }
    ];
    
    // Add options for Kite users with compound values
    if (kiteUsers && kiteUsers.length > 0) {
      kiteUsers.forEach(user => {
        options.push({
          value: `kite:${user.user_id}`, // Changed: now using a compound value
          user_id: user.user_id,
          label: user.display_name,
          authenticated: user.authenticated
        });
      });
    } else if (!kiteUsersLoaded) {
      // If Kite users haven't been loaded yet, add a generic Kite option
      options.push({ value: 'kite', label: 'Zerodha Kite' });
    }
    
    return options;
  }, [kiteUsers, kiteUsersLoaded]);
  
  // Helper to get base provider without the user ID part
  const getBaseProvider = (providerValue) => {
    if (providerValue && typeof providerValue === 'string' && providerValue.includes(':')) {
      return providerValue.split(':')[0];
    }
    return providerValue;
  };
  
  // Change data provider
  const changeDataProvider = async (provider, userId = null) => {
    try {
      setLoading(true);
      setError(null);
      
      // Handle compound values (e.g., "kite:sushant")
      if (provider && provider.includes(':')) {
        const parts = provider.split(':');
        provider = parts[0];
        userId = parts[1] || userId;
      }
      
      logDebug(`Changing data provider to: ${provider}${userId ? ` for user: ${userId}` : ''}`);
      
      // Store the requested values for verification
      const requestedProvider = provider;
      const requestedUserId = userId;
      
      const response = await api.setDataProvider(provider, userId);
      
      if (response.success) {
        setDataProvider(response.provider);
        
        // Verify the response matches what we requested
        if (requestedProvider === 'kite' && requestedUserId && 
            response.user_id !== requestedUserId) {
          logDebug(`WARNING: Requested user '${requestedUserId}' but received '${response.user_id}'`);
        }
        
        // Set display name with better validation
        if (response.display_name) {
          logDebug(`Setting display name to: ${response.display_name}`);
          setDataProviderDisplayName(response.display_name);
        } else {
          // Fallback display name logic
          const displayName = response.provider === 'kite' 
            ? `Kite${userId ? `-${userId.charAt(0).toUpperCase() + userId.slice(1)}` : ''}`
            : 'Yahoo Finance';
          logDebug(`Setting fallback display name to: ${displayName}`);
          setDataProviderDisplayName(displayName);
        }
        
        if (response.user_id) {
          logDebug(`Setting current Kite user to: ${response.user_id}`);
          setCurrentKiteUser(response.user_id);
        } else if (provider === 'yahoo') {
          setCurrentKiteUser(null);
        }
        
        // Enhanced logging for requiresAuth state change
        const requiresAuthValue = response.requires_auth;
        logDebug(`Setting requiresAuth to:`, {
          newValue: requiresAuthValue,
          valueType: typeof requiresAuthValue,
          provider: response.provider,
          responseUserId: response.user_id,
          currentStateStack: new Error().stack.split('\n').slice(1, 3).join('\n')
        });
        
        // Debug storage for state transitions
        debugSessionStorage('lastProviderChange', {
          timestamp: new Date().toISOString(),
          provider: response.provider,
          userId: response.user_id,
          requiresAuth: requiresAuthValue,
          currentKiteUser: currentKiteUser
        });
        
        setRequiresAuth(requiresAuthValue);
        
        // If provider is Kite and authentication is required, set state
        if (provider === 'kite') {
          setTokenValid(!response.requires_auth);
        }
      } else {
        setError(response.error || 'Failed to change data provider');
      }
    } catch (err) {
      logDebug("Error changing data provider:", err.message);
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  // Check Kite token validity with enhanced debugging
  const checkKiteToken = async (userId = null, force = false) => {
    try {
      // Enhanced logging to track exactly what's being passed
      logDebug(`checkKiteToken called with:`, {
        userId: userId,
        userIdType: typeof userId,
        userIdStringified: String(userId),
        userIdIsBoolean: typeof userId === 'boolean',
        force: force,
        currentKiteUser: currentKiteUser,
        requiresAuth: requiresAuth,
        callStack: new Error().stack.split('\n').slice(1, 4).join('\n') // First few lines of stack trace
      });
      
      // Defensive check - if userId is literally 'true', use currentKiteUser instead
      if (userId === 'true' || userId === true) {
        logDebug(`Detected 'true' as userId, using currentKiteUser instead: ${currentKiteUser}`);
        userId = currentKiteUser;
      }
      
      // Add to session storage debug log
      logDebug(`Checking Kite token validity (force=${force}, userId=${userId || 'default'})`);
      debugSessionStorage('kiteTokenCheckStart', {
        userId,
        force,
        currentKiteUser,
        tokenValid,
        requiresAuth,
        timestamp: new Date().toISOString()
      });
      
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
      const response = await api.verifyKiteToken(userId);
      const endTime = performance.now();
      
      // Log API call performance
      logDebug(`Token verification API call completed in ${Math.round(endTime - startTime)}ms`, response);
      
      // Store the verification response for debugging
      debugSessionStorage('kiteTokenVerifyResponse', {
        response,
        userId,
        dataProvider,
        baseProvider: getBaseProvider(dataProvider),
        currentDropdownValue: dataProvider === 'kite' && currentKiteUser ? `kite:${currentKiteUser}` : dataProvider,
        timestamp: new Date().toISOString(),
        requestDuration: Math.round(endTime - startTime)
      });
      
      if (response.success) {
        logDebug(`Token verification result: ${response.valid}`);
        
        // Track state change
        const oldState = { tokenValid, requiresAuth };
        
        setTokenValid(response.valid);
        setRequiresAuth(!response.valid);
        setLastTokenCheck(now);
        
        // Update currentKiteUser if returned in the response
        if (response.user_id) {
          setCurrentKiteUser(response.user_id);
        }
        
        logDebug('Updated token state', {
          previous: oldState,
          current: { tokenValid: response.valid, requiresAuth: !response.valid },
          changed: (oldState.tokenValid !== response.valid || oldState.requiresAuth === response.valid)
        });
        
        // If token verification failed, update the user's authenticated status in the kiteUsers array
        if (kiteUsers.length > 0 && !response.valid && response.user_id) {
          const updatedUsers = kiteUsers.map(user => 
            user.user_id === response.user_id 
              ? { ...user, authenticated: false } 
              : user
          );
          setKiteUsers(updatedUsers);
        }
        
        return response.valid;
      } else {
        logDebug(`Token verification failed: ${response.error}`);
        setTokenValid(false);
        setRequiresAuth(true);
        setLastTokenCheck(now);
        return false;
      }
    } catch (err) {
      logError('Error checking Kite token:', err.message);
      
      // Log error details
      const errorInfo = {
        message: err.message,
        name: err.name,
        stack: err.stack ? err.stack.split('\n')[0] : 'No stack trace',
        userId: userId || 'default'
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
    
    // Get base provider (handle compound values)
    const baseProvider = getBaseProvider(dataProvider);
    
    // If past trading hours and we're using Kite, we should verify
    return baseProvider === 'kite' && isPastTradingHours;
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
          
          // Attempt to process the message even in the backup listener
          if (event.data.status === 'success' && event.data.provider === 'kite') {
            logDebug('Backup listener: Detected successful auth message, setting sessionStorage flag');
            sessionStorage.setItem('kiteAuthBackupSuccess', JSON.stringify({
              data: event.data,
              timestamp: new Date().toISOString(),
              handledBy: 'backupListener'
            }));
          }
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
  
  // Check sessionStorage for backup messages (poll)
  useEffect(() => {
    // Only run if using Kite provider
    if (dataProvider !== 'kite') return;
    
    const checkBackupStorage = () => {
      try {
        // Check for backup success message
        const backupSuccessStr = sessionStorage.getItem('kiteAuthBackupSuccess');
        if (backupSuccessStr) {
          const backupData = JSON.parse(backupSuccessStr);
          logDebug('Found backup auth success message in sessionStorage', backupData);
          
          // Process the backup message
          if (backupData.data && backupData.data.user_id) {
            // Clear the backup message to prevent reprocessing
            sessionStorage.removeItem('kiteAuthBackupSuccess');
            
            // Update state
            setTokenValid(true);
            setRequiresAuth(false);
            setError(null);
            
            if (backupData.data.user_id) {
              setCurrentKiteUser(backupData.data.user_id);
              logDebug(`Setting current Kite user from backup message: ${backupData.data.user_id}`);
            }
            
            // Force token verification just to be sure
            checkKiteToken(backupData.data.user_id, true);
          }
        }
        
        // Also check for messages directly stored by popup
        const directMessageStr = sessionStorage.getItem('kiteAuthMessage');
        if (directMessageStr) {
          logDebug('Found direct auth message in sessionStorage', JSON.parse(directMessageStr));
          // Remove after logging to prevent duplicates
          sessionStorage.removeItem('kiteAuthMessage');
        }
        
        // Check for local fallback message
        const localFallbackStr = sessionStorage.getItem('kiteAuthMessage_forParent');
        if (localFallbackStr) {
          logDebug('Found local fallback auth message', JSON.parse(localFallbackStr));
          // Process it similar to above
          try {
            const fallbackData = JSON.parse(localFallbackStr);
            sessionStorage.removeItem('kiteAuthMessage_forParent');
            
            if (fallbackData.status === 'success' && fallbackData.provider === 'kite') {
              setTokenValid(true);
              setRequiresAuth(false);
              
              if (fallbackData.user_id) {
                setCurrentKiteUser(fallbackData.user_id);
              }
              
              // Force token verification
              checkKiteToken(fallbackData.user_id, true);
              
              logDebug('Successfully processed fallback auth message');
            }
          } catch (e) {
            logError('Error processing fallback message', e.message);
          }
        }
      } catch (e) {
        logError('Error checking backup storage', e.message);
      }
    };
    
    // Check immediately and then every 2 seconds
    checkBackupStorage();
    const interval = setInterval(checkBackupStorage, 2000);
    
    return () => clearInterval(interval);
  }, [dataProvider, currentKiteUser]);
  
  // Handle messages from popup window with enhanced debugging
  const handleAuthMessage = useCallback(async (event) => {
    // Enhanced message logging with color
    console.log('%c[AUTH_MESSAGE_RECEIVED]', 'background: #4a148c; color: white; padding: 2px 6px; border-radius: 2px;', {
      hasData: !!event.data,
      dataType: event.data ? typeof event.data : 'undefined',
      origin: event.origin,
      eventType: event.type,
      source: event.source ? 'Window object' : 'null',
      timestamp: new Date().toISOString(),
      dataProvider: dataProvider,
      tokenValid: tokenValid,
      requiresAuth: requiresAuth,
      requiresAuthType: typeof requiresAuth,
      currentKiteUser: currentKiteUser,
      data: event.data,
      callStack: new Error().stack.split('\n').slice(1, 3).join('\n')
    });
    
    // Log detailed info for debugging
    const messageInfo = {
      hasData: !!event.data,
      dataType: event.data ? typeof event.data : 'undefined',
      origin: event.origin,
      eventType: event.type,
      source: event.source ? 'Window object' : 'null',
      timestamp: new Date().toISOString(),
      dataProvider: dataProvider,
      tokenValid: tokenValid,
      requiresAuth: requiresAuth,
      requiresAuthType: typeof requiresAuth,
      currentKiteUser: currentKiteUser,
      callStack: new Error().stack.split('\n').slice(1, 3).join('\n')
    };
    
    logDebug('Received message event', messageInfo);
    
    // Store in session storage for cross-window debugging
    debugSessionStorage('lastReceivedMessage', {
      data: event.data,
      origin: event.origin,
      time: new Date().toISOString()
    });
    
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
      
      // Extract user_id from the message if available
      const userId = event.data.user_id || currentKiteUser;
      
      // Store the successful message for debugging
      sessionStorage.setItem('lastKiteAuthSuccess', JSON.stringify({
        data: event.data,
        time: new Date().toISOString(),
        origin: event.origin,
        userId: userId
      }));
      
      // Set as Kite provider and update token status
      logDebug('Updating state after successful authentication');
      setDataProvider('kite');
      setTokenValid(true);
      setRequiresAuth(false);
      setError(null);
      
      // Update display name if we have a user_id
      if (userId) {
        setCurrentKiteUser(userId);
        setDataProviderDisplayName(`Kite-${userId.charAt(0).toUpperCase() + userId.slice(1)}`);
        
        // Update the user's authenticated status in the kiteUsers array
        if (kiteUsers.length > 0) {
          const updatedUsers = kiteUsers.map(user => 
            user.user_id === userId 
              ? { ...user, authenticated: true } 
              : user
          );
          setKiteUsers(updatedUsers);
        }
      } else {
        setDataProviderDisplayName('Zerodha Kite');
      }
      
      // Verify token to ensure everything is properly set up
      logDebug('Verifying token after authentication');
      try {
        const result = await checkKiteToken(userId, true);
        logDebug('Token verification result', { result, userId });
      } catch (error) {
        logDebug('Error verifying token', { error: error.message, userId });
      }
      
      // Log final state
      logDebug('Authentication process completed', {
        provider: 'kite',
        tokenValid: true,
        requiresAuth: false,
        userId: userId
      });
      
    } else if (event.data.status === 'failed' || event.data.status === 'error') {
      const reason = event.data.reason || 'Unknown error';
      logDebug('Authentication failed message received', { status: event.data.status, reason });
      
      // Extract user_id from the message if available
      const userId = event.data.user_id || currentKiteUser;
      
      // Store the failure message for debugging
      sessionStorage.setItem('lastKiteAuthFailure', JSON.stringify({
        data: event.data,
        time: new Date().toISOString(),
        origin: event.origin,
        userId: userId
      }));
      
      setError(`Authentication failed: ${reason}`);
      
      // Keep existing provider, but update token status if provider is Kite
      if (dataProvider === 'kite') {
        logDebug('Updating Kite provider state after authentication failure');
        setTokenValid(false);
        setRequiresAuth(true);
        
        // Update the user's authenticated status in the kiteUsers array
        if (kiteUsers.length > 0 && userId) {
          const updatedUsers = kiteUsers.map(user => 
            user.user_id === userId 
              ? { ...user, authenticated: false } 
              : user
          );
          setKiteUsers(updatedUsers);
        }
      }
    } else {
      logDebug('Unrecognized message format', event.data);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataProvider, tokenValid, requiresAuth, currentKiteUser, kiteUsers]);
  
  // Set up event listener for popup messages with detailed logging
  useEffect(() => {
    logDebug('Setting up component message event listener for auth popup');
    
    // Check if the provider is Kite - this helps with debugging
    logDebug('Current data provider state before attaching listener', { 
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
    
    // Create a wrapper handler with detailed logging
    const wrappedHandler = (event) => {
      console.log('%c[AUTH_MESSAGE_RAW]', 'background: #0277bd; color: white; padding: 2px 6px; border-radius: 2px;', {
        hasData: !!event.data,
        origin: event.origin,
        time: new Date().toISOString(),
        windowUrl: window.location.href,
        eventType: event.type,
        data: event.data
      });
      
      // Call the actual handler
      handleAuthMessage(event);
    };
    
    // Add the event listener with wrapped handler
    window.addEventListener('message', wrappedHandler);
    
    // Test if the listener is active
    setTimeout(() => {
      checkListenerActive();
    }, 500);
    
    // Clean up function
    return () => {
      logDebug('Removing component message event listener');
      sessionStorage.setItem('kiteAuthListenerActive', 'false');
      window.removeEventListener('message', wrappedHandler);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [handleAuthMessage]);
  
  // Expose the debug helpers for external use
  useEffect(() => {
    window.kiteAuthDebug = {
      checkListener: checkListenerActive,
      getLogs: () => JSON.parse(sessionStorage.getItem('kiteAuthLogs') || '[]'),
      getLastMessage: () => JSON.parse(sessionStorage.getItem('lastKiteAuthMessage') || 'null'),
      getState: () => ({
        dataProvider,
        dataProviderDisplayName,
        tokenValid,
        requiresAuth,
        error,
        currentKiteUser,
        kiteUsers,
        listenerActive: sessionStorage.getItem('kiteAuthListenerActive') === 'true',
        backupListenerActive: sessionStorage.getItem('kiteAuthBackupListener') === 'active',
        messageCount: parseInt(sessionStorage.getItem('kiteAuthMessageCount') || '0'),
        listenerCount: parseInt(sessionStorage.getItem('kiteAuthListenerCount') || '0')
      }),
      clearLogs: () => sessionStorage.removeItem('kiteAuthLogs'),
      testListener: checkListenerActive,
      testMessageManual: (data) => {
        // Allow manual testing of message handler
        console.log('Sending test message manually:', data);
        handleAuthMessage({
          data: data || {
            status: 'success',
            provider: 'kite',
            user_id: currentKiteUser || 'sushant',
            timestamp: new Date().toISOString(),
            messageId: 'manual_test_' + Date.now()
          },
          origin: window.location.origin,
          source: window
        });
        return 'Test message sent to handler';
      },
      // Debug backend communication directly
      openDebugger: () => {
        const userId = currentKiteUser || 'sushant';
        const debugUrl = `/api/kite/debug-auth?user_id=${userId}`;
        window.open(debugUrl, '_blank', 'width=800,height=600');
        return `Opened debugger for user ${userId}`;
      },
      checkOrigins: () => {
        return {
          windowOrigin: window.location.origin,
          documentDomain: document.domain,
          codespacesDomain: window.location.hostname.includes('.github.dev'),
          potentialPopupOrigins: [
            window.location.origin,
            'https://localhost:3001',
            'http://localhost:3001',
            window.location.origin.replace('3000', '3001'),
            window.location.origin.replace('-3000', '-3001')
          ]
        };
      },
      forceVerifyToken: (userId) => {
        return checkKiteToken(userId || currentKiteUser, true);
      }
    };
    
    console.log('%c[KITE DEBUG TOOLS AVAILABLE]', 'background:#2e7d32; color:white; padding:4px; border-radius:2px;', 
      'Use window.kiteAuthDebug to access debugging functions');
    
    return () => {
      delete window.kiteAuthDebug;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataProvider, dataProviderDisplayName, tokenValid, requiresAuth, error, currentKiteUser, kiteUsers]);
  
  // Initiate Kite authentication with enhanced debugging
  const initiateKiteAuth = async (userId = null) => {
    try {
      // Defensive check - if userId is literally 'true', use currentKiteUser instead
      if (userId === 'true' || userId === true) {
        logDebug(`Detected 'true' as userId, using currentKiteUser instead: ${currentKiteUser}`);
        userId = currentKiteUser;
      }
      
      setLoading(true);
      logDebug(`Initiating Kite authentication with params:`, {
        userId: userId,
        userIdType: typeof userId,
        userIdStringified: String(userId),
        currentKiteUser: currentKiteUser,
        currentKiteUserType: typeof currentKiteUser,
        dataProvider: dataProvider,
        tokenValid: tokenValid,
        requiresAuth: requiresAuth,
        callStack: new Error().stack.split('\n').slice(1, 4).join('\n')
      });
      
      // Log current state before initiating auth
      logDebug("Current state before authentication", {
        dataProvider,
        tokenValid,
        requiresAuth,
        currentKiteUser,
        requestedUser: userId,
        listenerActive: sessionStorage.getItem('kiteAuthListenerActive') === 'true'
      });
      
      // Clear previous authentication tracking
      sessionStorage.setItem('kiteAuthStarted', new Date().toISOString());
      sessionStorage.removeItem('lastKiteAuthSuccess');
      sessionStorage.removeItem('lastKiteAuthFailure');
      sessionStorage.removeItem('kiteAuthMessage');
      sessionStorage.removeItem('kiteAuthMessage_forParent');
      sessionStorage.removeItem('kiteAuthBackupSuccess');
      
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
      
      const response = await api.getKiteLoginUrl(userId || currentKiteUser);
      
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
              logDebug("Popup closed without receiving auth message - verifying token status");
              // Check token status after a delay
              setTimeout(async () => {
                logDebug("Checking token status after popup closed");
                const isValid = await checkKiteToken(userId || currentKiteUser, true);
                logDebug(`Token check after popup close: ${isValid ? 'valid' : 'invalid'}`);
                
                // If token is valid, update the state directly
                if (isValid && dataProvider === 'kite') {
                  logDebug('Token valid after popup close - updating state');
                  setTokenValid(true);
                  setRequiresAuth(false);
                  setError(null);
                  
                  // Store this state change for debugging
                  debugSessionStorage('postPopupStateUpdate', {
                    userId: userId || currentKiteUser,
                    tokenValid: true,
                    requiresAuth: false,
                    timestamp: new Date().toISOString()
                  });
                }
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
  
  // Refresh Kite users list
  const refreshKiteUsers = async () => {
    return await fetchKiteUsers();
  };
  
  return (
    <DataSourceContext.Provider
      value={{
        dataProvider,
        dataProviderDisplayName,
        loading,
        error,
        requiresAuth,
        tokenValid,
        kiteUsers,
        currentKiteUser,
        getDataProviderOptions,
        changeDataProvider,
        checkKiteToken,
        initiateKiteAuth,
        shouldVerifyToken,
        refreshKiteUsers,
        getBaseProvider // Add our new utility function
      }}
    >
      {children}
    </DataSourceContext.Provider>
  );
};
