import React, { useState, useEffect } from 'react';
import './App.css';
import StrategyTuner from './components/StrategyTuner';
import api from './services/api';

function App() {
  const [dataProvider, setDataProvider] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDataProviderInfo = async () => {
      try {
        const info = await api.getDataProviderInfo();
        setDataProvider(info.provider);
        setLoading(false);
      } catch (err) {
        setError('Failed to connect to backend');
        setLoading(false);
      }
    };

    fetchDataProviderInfo();
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
            {dataProvider && (
              <div className="bg-blue-800 px-3 py-1 rounded-full text-sm flex items-center mr-2">
                <span className="mr-2">Data Source:</span>
                <span className="font-semibold">
                  {dataProvider === 'yahoo' ? 'Yahoo Finance' : 'Zerodha Kite'}
                </span>
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
    </div>
  );
}

export default App;
