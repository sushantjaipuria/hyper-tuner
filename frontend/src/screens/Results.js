import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

// Component for side-by-side strategy comparison
const StrategyComparison = ({ originalStrategy, optimizedParams }) => {
  if (!originalStrategy || !optimizedParams) {
    return (
      <div className="bg-white rounded shadow p-4 mb-6">
        <p className="text-gray-500 text-center py-4">Waiting for strategy data...</p>
      </div>
    );
  }
  
  // Helper to get optimized value based on parameter path
  const getOptimizedValue = (paramName) => {
    return optimizedParams[paramName] || null;
  };
  
  // Format values for display
  const formatValue = (value) => {
    if (typeof value === 'number') {
      return value.toFixed(value % 1 === 0 ? 0 : 2);
    }
    return String(value);
  };
  
  // Check if a value has been optimized (changed)
  const isOptimized = (originalValue, optimizedValue) => {
    if (originalValue === null || optimizedValue === null) return false;
    return originalValue !== optimizedValue;
  };
  
  // Render entry conditions
  const renderEntryConditions = () => {
    if (!originalStrategy.entry_conditions || !Array.isArray(originalStrategy.entry_conditions)) {
      return <p>No entry conditions defined</p>;
    }
    
    return originalStrategy.entry_conditions.map((condition, index) => {
      // Skip conditions without indicators/params
      if (!condition.indicator || !condition.params) {
        return null;
      }
      
      const rows = [];
      
      // Add parameters
      Object.entries(condition.params).forEach(([paramName, originalValue]) => {
        const fullParamName = `entry_${index}_${condition.indicator}_${paramName}`;
        const optimizedValue = getOptimizedValue(fullParamName);
        const changed = isOptimized(originalValue, optimizedValue);
        
        rows.push(
          <tr key={fullParamName} className={changed ? "bg-green-50" : ""}>
            <td className="border px-4 py-2">{paramName}</td>
            <td className="border px-4 py-2">{formatValue(originalValue)}</td>
            <td className="border px-4 py-2">
              {optimizedValue !== null ? (
                <span className={changed ? "font-bold text-green-600" : ""}>
                  {formatValue(optimizedValue)}
                  {changed && <span className="ml-1">↑</span>}
                </span>
              ) : formatValue(originalValue)}
            </td>
          </tr>
        );
      });
      
      // Add stop loss/take profit if they exist
      if (condition.stop_loss) {
        const fullParamName = `entry_${index}_stop_loss`;
        const optimizedValue = getOptimizedValue(fullParamName);
        const changed = isOptimized(condition.stop_loss, optimizedValue);
        
        rows.push(
          <tr key={fullParamName} className={changed ? "bg-green-50" : ""}>
            <td className="border px-4 py-2">Stop Loss</td>
            <td className="border px-4 py-2">{formatValue(condition.stop_loss)}</td>
            <td className="border px-4 py-2">
              {optimizedValue !== null ? (
                <span className={changed ? "font-bold text-green-600" : ""}>
                  {formatValue(optimizedValue)}
                  {changed && <span className="ml-1">↑</span>}
                </span>
              ) : formatValue(condition.stop_loss)}
            </td>
          </tr>
        );
      }
      
      if (condition.target_profit) {
        const fullParamName = `entry_${index}_target_profit`;
        const optimizedValue = getOptimizedValue(fullParamName);
        const changed = isOptimized(condition.target_profit, optimizedValue);
        
        rows.push(
          <tr key={fullParamName} className={changed ? "bg-green-50" : ""}>
            <td className="border px-4 py-2">Target Profit</td>
            <td className="border px-4 py-2">{formatValue(condition.target_profit)}</td>
            <td className="border px-4 py-2">
              {optimizedValue !== null ? (
                <span className={changed ? "font-bold text-green-600" : ""}>
                  {formatValue(optimizedValue)}
                  {changed && <span className="ml-1">↑</span>}
                </span>
              ) : formatValue(condition.target_profit)}
            </td>
          </tr>
        );
      }
      
      return (
        <div key={`entry_${index}`} className="mb-6">
          <h4 className="font-medium mb-2">Entry Condition {index + 1}: {condition.indicator}</h4>
          <table className="w-full border-collapse mb-2">
            <thead>
              <tr className="bg-gray-100">
                <th className="border px-4 py-2 text-left">Parameter</th>
                <th className="border px-4 py-2 text-left">Original</th>
                <th className="border px-4 py-2 text-left">Optimized</th>
              </tr>
            </thead>
            <tbody>
              {rows}
            </tbody>
          </table>
          
          {condition.condition && (
            <div className="mt-2 bg-gray-50 p-2 rounded">
              <strong>Condition:</strong> {condition.condition}
            </div>
          )}
        </div>
      );
    });
  };
  
  // Render exit conditions (similar to entry conditions)
  const renderExitConditions = () => {
    if (!originalStrategy.exit_conditions || 
       (!Array.isArray(originalStrategy.exit_conditions) && typeof originalStrategy.exit_conditions !== 'object')) {
      return <p>No exit conditions defined</p>;
    }
    
    // Handle both array and object formats for exit conditions
    const exitConditions = Array.isArray(originalStrategy.exit_conditions) 
      ? originalStrategy.exit_conditions 
      : [originalStrategy.exit_conditions];
    
    return exitConditions.map((condition, index) => {
      // Skip conditions without indicators/params
      if (!condition.indicator && !condition.condition) {
        return null;
      }
      
      const rows = [];
      
      // Add parameters if they exist
      if (condition.params) {
        Object.entries(condition.params).forEach(([paramName, originalValue]) => {
          const fullParamName = `exit_${index}_${condition.indicator}_${paramName}`;
          const optimizedValue = getOptimizedValue(fullParamName);
          const changed = isOptimized(originalValue, optimizedValue);
          
          rows.push(
            <tr key={fullParamName} className={changed ? "bg-green-50" : ""}>
              <td className="border px-4 py-2">{paramName}</td>
              <td className="border px-4 py-2">{formatValue(originalValue)}</td>
              <td className="border px-4 py-2">
                {optimizedValue !== null ? (
                  <span className={changed ? "font-bold text-green-600" : ""}>
                    {formatValue(optimizedValue)}
                    {changed && <span className="ml-1">↑</span>}
                  </span>
                ) : formatValue(originalValue)}
              </td>
            </tr>
          );
        });
      }
      
      // Global stop loss/take profit for the strategy
      if (index === 0) {
        if (originalStrategy.stop_loss !== undefined) {
          const fullParamName = `stop_loss`;
          const optimizedValue = getOptimizedValue(fullParamName);
          const changed = isOptimized(originalStrategy.stop_loss, optimizedValue);
          
          rows.push(
            <tr key={fullParamName} className={changed ? "bg-green-50" : ""}>
              <td className="border px-4 py-2">Global Stop Loss</td>
              <td className="border px-4 py-2">{formatValue(originalStrategy.stop_loss)}</td>
              <td className="border px-4 py-2">
                {optimizedValue !== null ? (
                  <span className={changed ? "font-bold text-green-600" : ""}>
                    {formatValue(optimizedValue)}
                    {changed && <span className="ml-1">↑</span>}
                  </span>
                ) : formatValue(originalStrategy.stop_loss)}
              </td>
            </tr>
          );
        }
        
        if (originalStrategy.target_profit !== undefined) {
          const fullParamName = `target_profit`;
          const optimizedValue = getOptimizedValue(fullParamName);
          const changed = isOptimized(originalStrategy.target_profit, optimizedValue);
          
          rows.push(
            <tr key={fullParamName} className={changed ? "bg-green-50" : ""}>
              <td className="border px-4 py-2">Global Target Profit</td>
              <td className="border px-4 py-2">{formatValue(originalStrategy.target_profit)}</td>
              <td className="border px-4 py-2">
                {optimizedValue !== null ? (
                  <span className={changed ? "font-bold text-green-600" : ""}>
                    {formatValue(optimizedValue)}
                    {changed && <span className="ml-1">↑</span>}
                  </span>
                ) : formatValue(originalStrategy.target_profit)}
              </td>
            </tr>
          );
        }
      }
      
      return (
        <div key={`exit_${index}`} className="mb-6">
          <h4 className="font-medium mb-2">
            Exit Condition {index + 1}: 
            {condition.indicator ? condition.indicator : 'Custom'}
          </h4>
          
          {rows.length > 0 && (
            <table className="w-full border-collapse mb-2">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border px-4 py-2 text-left">Parameter</th>
                  <th className="border px-4 py-2 text-left">Original</th>
                  <th className="border px-4 py-2 text-left">Optimized</th>
                </tr>
              </thead>
              <tbody>
                {rows}
              </tbody>
            </table>
          )}
          
          {condition.condition && (
            <div className="mt-2 bg-gray-50 p-2 rounded">
              <strong>Condition:</strong> {condition.condition}
            </div>
          )}
        </div>
      );
    });
  };
  
  return (
    <div className="bg-white rounded shadow p-4 mb-6">
      <h3 className="text-lg font-medium mb-4">Strategy Comparison: Original vs Optimized</h3>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h3 className="font-semibold text-blue-600 mb-3 pb-2 border-b">Entry Conditions</h3>
          {renderEntryConditions()}
        </div>
        
        <div>
          <h3 className="font-semibold text-blue-600 mb-3 pb-2 border-b">Exit Conditions</h3>
          {renderExitConditions()}
        </div>
      </div>
    </div>
  );
};

const Results = ({ backtestResults, optimizationResults }) => {
  const [originalStrategy, setOriginalStrategyDirect] = useState(null);
  const [loadingStrategy, setLoadingStrategy] = useState(false);
  const [strategyError, setStrategyError] = useState(null);
  
  // Custom setter function with logging
  const setOriginalStrategy = (data) => {
    console.log("Setting strategy state to:", data);
    setOriginalStrategyDirect(data);
  };
  
  // Debug log on component mount
  useEffect(() => {
    console.log('[DEBUG] Results component mounted with initial props:', {
      backtestResults,
      optimizationResults,
      hasStrategyId: !!backtestResults?.strategy_id,
      hasOptimizationId: !!optimizationResults?.optimization_id
    });
  }, []);
  
  // Fetch the original strategy when backtest results change
  useEffect(() => {
    console.log("useEffect triggered with backtestResults:", backtestResults);
    
    const fetchOriginalStrategy = async () => {
      if (backtestResults?.strategy_id) {
        try {
          setLoadingStrategy(true);
          setStrategyError(null);
          console.log('Attempting to fetch strategy with ID:', backtestResults.strategy_id);
          const response = await api.getStrategy(backtestResults.strategy_id);
          console.log('Raw strategy API response:', response);
          
          if (response.success) {
            console.log('Strategy data structure:', response.strategy);
            setOriginalStrategy(response.strategy);
          } else {
            console.error('API returned error:', response.error);
            setStrategyError(response.error || 'Failed to load strategy');
          }
        } catch (error) {
          console.error('Error fetching original strategy:', error);
          setStrategyError(error.message || 'Failed to load strategy');
        } finally {
          setLoadingStrategy(false);
        }
      }
    };
    
    fetchOriginalStrategy();
  }, [backtestResults]);
  // Check if we have results to display
  const hasResults = backtestResults && optimizationResults?.comparison;
  
  // Debug logging to understand data flow
  console.log("Results render data:", {
    backtestResults: backtestResults,
    optimizationResults: optimizationResults,
    originalStrategy: originalStrategy,
    hasStrategyId: !!backtestResults?.strategy_id,
    hasOptimizationId: !!optimizationResults?.optimization_id,
    strategyLoading: loadingStrategy
  });
  
  // Get comparison metrics
  const comparison = optimizationResults?.comparison || {
    original: {
      returns: 0,
      win_rate: 0,
      max_drawdown: 0,
      sharpe_ratio: 0,
      trade_count: 0
    },
    optimized: {
      returns: 0,
      win_rate: 0,
      max_drawdown: 0,
      sharpe_ratio: 0,
      trade_count: 0
    }
  };
  
  // Prepare data for comparison chart
  const prepareComparisonData = () => {
    const { original, optimized } = comparison;
    
    return [
      {
        name: 'Returns (%)',
        original: original.returns,
        optimized: optimized.returns,
        improvement: optimized.returns - original.returns
      },
      {
        name: 'Win Rate (%)',
        original: original.win_rate * 100,
        optimized: optimized.win_rate * 100,
        improvement: (optimized.win_rate - original.win_rate) * 100
      },
      {
        name: 'Max Drawdown (%)',
        original: original.max_drawdown,
        optimized: optimized.max_drawdown,
        // For drawdown, lower is better, so we invert the improvement calculation
        improvement: original.max_drawdown - optimized.max_drawdown
      },
      {
        name: 'Sharpe Ratio',
        original: original.sharpe_ratio,
        optimized: optimized.sharpe_ratio,
        improvement: optimized.sharpe_ratio - original.sharpe_ratio
      }
    ];
  };
  

  
  // Calculate improvement percentage
  const calculateImprovement = (original, optimized) => {
    if (original === 0) return optimized === 0 ? 0 : 100;
    return ((optimized - original) / Math.abs(original)) * 100;
  };
  
  if (!hasResults) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold mb-4">Results</h2>
        <p className="text-gray-500">
          Run a backtest and optimization to see results here.
        </p>
      </div>
    );
  }
  
  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Strategy Optimization Results</h2>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded shadow p-4">
          <div className="text-sm text-gray-500 mb-1">Returns</div>
          <div className="flex items-end">
            <div className="text-2xl font-bold text-green-600">
              {comparison.optimized.returns.toFixed(2)}%
            </div>
            <div className="ml-2 text-sm">
              {comparison.original.returns.toFixed(2)}%
            </div>
            <div className={`ml-2 text-sm ${comparison.optimized.returns > comparison.original.returns ? 'text-green-500' : 'text-red-500'}`}>
              {calculateImprovement(comparison.original.returns, comparison.optimized.returns).toFixed(1)}%
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded shadow p-4">
          <div className="text-sm text-gray-500 mb-1">Win Rate</div>
          <div className="flex items-end">
            <div className="text-2xl font-bold">
              {(comparison.optimized.win_rate * 100).toFixed(2)}%
            </div>
            <div className="ml-2 text-sm">
              {(comparison.original.win_rate * 100).toFixed(2)}%
            </div>
            <div className={`ml-2 text-sm ${comparison.optimized.win_rate > comparison.original.win_rate ? 'text-green-500' : 'text-red-500'}`}>
              {calculateImprovement(comparison.original.win_rate, comparison.optimized.win_rate).toFixed(1)}%
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded shadow p-4">
          <div className="text-sm text-gray-500 mb-1">Max Drawdown</div>
          <div className="flex items-end">
            <div className="text-2xl font-bold text-red-600">
              {comparison.optimized.max_drawdown.toFixed(2)}%
            </div>
            <div className="ml-2 text-sm">
              {comparison.original.max_drawdown.toFixed(2)}%
            </div>
            <div className={`ml-2 text-sm ${comparison.optimized.max_drawdown < comparison.original.max_drawdown ? 'text-green-500' : 'text-red-500'}`}>
              {calculateImprovement(comparison.original.max_drawdown, comparison.optimized.max_drawdown, true).toFixed(1)}%
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded shadow p-4">
          <div className="text-sm text-gray-500 mb-1">Sharpe Ratio</div>
          <div className="flex items-end">
            <div className="text-2xl font-bold">
              {comparison.optimized.sharpe_ratio.toFixed(2)}
            </div>
            <div className="ml-2 text-sm">
              {comparison.original.sharpe_ratio.toFixed(2)}
            </div>
            <div className={`ml-2 text-sm ${comparison.optimized.sharpe_ratio > comparison.original.sharpe_ratio ? 'text-green-500' : 'text-red-500'}`}>
              {calculateImprovement(comparison.original.sharpe_ratio, comparison.optimized.sharpe_ratio).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>
      
      {/* Comparison Chart */}
      <div className="bg-white rounded shadow p-4 mb-6">
        <h3 className="text-lg font-medium mb-4">Performance Comparison</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={prepareComparisonData()}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [
                  `${value.toFixed(2)}${name === 'improvement' ? '% improvement' : ''}`, 
                  name.charAt(0).toUpperCase() + name.slice(1)
                ]}
              />
              <Legend />
              <Bar dataKey="original" name="Original" fill="#8884d8" />
              <Bar dataKey="optimized" name="Optimized" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      {/* Strategy Comparison */}
      {loadingStrategy ? (
        <div className="bg-white rounded shadow p-4 mb-6 text-center">
          <p className="text-gray-500">Loading strategy data...</p>
        </div>
      ) : strategyError ? (
        <div className="bg-white rounded shadow p-4 mb-6 text-center">
          <p className="text-red-500">Error loading strategy: {strategyError}</p>
        </div>
      ) : (
        <StrategyComparison 
          originalStrategy={originalStrategy} 
          optimizedParams={optimizationResults?.status?.best_params || {}} 
        />
      )}
      
      {/* Optimized Parameters */}
      {optimizationResults?.status?.best_params && (
        <div className="bg-white rounded shadow p-4 mb-6">
          <h3 className="text-lg font-medium mb-4">Optimized Parameters</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(optimizationResults.status.best_params).map(([key, value]) => (
              <div key={key} className="border p-3 rounded">
                <div className="text-sm text-gray-500 mb-1">{key}</div>
                <div className="font-medium">
                  {typeof value === 'number' ? value.toFixed(2) : value}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Actions */}
      <div className="flex justify-end space-x-4">
        <button
          className="px-4 py-2 border border-blue-600 text-blue-600 rounded hover:bg-blue-50"
          onClick={() => {
            if (optimizationResults?.optimization_id) {
              // Create a download link and click it to start the download
              const link = document.createElement('a');
              link.href = api.exportOptimizationCSV(optimizationResults.optimization_id);
              link.download = `optimization_report_${optimizationResults.optimization_id}.csv`;
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
            } else {
              alert('No optimization results available to download');
            }
          }}
        >
          Download CSV Report
        </button>
        <button
          id="save-optimized-button"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          onClick={async () => {
            // Debug logging for save button click
            console.log("Save button clicked with:", {
              backtestResultsExists: !!backtestResults,
              strategyId: backtestResults?.strategy_id,
              optimizationId: optimizationResults?.optimization_id,
              originalStrategyExists: !!originalStrategy
            });
            
            if (!backtestResults?.strategy_id) {
              console.error('[DEBUG] Missing strategy ID when saving', { backtestResults });
              alert('Missing strategy ID in backtest results');
              return;
            }
            
            if (!optimizationResults?.optimization_id) {
              console.error('[DEBUG] Missing optimization ID when saving', { optimizationResults });
              alert('Missing optimization ID in optimization results');
              return;
            }
            
            if (!originalStrategy) {
              console.error('[DEBUG] Missing strategy data when saving', { 
                backtestResults,
                optimizationResults,
                originalStrategy 
              });
              alert('Strategy data not loaded yet. Please wait or refresh the page.');
              return;
            }
            
            try {
              // Show loading state
              const saveButton = document.getElementById('save-optimized-button');
              if (saveButton) {
                saveButton.disabled = true;
                saveButton.innerText = 'Saving...';
              }
              
              console.log('Saving optimized strategy with:', {
                strategy_id: backtestResults.strategy_id,
                optimization_id: optimizationResults.optimization_id
              });
              
              const result = await api.saveOptimizedStrategy({
                strategy_id: backtestResults.strategy_id,
                optimization_id: optimizationResults.optimization_id
              });
              
              if (result.success) {
                // Show success message with strategy details
                alert(`Strategy saved successfully!\n\nNew strategy name: ${result.strategy_name}\nStrategy ID: ${result.new_strategy_id}\n\nYou can now find this strategy in your strategy list.`);
              } else {
                // Show error message
                alert(`Error saving strategy: ${result.error}`);
              }
            } catch (error) {
              console.error('Error saving optimized strategy:', error);
              alert('Failed to save optimized strategy: ' + (error.message || 'Unknown error'));
            } finally {
              // Reset button state
              const saveButton = document.getElementById('save-optimized-button');
              if (saveButton) {
                saveButton.disabled = false;
                saveButton.innerText = 'Save Optimized Strategy';
              }
            }
          }}
        >
          Save Optimized Strategy
        </button>
      </div>
    </div>
  );
};

export default Results;
