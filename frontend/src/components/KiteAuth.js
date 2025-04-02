import React, { useState, useEffect } from 'react';
import api from '../services/api';

const KiteAuth = ({ onAuthSuccess }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [errorDetails, setErrorDetails] = useState(null);
  const [authStatus, setAuthStatus] = useState({ authenticated: false });
  const [traceId, setTraceId] = useState(null);

  useEffect(() => {
    // Check for auth_status and errors in URL (callback from Kite)
    const urlParams = new URLSearchParams(window.location.search);
    const authStatusParam = urlParams.get('auth_status');
    const errorParam = urlParams.get('error');
    const traceIdParam = urlParams.get('trace_id');
    
    if (traceIdParam) {
      setTraceId(traceIdParam);
      console.log(`Auth flow trace ID: ${traceIdParam}`);
    }
    
    if (authStatusParam) {
      if (authStatusParam === 'success') {
        console.log('Authentication successful via URL callback');
        setAuthStatus({ authenticated: true });
        localStorage.setItem('kite_auth_state', JSON.stringify({
          authenticated: true,
          timestamp: Date.now()
        }));
        onAuthSuccess();
        
        // Clear the URL params
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
      } else if (authStatusParam === 'failed' || authStatusParam === 'error') {
        const errorMsg = errorParam || 'Authentication failed';
        console.error(`Authentication error: ${errorMsg}`);
        setError(errorMsg);
        setLoading(false);
        
        // Clear the URL params after a short delay (to allow logging)
        setTimeout(() => {
          window.history.replaceState({}, document.title, window.location.pathname);
        }, 500);
        return;
      }
    }
    
    // Check if we have a stored auth state
    const storedAuthState = localStorage.getItem('kite_auth_state');
    if (storedAuthState) {
      try {
        const authState = JSON.parse(storedAuthState);
        // Only trust stored state if it's recent (last 10 minutes)
        const isRecent = (Date.now() - authState.timestamp) < (10 * 60 * 1000);
        
        if (authState.authenticated && isRecent) {
          console.log('Using stored authentication state');
          // Verify with backend
          checkAuthStatus(true);
          return;
        }
      } catch (e) {
        console.error('Error parsing stored auth state:', e);
      }
    }
    
    // Otherwise check current auth status
    checkAuthStatus();
  }, [onAuthSuccess]);

  const checkAuthStatus = async (usingStoredState = false) => {
    try {
      setLoading(true);
      if (usingStoredState) {
        console.log('Verifying stored authentication state with server');
      } else {
        console.log('Checking authentication status with server');
      }
      
      const response = await api.kiteAuthStatus();
      
      if (response.success) {
        setAuthStatus({
          authenticated: response.authenticated,
          provider: response.provider,
          timestamp: response.timestamp
        });
        
        // Update localStorage if authenticated
        if (response.authenticated) {
          localStorage.setItem('kite_auth_state', JSON.stringify({
            authenticated: true,
            timestamp: Date.now()
          }));
          onAuthSuccess();
        } else if (usingStoredState) {
          // Clear invalid stored state
          localStorage.removeItem('kite_auth_state');
        }
      } else {
        setError(response.error || 'Failed to check authentication status');
        setErrorDetails(response.errorDetails || null);
        
        // Clear invalid stored state
        localStorage.removeItem('kite_auth_state');
      }
    } catch (err) {
      setError(err.message || 'An error occurred');
      
      // Clear invalid stored state
      localStorage.removeItem('kite_auth_state');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    try {
      setLoading(true);
      setError(null);
      setErrorDetails(null);
      
      console.log('Initiating Kite login process');
      const response = await api.kiteAuth();
      
      if (response.success) {
        if (response.authenticated) {
          // Already authenticated
          console.log('Already authenticated with Kite');
          setAuthStatus({ authenticated: true });
          localStorage.setItem('kite_auth_state', JSON.stringify({
            authenticated: true,
            timestamp: Date.now()
          }));
          onAuthSuccess();
        } else if (response.login_url) {
          // Need to redirect to Kite login
          console.log('Redirecting to Kite login page');
          
          // Get current URL for the redirect back
          const currentUrl = window.location.origin;
          
          // Redirect to Kite login page with redirect parameter
          const redirectUrl = `${response.login_url}&redirect_uri=${encodeURIComponent(currentUrl)}`;
          window.location.href = redirectUrl;
        } else {
          setError('Invalid response from server');
        }
      } else {
        setError(response.error || 'Failed to generate login URL');
        setErrorDetails(response.errorDetails || null);
      }
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Show debugging information in development mode
  const renderDebugInfo = () => {
    if (process.env.NODE_ENV !== 'development' && !traceId) return null;
    
    return (
      <div className="mt-4 p-3 bg-gray-100 rounded text-xs font-mono text-gray-700">
        <div className="font-bold mb-1">Debug Info:</div>
        {traceId && <div>Trace ID: {traceId}</div>}
        <div>Auth Status: {JSON.stringify(authStatus)}</div>
        {errorDetails && <div>Error Details: {JSON.stringify(errorDetails)}</div>}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700"></div>
        <p className="mt-4 text-gray-600">Checking authentication status...</p>
        {renderDebugInfo()}
      </div>
    );
  }

  if (authStatus.authenticated) {
    return (
      <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-md text-center mb-4">
        <p>Successfully authenticated with Kite!</p>
        <p className="text-sm mt-2">Redirecting to the trading dashboard...</p>
        {renderDebugInfo()}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-8 max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Kite API Authentication</h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      )}
      
      <div className="mb-6 text-center">
        <p className="text-gray-600 mb-4">
          You need to authenticate with your Zerodha Kite account to use the Kite API.
        </p>
        <p className="text-gray-600 mb-4">
          Click the button below to login to your Kite account. You'll be redirected back to this app after authentication.
        </p>
      </div>
      
      <div className="flex justify-center">
        <button
          onClick={handleLogin}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-md flex items-center"
        >
          {loading ? (
            <>
              <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
              Connecting...
            </>
          ) : (
            <>
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
              </svg>
              Login with Zerodha Kite
            </>
          )}
        </button>
      </div>
      
      {renderDebugInfo()}
    </div>
  );
};

export default KiteAuth;