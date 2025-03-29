import React, { useState } from 'react';
import StrategyCreation from '../screens/StrategyCreation';
import BacktestParameters from '../screens/BacktestParameters';
import HyperTuning from '../screens/HyperTuning';
import Results from '../screens/Results';
import api from '../services/api';

const StrategyTuner = () => {
  const [activeTab, setActiveTab] = useState('strategy');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Strategy data
  const [strategy, setStrategy] = useState({
    name: '',
    type: 'buy',
    symbol: '',
    timeframe: '',
    entry_conditions: [],
    exit_conditions: []
  });
  
  // Backtest parameters
  const [backtestParams, setBacktestParams] = useState({
    initial_capital: 100000,
    start_date: '',
    end_date: ''
  });
  
  // Results data
  const [backtestResults, setBacktestResults] = useState(null);
  const [optimizationResults, setOptimizationResults] = useState(null);
  const [optimizationId, setOptimizationId] = useState(null);
  const [optimizationStatus, setOptimizationStatus] = useState(null);
  
  // Handle strategy save
  const handleSaveStrategy = async (strategyData) => {
    try {
      setLoading(true);
      setError(null);
      
      // Update strategy with form data
      const updatedStrategy = { ...strategy, ...strategyData };
      setStrategy(updatedStrategy);
      
      // Save strategy to backend
      const response = await api.saveStrategy(updatedStrategy);
      
      // Update strategy with response data
      if (response.success) {
        setStrategy({ ...updatedStrategy, strategy_id: response.strategy_id });
        setActiveTab('backtest'); // Move to next tab
      } else {
        setError(response.error || 'Failed to save strategy');
      }
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  // Handle backtest run
  const handleRunBacktest = async (backtestData) => {
    try {
      setLoading(true);
      setError(null);
      
      // Update backtest params with form data
      const updatedParams = { ...backtestParams, ...backtestData };
      setBacktestParams(updatedParams);
      
      // Run backtest
      const response = await api.runBacktest({
        strategy_id: strategy.strategy_id,
        ...updatedParams
      });
      
      // Update backtest results
      if (response.success) {
        setBacktestResults(response);
        setActiveTab('tuning'); // Move to next tab
      } else {
        setError(response.error || 'Failed to run backtest');
      }
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  // Handle optimization run
  const handleRunOptimization = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Run optimization
      const response = await api.runOptimization({
        strategy_id: strategy.strategy_id,
        backtest_id: backtestResults.backtest_id
      });
      
      // Update optimization results
      if (response.success) {
        setOptimizationId(response.optimization_id);
        setOptimizationResults(response);
        
        // Start polling for optimization status
        pollOptimizationStatus(response.optimization_id);
      } else {
        setError(response.error || 'Failed to run optimization');
      }
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  // Poll optimization status with debugging
  const pollOptimizationStatus = async (optimizationId) => {
    try {
      console.log(`[DEBUG] Polling optimization status for ID: ${optimizationId}`);
      const response = await api.getOptimizationStatus(optimizationId);
      
      if (response.success && response.status) {
        // Set state with received status
        setOptimizationStatus(response.status);
        
        // Log basic information
        console.log(`[DEBUG] Status: ${response.status.status}, Progress: ${response.status.progress}%`);
        console.log(`[DEBUG] Strategy data available: ${!!strategy}, Strategy ID: ${strategy?.strategy_id}`);
        
        if (response.status.iteration_results) {
          console.log(`[DEBUG] Got ${response.status.iteration_results.length} iteration results`);
        }
        
        // If optimization is still running, poll again after 2 seconds
        if (response.status.status === 'running' || 
            response.status.status === 'running iteration' || 
            response.status.status === 'starting') {
          // Continue polling while optimization is running
          setTimeout(() => pollOptimizationStatus(optimizationId), 2000);
        } else if (response.status.status === 'completed') {
          // Optimization completed
          console.log(`Optimization completed successfully`);
          
          // Finalize results with comparison data
          let comparisonData = response.status.comparison;
          
          // Validate comparison data and create fallback if necessary
          if (!comparisonData || !comparisonData.original || !comparisonData.optimized) {
            console.warn("Incomplete comparison data, creating fallback");
            
            // Default metrics template
            const defaultMetrics = {
              returns: 0,
              win_rate: 0,
              max_drawdown: 0,
              sharpe_ratio: 0,
              trade_count: 0
            };
            
            // Create fallback using available data
            comparisonData = {
              original: comparisonData?.original || {
                ...defaultMetrics,
                ...backtestResults?.summary
              },
              optimized: comparisonData?.optimized || {
                ...defaultMetrics,
                returns: response.status.best_result || 0
              }
            };
          }
          
          // Update optimization results
          setOptimizationResults({
            ...optimizationResults,
            optimization_id: optimizationId,
            comparison: comparisonData,
            status: response.status  // Include the complete status object
          });
          
          // Move to results tab after a short delay to allow UI to update
          setTimeout(() => {
            console.log('[DEBUG] Moving to results tab with data:', {
              strategy_id: strategy.strategy_id,
              backtestResults,
              optimizationId,
              optimizationResults: {
                ...optimizationResults,
                optimization_id: optimizationId,
                comparison: comparisonData,
                status: response.status
              }
            });
            setActiveTab('results');
          }, 500);
        } else if (response.status.status === 'failed' || response.status.status === 'error') {
          // Optimization failed
          console.error(`Optimization failed: ${response.status.error || 'Unknown error'}`);
          setError(`Optimization failed: ${response.status.error || 'Unknown error'}`);
        }
      } else {
        // Handle error in the response
        const errorMsg = response.error || 'Failed to get optimization status';
        console.error(`Status request failed: ${errorMsg}`);
        
        // Still retry a few times before giving up
        if (window.pollAttempts === undefined) {
          window.pollAttempts = 1;
        } else {
          window.pollAttempts++;
        }
        
        // Retry up to 5 times with exponential backoff
        if (window.pollAttempts <= 5) {
          const delay = Math.min(2000 * Math.pow(1.5, window.pollAttempts), 10000);
          console.log(`Retrying in ${delay}ms (attempt ${window.pollAttempts} of 5)`);
          setTimeout(() => pollOptimizationStatus(optimizationId), delay);
        } else {
          setError(errorMsg);
          window.pollAttempts = undefined; // Reset for next time
        }
      }
    } catch (err) {
      console.error(`Error polling optimization status: ${err.message}`);
      
      // Still retry a few times on error
      if (window.pollRetries === undefined) {
        window.pollRetries = 1;
      } else {
        window.pollRetries++;
      }
      
      // Retry up to 3 times with exponential backoff
      if (window.pollRetries <= 3) {
        const delay = 2000 * Math.pow(2, window.pollRetries);
        console.log(`Error occurred, retrying in ${delay}ms`);
        setTimeout(() => pollOptimizationStatus(optimizationId), delay);
      } else {
        setError(err.message || 'Failed to connect to the server');
        window.pollRetries = undefined; // Reset for next time
      }
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Tabs */}
      <div className="flex border-b">
        <button
          className={`py-4 px-6 font-medium ${activeTab === 'strategy' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
          onClick={() => setActiveTab('strategy')}
        >
          1. Strategy Creation
        </button>
        <button
          className={`py-4 px-6 font-medium ${activeTab === 'backtest' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
          onClick={() => setActiveTab('backtest')}
          disabled={!strategy.strategy_id}
        >
          2. Backtest Parameters
        </button>
        <button
          className={`py-4 px-6 font-medium ${activeTab === 'tuning' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
          onClick={() => setActiveTab('tuning')}
          disabled={!backtestResults}
        >
          3. Hyper-Tuning
        </button>
        <button
          className={`py-4 px-6 font-medium ${activeTab === 'results' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
          onClick={() => {
            setActiveTab('results');
            console.log('Results tab activated with state:', {
              strategy,
              backtestResults,
              optimizationId,
              optimizationResults,
              optimizationStatus
            });
          }}
          disabled={!optimizationResults}
        >
          4. Results
        </button>
      </div>
      
      {/* Error message */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 m-4 rounded">
          <strong className="font-bold">Error:</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}
      
      {/* Tab content */}
      <div className="p-6">
        {activeTab === 'strategy' && (
          <StrategyCreation
            strategy={strategy}
            onSave={handleSaveStrategy}
            loading={loading}
          />
        )}
        
        {activeTab === 'backtest' && (
          <BacktestParameters
            backtestParams={backtestParams}
            onSubmit={handleRunBacktest}
            loading={loading}
          />
        )}
        
        {activeTab === 'tuning' && (
          <HyperTuning
            backtestResults={backtestResults}
            optimizationStatus={optimizationStatus}
            onStartOptimization={handleRunOptimization}
            loading={loading}
          />
        )}
        
        {activeTab === 'results' && (
          <Results
            backtestResults={backtestResults}
            optimizationResults={{
              ...optimizationResults,
              optimization_id: optimizationId
            }}
          />
        )}

        {/* Debug output - hidden in production */}
        <div style={{ display: 'none' }}>
          <pre>
            {JSON.stringify({
              activeTab,
              strategyId: strategy.strategy_id,
              backtestId: backtestResults?.backtest_id,
              optimizationId,
              hasOptimizationResults: !!optimizationResults,
              optimizationStatus: optimizationStatus?.status
            }, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default StrategyTuner;
