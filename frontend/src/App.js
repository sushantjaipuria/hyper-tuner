import React, { useState, useEffect, useContext } from 'react';
import './App.css';
import StrategyTuner from './components/StrategyTuner';
import api from './services/api';
import { DataSourceContext, DataSourceProvider } from './context/DataSourceContext';
import KiteAuthModal from './components/KiteAuthModal';

function AppContent() {
  // Setup global debugging tools
  useEffect(() => {
    // Setup cross-window debugging
    window.debugKiteAuth = {
      windowInfo: {
        url: window.location.href,
        origin: window.location.origin,
        host: window.location.host,
        protocol: window.location.protocol
      },
      checkMessage: (testMessage) => {
        console.log('%c[DEBUG] Test message received', 'background: #1e88e5; color: white; padding: 2px 6px; border-radius: 2px;', testMessage);
        return 'Response from main window at ' + new Date().toISOString();
      },
      securityPolicies: {
        crossOriginIsolated: window.crossOriginIsolated || false,
        isSecureContext: window.isSecureContext || false
      },
      testPostMessage: () => {
        const testWindow = window.open('', '_blank');
        if (testWindow) {
          testWindow.document.write(`
            <html>
              <head><title>PostMessage Test Window</title></head>
              <body>
                <h3>Test Window</h3>
                <div id="log" style="font-family: monospace; margin-top: 20px;"></div>
                <script>
                  function log(msg) {
                    console.log(msg);
                    document.getElementById('log').innerHTML += '<div>' + msg + '</div>';
                  }
                  log("Test window opened");
                  log("Opener exists: " + (window.opener !== null));
                  log("Attempting to send message to parent...");
                  
                  try {
                    window.opener.postMessage({
                      type: "test", 
                      message: "Hello from test window",
                      time: new Date().toISOString()
                    }, "*");
                    log("Message sent with wildcard origin");
                    
                    // Try with specific origin
                    setTimeout(() => {
                      try {
                        const parentOrigin = window.opener.location.origin;
                        log("Parent origin: " + parentOrigin);
                        window.opener.postMessage({
                          type: "test", 
                          message: "Hello with specific origin",
                          time: new Date().toISOString()
                        }, parentOrigin);
                        log("Message sent with specific origin");
                      } catch(e) {
                        log("Error sending with specific origin: " + e.message);
                      }
                    }, 1000);
                  } catch(e) {
                    log("Error sending message: " + e.message);
                  }
                  
                  // Listen for messages
                  window.addEventListener('message', function(event) {
                    log("Received message from parent: " + JSON.stringify(event.data));
                  });
                  
                  // Close after delay
                  setTimeout(() => {
                    log("Closing window...");
                    window.close();
                  }, 5000);
                </script>
              </body>
            </html>
          `);
          console.log('%c[DEBUG] Test window opened, waiting for message...', 'background: #1e88e5; color: white; padding: 2px 6px; border-radius: 2px;');
        } else {
          console.error('%c[DEBUG] Failed to open test window - popup blocked?', 'background: #d32f2f; color: white; padding: 2px 6px; border-radius: 2px;');
        }
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
      debugKiteAuthModal: () => {
        // Manually show auth modal for debugging
        setShowAuthModal(true);
        return 'Auth modal opened for debugging';
      }
    };
    
    // Set up listener for test messages
    const testMessageListener = (event) => {
      if (event.data && event.data.type === 'test') {
        console.log('%c[DEBUG] Received test message from popup window', 'background: #1e88e5; color: white; padding: 2px 6px; border-radius: 2px;', {
          message: event.data,
          origin: event.origin,
          source: event.source ? 'Window object' : 'null',
          time: new Date().toISOString()
        });
        
        // Send response back if possible
        try {
          if (event.source) {
            event.source.postMessage({
              type: 'test-response',
              message: 'Message received by parent',
              time: new Date().toISOString()
            }, '*');
            console.log('%c[DEBUG] Response sent back to test window', 'background: #43a047; color: white; padding: 2px 6px; border-radius: 2px;');
          }
        } catch(e) {
          console.error('Error responding to test window:', e);
        }
      }
    };
    
    window.addEventListener('message', testMessageListener);
    
    console.log('%c[GLOBAL DEBUG TOOLS AVAILABLE]', 'background:#2e7d32; color:white; padding:4px; border-radius:2px;', 
      'Use window.debugKiteAuth to access global debugging functions');
    
    return () => {
      window.removeEventListener('message', testMessageListener);
      delete window.debugKiteAuth;
    };
  }, []);
  const { 
    dataProvider, 
    dataProviderDisplayName,
    loading, 
    error, 
    requiresAuth,
    changeDataProvider,
    getDataProviderOptions,
    refreshKiteUsers,
    currentKiteUser,
    getBaseProvider
  } = useContext(DataSourceContext);
  
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [refreshingUsers, setRefreshingUsers] = useState(false);
  
  // Function to determine the current dropdown value based on provider and user
  const getCurrentDropdownValue = () => {
    if (!dataProvider) return 'yahoo'; // Default fallback
    
    if (dataProvider === 'kite' && currentKiteUser) {
      return `kite:${currentKiteUser}`;
    } else if (typeof dataProvider === 'string' && dataProvider.includes(':')) {
      // Already in compound format
      return dataProvider;
    }
    
    return dataProvider;
  };
  
  // Show auth modal if Kite requires authentication
  useEffect(() => {
    // Get the base provider without the user ID part
    const baseProvider = getBaseProvider(dataProvider);
    
    if (requiresAuth && baseProvider === 'kite') {
      setShowAuthModal(true);
    } else {
      setShowAuthModal(false);
    }
  }, [requiresAuth, dataProvider, getBaseProvider]);
  
  // Create debug helper for authentication diagnostics
  useEffect(() => {
    window.debugKiteAuthFlow = {
      getState: () => ({
        dataProvider,
        dataProviderDisplayName,
        requiresAuth,
        showAuthModal,
        currentKiteUser,
        apiUrl: api.getApiUrl(),
        windowContext: {
          url: window.location.href,
          hash: window.location.hash,
          isCodespaces: window.location.hostname.includes('.github.dev')
        }
      }),
      testMessageListener: () => {
        console.log('%c[DEBUG] Testing message listener...', 'background: #f57c00; color: white; padding: 2px 6px; border-radius: 2px;');
        window.postMessage({
          type: 'test',
          source: 'debugger',
          time: new Date().toISOString()
        }, '*');
      },
      forceAuthModal: (show) => {
        setShowAuthModal(show !== false);
      }
    };
    
    return () => {
      delete window.debugKiteAuthFlow;
    };
  }, [dataProvider, dataProviderDisplayName, requiresAuth, showAuthModal, currentKiteUser]);

  // Handle URL hash for authentication callback
  useEffect(() => {
    const handleAuthCallback = () => {
      const hash = window.location.hash;
      
      if (hash.startsWith('#auth-success')) {
        console.log('Kite authentication successful');
        // Remove hash from URL
        window.history.replaceState(null, document.title, window.location.pathname);
        // Close modal
        setShowAuthModal(false);
      } else if (hash.startsWith('#auth-failed') || hash.startsWith('#auth-error')) {
        console.error('Kite authentication failed', hash);
        // Remove hash from URL
        window.history.replaceState(null, document.title, window.location.pathname);
      }
    };
    
    handleAuthCallback();
  }, []);
  
  // Handle data provider selection change
  const handleProviderChange = (e) => {
    const value = e.target.value;
    let providerName, userId;
    
    // Parse compound values like "kite:sushant"
    if (value.includes(':')) {
      [providerName, userId] = value.split(':');
    } else {
      // Handle simple values like "yahoo"
      providerName = value;
      const selectedIndex = e.target.selectedIndex;
      const selectedOption = e.target.options[selectedIndex];
      userId = selectedOption.getAttribute('data-user-id');
    }
    
    // Log the selection (helpful for debugging)
    console.log('Provider change:', { 
      rawValue: value,
      parsedProvider: providerName,
      parsedUserId: userId
    });
    
    // Call changeDataProvider with the extracted provider and userId
    changeDataProvider(providerName, userId);
  };
  
  // Handle refresh button click
  const handleRefreshUsers = async () => {
    setRefreshingUsers(true);
    await refreshKiteUsers();
    setRefreshingUsers(false);
  };
  
  return (
    <div className="bg-gray-100 min-h-screen">
      <header className="bg-blue-700 text-white p-4 shadow-md">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">Trading Strategy Hyper-Tuner</h1>
            <p className="text-sm opacity-80">Optimize your trading strategies with Bayesian optimization</p>
          </div>
          <div className="flex items-center">
            {!loading && (
              <div className="bg-blue-800 px-3 py-1 rounded-full text-sm flex items-center mr-2">
                <span className="mr-2">Data Source:</span>
                <select
                  className="bg-blue-700 border border-blue-600 rounded px-2 py-1 text-white"
                  value={getCurrentDropdownValue()}
                  onChange={handleProviderChange}
                >
                  {(() => {
                    const options = getDataProviderOptions();
                    // Log dropdown state for debugging
                    console.log('Dropdown rendering:', {
                      options,
                      currentValue: getCurrentDropdownValue(),
                      dataProvider,
                      currentKiteUser
                    });
                    return options.map((option, index) => (
                      <option 
                        key={`${option.value}-${option.user_id || index}`}
                        value={option.value}
                        data-user-id={option.user_id}
                      >
                        {option.label} {option.authenticated === false ? '(Login Required)' : ''}
                      </option>
                    ));
                  })()}
                </select>
                <button
                  className="ml-2 text-xs bg-blue-600 hover:bg-blue-700 rounded p-1"
                  onClick={handleRefreshUsers}
                  disabled={refreshingUsers}
                  title="Refresh data sources"
                >
                  {refreshingUsers ? '...' : '↻'}
                </button>
                <span className={`ml-2 w-2 h-2 rounded-full ${dataProvider === 'yahoo' ? 'bg-yellow-400' : 'bg-green-400'}`}></span>
              </div>
            )}
            
            {/* Debug status with API URL - only in development or when error occurs */}
            {(process.env.NODE_ENV === 'development' || error) && (
              <div className={`px-3 py-1 rounded-full text-sm flex items-center ${error ? 'bg-red-700' : 'bg-blue-900'}`}>
                <span className="mr-2">API:</span>
                <span className="font-mono text-xs truncate max-w-[200px]" title={api.getApiUrl()}>
                  {api.getApiUrl()}
                </span>
                {error ? (
                  <span className="ml-2 w-2 h-2 rounded-full bg-red-400"></span>
                ) : (
                  <span className="ml-2 w-2 h-2 rounded-full bg-green-400"></span>
                )}
              </div>
            )}
          </div>
        </div>
      </header>
      <main className="container mx-auto py-6 px-4">
        <StrategyTuner />
      </main>
      <footer className="bg-gray-800 text-white p-4 text-center">
        <p className="text-sm">© 2024 Trading Strategy Hyper-Tuner</p>
      </footer>
      
      {/* Kite Authentication Modal */}
      <KiteAuthModal 
        isOpen={showAuthModal} 
        onClose={() => setShowAuthModal(false)}
        userId={currentKiteUser}
      />
    </div>
  );
}

function App() {
  return (
    <DataSourceProvider>
      <AppContent />
    </DataSourceProvider>
  );
}

export default App;
