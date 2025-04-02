import React, { useState, useEffect, useContext } from 'react';
import './App.css';
import StrategyTuner from './components/StrategyTuner';
import api from './services/api';
import { DataSourceContext, DataSourceProvider } from './context/DataSourceContext';
import KiteAuthModal from './components/KiteAuthModal';

function AppContent() {
  const { 
    dataProvider, 
    loading, 
    error, 
    requiresAuth,
    changeDataProvider
  } = useContext(DataSourceContext);
  
  const [showAuthModal, setShowAuthModal] = useState(false);
  
  // Show auth modal if Kite requires authentication
  useEffect(() => {
    if (requiresAuth && dataProvider === 'kite') {
      setShowAuthModal(true);
    } else {
      setShowAuthModal(false);
    }
  }, [requiresAuth, dataProvider]);
  
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
                  value={dataProvider}
                  onChange={(e) => changeDataProvider(e.target.value)}
                >
                  <option value="yahoo">Yahoo Finance</option>
                  <option value="kite">Zerodha Kite</option>
                </select>
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
