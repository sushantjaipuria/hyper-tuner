import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const HyperTuning = ({ backtestResults, optimizationStatus, onStartOptimization, loading }) => {
  // Default metrics
  const baseMetrics = backtestResults?.summary || {
    returns: 0,
    win_rate: 0,
    max_drawdown: 0,
    sharpe_ratio: 0,
    trade_count: 0
  };
  
  // Generate placeholder data for the chart if no optimization is running
  const generatePlaceholderData = () => {
    const data = [];
    
    for (let i = 1; i <= 20; i++) {
      data.push({
        iteration: i,
        objective: null,
        best: null
      });
    }
    
    return data;
  };
  
  // Generate chart data from optimization status
  const generateChartData = () => {
    // Use placeholder data if no optimization is running
    if (!optimizationStatus || !optimizationStatus.iteration_results || optimizationStatus.iteration_results.length === 0) {
      return generatePlaceholderData();
    }
    
    const data = [];
    
    // Process each iteration result
    optimizationStatus.iteration_results.forEach((result) => {
      // If the backend returns pre-formatted data, use it directly
      let objectiveValue = 0;
      let bestValue = 0;
      
      // Try to use the most appropriate data structure based on what's available
      if (result.objective_value !== undefined) {
        // Backend might provide negative values (for minimization) - convert to positive
        objectiveValue = typeof result.objective_value === 'number' ? -result.objective_value : 0;
      }
      
      // Get best value - either from pre-calculated field or use current best
      if (result.best_so_far !== undefined) {
        bestValue = result.best_so_far;
      } else {
        // Fallback - find the best value manually
        const previousBest = data.length > 0 ? parseFloat(data[data.length - 1].best) : 0;
        bestValue = Math.max(previousBest, objectiveValue);
      }
      
      // Use iteration number if available, otherwise use array index
      const iterationNumber = result.iteration || data.length + 1;
      
      data.push({
        iteration: iterationNumber,
        objective: objectiveValue.toFixed(2),
        best: bestValue.toFixed(2)
      });
    });
    
    // Fill remaining iterations with null for visualization
    const remainingIterations = 20 - data.length;
    
    for (let i = 1; i <= remainingIterations; i++) {
      data.push({
        iteration: data.length + 1,
        objective: null,
        best: null
      });
    }
    
    return data;
  };
  
  // Generate progress percentage
  const getProgressPercentage = () => {
    if (!optimizationStatus) return 0;
    return optimizationStatus.progress || 0;
  };
  
  // Format the status message
  const getStatusMessage = () => {
    if (!optimizationStatus) return 'Ready to start optimization';
    
    switch (optimizationStatus.status) {
      case 'starting':
        return 'Preparing optimization...';
      case 'running':
        return 'Optimization in progress...';
      case 'running iteration':
        return `Running iteration ${optimizationStatus.iteration_results?.length || 0}/20...`;
      case 'completed':
        return 'Optimization completed successfully!';
      case 'failed':
        return `Optimization failed: ${optimizationStatus.error || 'Unknown error'}`;
      default:
        return 'Unknown status';
    }
  };
  
  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Strategy Hyper-Tuning</h2>
      
      {/* Original Backtest Summary */}
      <div className="mb-6">
        <h3 className="text-lg font-medium mb-2">Original Backtest Results</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="bg-white p-4 rounded shadow">
            <div className="text-gray-500 text-sm">Returns</div>
            <div className="text-xl font-bold text-green-600">{baseMetrics.returns.toFixed(2)}%</div>
          </div>
          
          <div className="bg-white p-4 rounded shadow">
            <div className="text-gray-500 text-sm">Win Rate</div>
            <div className="text-xl font-bold">{(baseMetrics.win_rate * 100).toFixed(2)}%</div>
          </div>
          
          <div className="bg-white p-4 rounded shadow">
            <div className="text-gray-500 text-sm">Max Drawdown</div>
            <div className="text-xl font-bold text-red-600">{baseMetrics.max_drawdown.toFixed(2)}%</div>
          </div>
          
          <div className="bg-white p-4 rounded shadow">
            <div className="text-gray-500 text-sm">Sharpe Ratio</div>
            <div className="text-xl font-bold">{baseMetrics.sharpe_ratio.toFixed(2)}</div>
          </div>
          
          <div className="bg-white p-4 rounded shadow">
            <div className="text-gray-500 text-sm">Trades</div>
            <div className="text-xl font-bold">{baseMetrics.trade_count}</div>
          </div>
        </div>
      </div>
      
      {/* Optimization Progress */}
      <div className="mb-6">
        <h3 className="text-lg font-medium mb-2">Optimization Progress</h3>
        <div className="bg-white p-4 rounded shadow">
          <div className="flex items-center justify-between mb-2">
            <div className="text-gray-700">{getStatusMessage()}</div>
            <div className="text-gray-500 text-sm">
              {optimizationStatus?.iteration_results?.length || 0}/20 iterations
            </div>
          </div>
          
          <div className="w-full bg-gray-200 rounded h-4 mb-4">
            <div
              className="bg-blue-600 h-4 rounded"
              style={{ width: `${getProgressPercentage()}%` }}
            ></div>
          </div>
          
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={generateChartData()}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="iteration" 
                  label={{ value: 'Iteration', position: 'insideBottomRight', offset: -10 }}
                />
                <YAxis 
                  label={{ value: 'Objective Value', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="objective"
                  name="Current Iteration"
                  stroke="#8884d8"
                  activeDot={{ r: 8 }}
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="best"
                  name="Best So Far"
                  stroke="#82ca9d"
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      
      {/* Optimization Parameters */}
      {optimizationStatus?.best_params && (
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-2">Current Best Parameters</h3>
          <div className="bg-white p-4 rounded shadow">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(optimizationStatus.best_params).map(([key, value]) => (
                <div key={key} className="border p-2 rounded">
                  <div className="text-gray-500 text-sm">{key}</div>
                  <div className="font-medium">{typeof value === 'number' ? value.toFixed(2) : value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Start Optimization Button */}
      <div className="flex justify-end">
        <button
          className={`px-6 py-3 rounded font-medium ${
            loading || (optimizationStatus && optimizationStatus.status === 'completed')
              ? 'bg-gray-400 text-white cursor-not-allowed'
              : 'bg-green-600 text-white hover:bg-green-700'
          }`}
          onClick={onStartOptimization}
          disabled={loading || (optimizationStatus && optimizationStatus.status === 'completed')}
        >
          {loading
            ? 'Starting Optimization...'
            : optimizationStatus && optimizationStatus.status === 'completed'
            ? 'Optimization Complete'
            : optimizationStatus && ['running', 'running iteration'].includes(optimizationStatus.status)
            ? 'Optimization Running...'
            : 'Start Optimization'}
        </button>
      </div>
    </div>
  );
};

export default HyperTuning;
