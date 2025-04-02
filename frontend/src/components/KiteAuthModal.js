import React, { useContext, useState, useEffect } from 'react';
import { DataSourceContext } from '../context/DataSourceContext';

const KiteAuthModal = ({ isOpen, onClose }) => {
  const { initiateKiteAuth, changeDataProvider, tokenValid, requiresAuth, checkKiteToken } = useContext(DataSourceContext);
  const [isLoading, setIsLoading] = useState(false);
  const [debugVisible, setDebugVisible] = useState(false);
  const [debugInfo, setDebugInfo] = useState({});
  
  // Debug logging helper
  const logModalDebug = (message, data = null) => {
    const timestamp = new Date().toISOString();
    console.log('%c[KiteAuthModal]', 'color: #2196f3; font-weight: bold', `[${timestamp}] ${message}`, data || '');
    
    // Update session storage for debugging
    const modalLogs = JSON.parse(sessionStorage.getItem('kiteAuthModalLogs') || '[]');
    modalLogs.push({ timestamp, message, data: data ? JSON.stringify(data) : null });
    if (modalLogs.length > 20) modalLogs.shift();
    sessionStorage.setItem('kiteAuthModalLogs', JSON.stringify(modalLogs));
  };
  
  // Track modal opens and closures
  useEffect(() => {
    if (isOpen) {
      logModalDebug('Kite auth modal opened', { tokenValid, requiresAuth });
      sessionStorage.setItem('kiteAuthModalOpened', new Date().toISOString());
    }
  }, [isOpen, tokenValid, requiresAuth]);
  
  // When the modal is open, refresh debug info
  useEffect(() => {
    if (!isOpen || !debugVisible) return;
    
    const updateDebugInfo = () => {
      // Gather state information for debugging
      const info = {
        sessionStorage: {
          kiteAuthListenerActive: sessionStorage.getItem('kiteAuthListenerActive') || 'not set',
          kiteAuthBackupListener: sessionStorage.getItem('kiteAuthBackupListener') || 'not set',
          kiteAuthMessageCount: sessionStorage.getItem('kiteAuthMessageCount') || '0',
          lastKiteAuthSuccess: sessionStorage.getItem('lastKiteAuthSuccess') ? 'present' : 'none',
          lastKiteAuthFailure: sessionStorage.getItem('lastKiteAuthFailure') ? 'present' : 'none',
        },
        context: {
          tokenValid,
          requiresAuth,
          timestamp: new Date().toISOString()
        }
      };
      
      setDebugInfo(info);
    };
    
    // Initial update
    updateDebugInfo();
    
    // Update every second while debug is visible
    const interval = setInterval(updateDebugInfo, 1000);
    
    return () => clearInterval(interval);
  }, [isOpen, debugVisible, tokenValid, requiresAuth]);
  
  const handleLoginClick = async () => {
    logModalDebug('Login button clicked');
    setIsLoading(true);
    
    try {
      // Check if message listener is active
      if (window.kiteAuthDebug && typeof window.kiteAuthDebug.checkListener === 'function') {
        const listenerActive = window.kiteAuthDebug.checkListener();
        logModalDebug(`Message listener pre-check: ${listenerActive ? 'active' : 'inactive'}`);
      }
      
      // Initiate authentication
      await initiateKiteAuth();
      logModalDebug('initiateKiteAuth completed');
      
    } catch (err) {
      logModalDebug('Error during authentication', err.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleCancelClick = () => {
    logModalDebug('Cancel button clicked');
    // Switch back to Yahoo Finance
    changeDataProvider('yahoo');
    sessionStorage.setItem('kiteAuthModalClosed', new Date().toISOString());
    onClose();
  };
  
  const handleManualCheck = async () => {
    logModalDebug('Manual token check requested');
    setIsLoading(true);
    
    try {
      const result = await checkKiteToken(true);
      logModalDebug('Manual token check completed', { valid: result });
    } catch (err) {
      logModalDebug('Error checking token', err.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const toggleDebugInfo = () => {
    setDebugVisible(!debugVisible);
    logModalDebug(`Debug info ${!debugVisible ? 'shown' : 'hidden'}`);
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <h3 className="text-lg font-medium mb-4">Kite Authentication Required</h3>
        <p className="mb-4">
          To use Zerodha Kite as a data source, you need to authenticate with your Kite account.
          Click the button below to start the authentication process.
        </p>
        
        {/* Debug information section */}
        {debugVisible && (
          <div className="mb-4 p-3 bg-gray-100 rounded text-xs">
            <h4 className="font-bold mb-1">Debug Information</h4>
            <p>Token valid: {tokenValid ? 'Yes' : 'No'}</p>
            <p>Requires auth: {requiresAuth ? 'Yes' : 'No'}</p>
            <p>Listener active: {debugInfo?.sessionStorage?.kiteAuthListenerActive || 'Unknown'}</p>
            <p>Backup listener: {debugInfo?.sessionStorage?.kiteAuthBackupListener || 'Unknown'}</p>
            <p>Message count: {debugInfo?.sessionStorage?.kiteAuthMessageCount || '0'}</p>
            <p>Success message: {debugInfo?.sessionStorage?.lastKiteAuthSuccess || 'None'}</p>
            <p>Failure message: {debugInfo?.sessionStorage?.lastKiteAuthFailure || 'None'}</p>
            <p className="mt-2">Updated: {debugInfo?.context?.timestamp || 'Unknown'}</p>
          </div>
        )}
        
        <div className="flex flex-wrap justify-between items-center mb-4">
          <button 
            onClick={toggleDebugInfo}
            className="text-xs text-gray-500 hover:text-gray-700 underline"
          >
            {debugVisible ? 'Hide Debug Info' : 'Show Debug Info'}
          </button>
          
          {debugVisible && (
            <button
              className="text-xs bg-gray-200 hover:bg-gray-300 px-2 py-1 rounded ml-2"
              onClick={handleManualCheck}
              disabled={isLoading}
            >
              Manual Token Check
            </button>
          )}
        </div>
        
        <div className="flex justify-end space-x-3">
          <button
            className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
            onClick={handleCancelClick}
            disabled={isLoading}
          >
            Cancel
          </button>
          <button
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
            onClick={handleLoginClick}
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : 'Login to Kite'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default KiteAuthModal;
