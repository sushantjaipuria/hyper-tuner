import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { FaPlus, FaTrash } from 'react-icons/fa';

const StrategyCreation = ({ strategy, onSave, loading }) => {
  const [strategyName, setStrategyName] = useState(strategy.name || '');
  const [strategyType, setStrategyType] = useState(strategy.type || 'buy');
  const [symbol, setSymbol] = useState(strategy.symbol || '');
  const [timeframe, setTimeframe] = useState(strategy.timeframe || '');
  
  // Entry conditions
  const [entryConditions, setEntryConditions] = useState(strategy.entry_conditions || []);
  const [entryIndicator, setEntryIndicator] = useState('');
  const [entryComparison, setEntryComparison] = useState('=');
  const [entryParams, setEntryParams] = useState({});
  const [entryVariable, setEntryVariable] = useState('');
  
  // Exit conditions
  const [exitConditions, setExitConditions] = useState(Array.isArray(strategy.exit_conditions) ? strategy.exit_conditions : []);
  const [exitIndicator, setExitIndicator] = useState('');
  const [exitComparison, setExitComparison] = useState('=');
  const [exitParams, setExitParams] = useState({});
  const [exitVariable, setExitVariable] = useState('');
  
  // Stop loss and target profit
  const [stopLoss, setStopLoss] = useState(strategy.stop_loss || '');
  const [targetProfit, setTargetProfit] = useState(strategy.target_profit || '');
  
  // Validation errors
  const [errors, setErrors] = useState({});
  
  // State for dynamic indicators
  const [availableIndicators, setAvailableIndicators] = useState([]);
  const [isLoadingIndicators, setIsLoadingIndicators] = useState(false);
  const [indicatorError, setIndicatorError] = useState('');
  
  // Group indicators by category for better organization
  const indicatorsByCategory = availableIndicators.reduce((acc, indicator) => {
    const category = indicator.category || 'Other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(indicator);
    return acc;
  }, {});
  
  // Fetch indicators on component mount
  useEffect(() => {
    fetchIndicators();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  
  // Function to fetch indicators
  const fetchIndicators = async () => {
    try {
      setIsLoadingIndicators(true);
      setIndicatorError('');
      
      // Environment diagnostic information
      console.log('Current environment information:');
      console.log('- Hostname:', window.location.hostname);
      console.log('- Protocol:', window.location.protocol);
      console.log('- Port:', window.location.port || '(default)');
      
      // First test API connectivity
      console.log('Testing API connectivity...');
      const testResult = await api.testConnection();
      console.log('API test result:', testResult);
      
      if (!testResult.success) {
        throw new Error(`Cannot connect to backend API: ${testResult.error || 'Unknown error'}`);
      }
      
      console.log('Fetching indicators from API...');
      console.log('API endpoint:', api.getApiUrl() + '/get-available-indicators');
      const response = await api.getAvailableIndicators();
      console.log('Indicators response:', response);
      
      if (response.success) {
        // Transform the response to the format expected by the component
        const indicators = [];
        
        for (const [name, info] of Object.entries(response.indicators)) {
          indicators.push({
            value: name,
            label: info.display_name || name,
            description: info.description || '',
            params: info.params,
            category: info.category,
            code_name: info.code_name || name
          });
        }
        
        // Sort indicators by category and name
        indicators.sort((a, b) => {
          if (a.category === b.category) {
            return a.label.localeCompare(b.label);
          }
          return a.category.localeCompare(b.category);
        });
        
        setAvailableIndicators(indicators);
      } else {
        setIndicatorError('Failed to load indicators');
        // Fallback to hardcoded list
        setDefaultIndicators();
      }
    } catch (error) {
      console.error('Error fetching indicators:', error);
      setIndicatorError(`Error loading indicators: ${error.message || 'Unknown error'}. Using default set.`);
      // Fallback to hardcoded list
      setDefaultIndicators();
    } finally {
      setIsLoadingIndicators(false);
    }
  };
  
  // Fallback to default indicators if API fails
  const setDefaultIndicators = () => {
    setAvailableIndicators([
      { value: 'SMA', label: 'Simple Moving Average (SMA)', description: 'Average price over a specified period', params: ['timeperiod'], category: 'Overlap Studies', code_name: 'SMA' },
      { value: 'EMA', label: 'Exponential Moving Average (EMA)', description: 'Weighted moving average giving more importance to recent prices', params: ['timeperiod'], category: 'Overlap Studies', code_name: 'EMA' },
      { value: 'RSI', label: 'Relative Strength Index (RSI)', description: 'Momentum oscillator measuring speed and change of price movements (0-100)', params: ['timeperiod'], category: 'Momentum Indicators', code_name: 'RSI' },
      { value: 'MACD', label: 'Moving Average Convergence Divergence (MACD)', description: 'Trend-following momentum indicator showing relationship between two moving averages', params: ['fastperiod', 'slowperiod', 'signalperiod'], category: 'Momentum Indicators', code_name: 'MACD' },
      { value: 'BBANDS', label: 'Bollinger Bands (BB)', description: 'Volatility bands placed above and below a moving average', params: ['timeperiod', 'nbdevup', 'nbdevdn'], category: 'Overlap Studies', code_name: 'BBANDS' },
      { value: 'STOCH', label: 'Stochastic Oscillator', description: 'Compares closing price to price range over a period (0-100)', params: ['fastk_period', 'slowk_period', 'slowd_period'], category: 'Momentum Indicators', code_name: 'STOCH' }
    ]);
  };
  
  // Available timeframes
  const availableTimeframes = [
    { value: '1minute', label: '1 Minute' },
    { value: '5minute', label: '5 Minutes' },
    { value: '15minute', label: '15 Minutes' },
    { value: '30minute', label: '30 Minutes' },
    { value: '60minute', label: '1 Hour' },
    { value: 'day', label: 'Daily' },
    { value: 'week', label: 'Weekly' }
  ];
  
  // Handle adding entry indicator
  const handleAddEntryIndicator = () => {
    if (!entryIndicator) {
      setErrors({ ...errors, entryIndicator: 'Please select an indicator' });
      return;
    }
    
    // Find selected indicator
    const selectedIndicator = availableIndicators.find(ind => ind.value === entryIndicator);
    
    // Prepare params
    const params = {};
    let hasParamErrors = false;
    
    selectedIndicator.params.forEach(param => {
      // For value/price parameter, it's a string from dropdown
      if (param.toLowerCase() === 'value' || param.toLowerCase() === 'price' || param.toLowerCase() === 'real') {
        const value = entryParams[param] || 'close'; // Default to close
        params[param] = value;
      } else {
        // For numeric parameters
        const value = entryParams[param];
        if (!value || isNaN(value)) {
          setErrors({ ...errors, [param]: `Please enter a valid value for ${param}` });
          hasParamErrors = true;
        } else {
          params[param] = Number(value);
        }
      }
    });
    
    if (hasParamErrors) return;
    
    // Check if we need a threshold value (for all comparison operators)
    if ((!entryParams.threshold && entryParams.threshold !== 0)) {
      setErrors({ ...errors, threshold: 'Please enter a threshold value for comparison' });
      return;
    }
    
    // Add indicator to entry conditions
    const newCondition = {
      indicator: entryIndicator,
      comparison: entryComparison,
      params,
      variable: entryVariable || entryIndicator.toLowerCase()
    };
    
    // Add threshold for all comparison operators
    if (entryParams.threshold || entryParams.threshold === 0) {
      newCondition.threshold = parseFloat(entryParams.threshold);
    }
    
    setEntryConditions([...entryConditions, newCondition]);
    
    // Reset form
    setEntryIndicator('');
    setEntryParams({});
    setEntryVariable('');
    setEntryComparison('=');
    setErrors({});
  };
  
  // Handle adding exit indicator
  const handleAddExitIndicator = () => {
    if (!exitIndicator) {
      setErrors({ ...errors, exitIndicator: 'Please select an indicator' });
      return;
    }
    
    // Find selected indicator
    const selectedIndicator = availableIndicators.find(ind => ind.value === exitIndicator);
    
    // Prepare params
    const params = {};
    let hasParamErrors = false;
    
    selectedIndicator.params.forEach(param => {
      // For value/price parameter, it's a string from dropdown
      if (param.toLowerCase() === 'value' || param.toLowerCase() === 'price' || param.toLowerCase() === 'real') {
        const value = exitParams[param] || 'close'; // Default to close
        params[param] = value;
      } else {
        // For numeric parameters
        const value = exitParams[param];
        if (!value || isNaN(value)) {
          setErrors({ ...errors, [param]: `Please enter a valid value for ${param}` });
          hasParamErrors = true;
        } else {
          params[param] = Number(value);
        }
      }
    });
    
    if (hasParamErrors) return;
    
    // Check if we need a threshold value (for all comparison operators)
    if ((!exitParams.threshold && exitParams.threshold !== 0)) {
      setErrors({ ...errors, threshold: 'Please enter a threshold value for comparison' });
      return;
    }
    
    // Add indicator to exit conditions
    const newCondition = {
      indicator: exitIndicator,
      comparison: exitComparison,
      params,
      variable: exitVariable || exitIndicator.toLowerCase()
    };
    
    // Add threshold for all comparison operators
    if (exitParams.threshold || exitParams.threshold === 0) {
      newCondition.threshold = parseFloat(exitParams.threshold);
    }
    
    setExitConditions([...exitConditions, newCondition]);
    
    // Reset form
    setExitIndicator('');
    setExitParams({});
    setExitVariable('');
    setExitComparison('=');
    setErrors({});
  };
  
  // Handle removing entry condition
  const handleRemoveEntryCondition = (index) => {
    const newConditions = [...entryConditions];
    newConditions.splice(index, 1);
    setEntryConditions(newConditions);
  };
  
  // Handle removing exit condition
  const handleRemoveExitCondition = (index) => {
    const newConditions = [...exitConditions];
    newConditions.splice(index, 1);
    setExitConditions(newConditions);
  };
  
  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate form
    const formErrors = {};
    
    if (!strategyName) formErrors.strategyName = 'Strategy name is required';
    if (!symbol) formErrors.symbol = 'Symbol is required';
    if (!timeframe) formErrors.timeframe = 'Timeframe is required';
    if (entryConditions.length === 0) formErrors.entryConditions = 'At least one entry condition is required';
    
    // Validate stop loss and target profit
    if (!stopLoss || isNaN(stopLoss) || parseFloat(stopLoss) <= 0) 
      formErrors.stopLoss = 'Valid stop loss percentage is required';
    if (!targetProfit || isNaN(targetProfit) || parseFloat(targetProfit) <= 0) 
      formErrors.targetProfit = 'Valid target profit percentage is required';
    
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      return;
    }
    
    // Prepare strategy data
    const strategyData = {
      name: strategyName,
      type: strategyType,
      symbol,
      timeframe,
      entry_conditions: entryConditions,
      exit_conditions: exitConditions,
      stop_loss: parseFloat(stopLoss),
      target_profit: parseFloat(targetProfit)
    };
    
    // Save strategy
    onSave(strategyData);
  };
  
  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Strategy Creation</h2>
      
      <form onSubmit={handleSubmit}>
        {/* Basic Strategy Information */}
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-2">Basic Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-700 mb-1">Strategy Name</label>
              <input
                type="text"
                className={`w-full border rounded px-3 py-2 ${errors.strategyName ? 'border-red-500' : 'border-gray-300'}`}
                value={strategyName}
                onChange={(e) => setStrategyName(e.target.value)}
                placeholder="e.g., EMA Crossover Strategy"
              />
              {errors.strategyName && <p className="text-red-500 text-sm mt-1">{errors.strategyName}</p>}
            </div>
            
            <div>
              <label className="block text-gray-700 mb-1">Strategy Type</label>
              <select
                className="w-full border border-gray-300 rounded px-3 py-2"
                value={strategyType}
                onChange={(e) => setStrategyType(e.target.value)}
              >
                <option value="buy">Buy (Long)</option>
                <option value="sell">Sell (Short)</option>
              </select>
            </div>
            
            <div>
              <label className="block text-gray-700 mb-1">Symbol</label>
              <input
                type="text"
                className={`w-full border rounded px-3 py-2 ${errors.symbol ? 'border-red-500' : 'border-gray-300'}`}
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="e.g., NIFTY, RELIANCE"
              />
              {errors.symbol && <p className="text-red-500 text-sm mt-1">{errors.symbol}</p>}
            </div>
            
            <div>
              <label className="block text-gray-700 mb-1">Timeframe</label>
              <select
                className={`w-full border rounded px-3 py-2 ${errors.timeframe ? 'border-red-500' : 'border-gray-300'}`}
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
              >
                <option value="">Select Timeframe</option>
                {availableTimeframes.map((tf) => (
                  <option key={tf.value} value={tf.value}>{tf.label}</option>
                ))}
              </select>
              {errors.timeframe && <p className="text-red-500 text-sm mt-1">{errors.timeframe}</p>}
            </div>
          </div>
        </div>
        
        {/* Entry Conditions */}
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-2">Entry Conditions</h3>
          
          {/* Added entry conditions */}
          {entryConditions.length > 0 ? (
            <div className="mb-4">
              <h4 className="text-md font-medium mb-2">Added Indicators:</h4>
              <ul className="space-y-2">
                {entryConditions.map((condition, index) => (
                  <li key={index} className="flex items-center justify-between bg-blue-50 p-3 rounded border border-blue-200">
                    <div>
                      <span className="font-medium">{condition.indicator}</span>
                      <span className="text-gray-600 ml-2">{condition.variable}</span>
                      <span className="text-gray-600 ml-2">{condition.comparison || '='}</span>
                      <span className="text-blue-600 ml-2">{condition.threshold !== undefined ? condition.threshold : ''}</span>
                      <span className="text-gray-500 ml-2">
                        (
                        {Object.entries(condition.params).map(([key, value], i, arr) => (
                          <span key={key}>
                            {key}: {value}{i < arr.length - 1 ? ', ' : ''}
                          </span>
                        ))}
                        )
                      </span>
                    </div>
                    <button
                      type="button"
                      className="text-red-500 hover:text-red-700"
                      onClick={() => handleRemoveEntryCondition(index)}
                    >
                      <FaTrash />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-gray-500 italic mb-4">No entry conditions added yet.</p>
          )}
          
          {errors.entryConditions && (
            <p className="text-red-500 text-sm mb-4">{errors.entryConditions}</p>
          )}
          
          {/* Add new entry condition */}
          <div className="bg-gray-50 p-4 rounded border border-gray-200">
            <h4 className="text-md font-medium mb-2">Add New Indicator:</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
              <div>
                <label className="block text-gray-700 mb-1">Indicator</label>
                <select
                  className={`w-full border rounded px-3 py-2 ${errors.entryIndicator ? 'border-red-500' : 'border-gray-300'}`}
                  value={entryIndicator}
                  onChange={(e) => {
                    setEntryIndicator(e.target.value);
                    setEntryParams({});
                    // Use code_name or value for variable name suggestion
                    const selectedInd = availableIndicators.find(ind => ind.value === e.target.value);
                    const suggestedVarName = selectedInd ? 
                      (selectedInd.code_name || e.target.value).toLowerCase() : 
                      e.target.value.toLowerCase();
                    setEntryVariable(suggestedVarName);
                    setEntryComparison('='); // Reset comparison operator when indicator changes
                  }}
                  disabled={isLoadingIndicators}
                >
                  <option value="">Select Indicator</option>
                  {Object.entries(indicatorsByCategory).map(([category, indicators]) => (
                    <optgroup key={category} label={category}>
                      {indicators.map((indicator) => (
                        <option 
                          key={indicator.value} 
                          value={indicator.value}
                          title={indicator.description || indicator.label}
                        >
                          {indicator.label}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
                {isLoadingIndicators && <p className="text-blue-500 text-sm mt-1">Loading indicators...</p>}
                {indicatorError && <p className="text-orange-500 text-sm mt-1">{indicatorError}</p>}
                {errors.entryIndicator && <p className="text-red-500 text-sm mt-1">{errors.entryIndicator}</p>}
              </div>

              <div>
                <label className="block text-gray-700 mb-1">Comparison</label>
                <select
                  className="w-full border border-gray-300 rounded px-3 py-2"
                  value={entryComparison}
                  onChange={(e) => setEntryComparison(e.target.value)}
                  disabled={!entryIndicator}
                >
                  <option value="=">=</option>
                  <option value=">">&gt;</option>
                  <option value="<">&lt;</option>
                  <option value=">=">&gt;=</option>
                  <option value="<=">&lt;=</option>
                </select>
              </div>
              
              <div>
                <label className="block text-gray-700 mb-1">Variable Name</label>
                <input
                  type="text"
                  className="w-full border border-gray-300 rounded px-3 py-2"
                  value={entryVariable}
                  onChange={(e) => setEntryVariable(e.target.value)}
                  placeholder="e.g., ema_short"
                />
              </div>
            </div>
            
            {/* Indicator parameters */}
            {entryIndicator && (
              <div className="mb-3">
                <h5 className="text-sm font-medium mb-2">Parameters:</h5>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {availableIndicators.find(ind => ind.value === entryIndicator)?.params.map((param) => {
                    // Special handling for 'value' parameter
                    if (param.toLowerCase() === 'value' || param.toLowerCase() === 'price' || param.toLowerCase() === 'real') {
                      return (
                        <div key={param}>
                          <label className="block text-gray-700 text-sm mb-1">Price Series</label>
                          <select
                            className={`w-full border rounded px-3 py-2 ${errors[param] ? 'border-red-500' : 'border-gray-300'}`}
                            value={entryParams[param] || 'close'}
                            onChange={(e) => setEntryParams({ ...entryParams, [param]: e.target.value })}
                          >
                            <option value="close">Close</option>
                            <option value="open">Open</option>
                            <option value="high">High</option>
                            <option value="low">Low</option>
                            <option value="volume">Volume</option>
                          </select>
                          {errors[param] && <p className="text-red-500 text-xs mt-1">{errors[param]}</p>}
                        </div>
                      );
                    }
                    
                    // Regular numeric parameters
                    return (
                      <div key={param}>
                        <label className="block text-gray-700 text-sm mb-1">{param}</label>
                        <input
                          type="number"
                          className={`w-full border rounded px-3 py-2 ${errors[param] ? 'border-red-500' : 'border-gray-300'}`}
                          value={entryParams[param] || ''}
                          onChange={(e) => setEntryParams({ ...entryParams, [param]: e.target.value })}
                          placeholder={`Enter ${param}`}
                        />
                        {errors[param] && <p className="text-red-500 text-xs mt-1">{errors[param]}</p>}
                      </div>
                    );
                  })}
                  
                  {/* Add threshold value field */}
                  <div>
                    <label className="block text-gray-700 text-sm mb-1">Threshold</label>
                    <input
                      type="number"
                      step="any"
                      className={`w-full border rounded px-3 py-2 ${errors.threshold ? 'border-red-500' : 'border-gray-300'}`}
                      value={entryParams.threshold || ''}
                      onChange={(e) => setEntryParams({ ...entryParams, threshold: parseFloat(e.target.value) })}
                      placeholder="Enter comparison value"
                    />
                    <p className="text-gray-500 text-xs mt-1">Value to compare the indicator against</p>
                    {errors.threshold && <p className="text-red-500 text-xs mt-1">{errors.threshold}</p>}
                  </div>
                </div>
              </div>
            )}
            
            <div className="flex justify-end">
              <button
                type="button"
                className="bg-blue-600 text-white px-4 py-2 rounded flex items-center"
                onClick={handleAddEntryIndicator}
              >
                <FaPlus className="mr-1" /> Add Indicator
              </button>
            </div>
          </div>
        </div>
        
        {/* Exit Conditions */}
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-2">Exit Conditions</h3>
          
          {/* Mandatory Stop Loss and Target Profit */}
          <div className="mb-4">
            <h4 className="text-md font-medium mb-2">Mandatory Exit Parameters:</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-gray-700 mb-1">Stop Loss (%)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  className={`w-full border rounded px-3 py-2 ${errors.stopLoss ? 'border-red-500' : 'border-gray-300'}`}
                  value={stopLoss}
                  onChange={(e) => setStopLoss(e.target.value)}
                  placeholder="e.g., 5 for 5%"
                />
                {errors.stopLoss && <p className="text-red-500 text-sm mt-1">{errors.stopLoss}</p>}
              </div>
              <div>
                <label className="block text-gray-700 mb-1">Target Profit (%)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  className={`w-full border rounded px-3 py-2 ${errors.targetProfit ? 'border-red-500' : 'border-gray-300'}`}
                  value={targetProfit}
                  onChange={(e) => setTargetProfit(e.target.value)}
                  placeholder="e.g., 10 for 10%"
                />
                {errors.targetProfit && <p className="text-red-500 text-sm mt-1">{errors.targetProfit}</p>}
              </div>
            </div>
          </div>
          
          {/* Optional Indicator-Based Exit Conditions */}
          <h4 className="text-md font-medium mb-2">Optional Indicator-Based Exit Conditions:</h4>
          
          {/* Added exit conditions */}
          {exitConditions.length > 0 ? (
            <div className="mb-4">
              <h4 className="text-md font-medium mb-2">Added Indicators:</h4>
              <ul className="space-y-2">
                {exitConditions.map((condition, index) => (
                  <li key={index} className="flex items-center justify-between bg-green-50 p-3 rounded border border-green-200">
                    <div>
                      <span className="font-medium">{condition.indicator}</span>
                      <span className="text-gray-600 ml-2">{condition.variable}</span>
                      <span className="text-gray-600 ml-2">{condition.comparison || '='}</span>
                      <span className="text-green-600 ml-2">{condition.threshold !== undefined ? condition.threshold : ''}</span>
                      <span className="text-gray-500 ml-2">
                        (
                        {Object.entries(condition.params).map(([key, value], i, arr) => (
                          <span key={key}>
                            {key}: {value}{i < arr.length - 1 ? ', ' : ''}
                          </span>
                        ))}
                        )
                      </span>
                    </div>
                    <button
                      type="button"
                      className="text-red-500 hover:text-red-700"
                      onClick={() => handleRemoveExitCondition(index)}
                    >
                      <FaTrash />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-gray-500 italic mb-4">No exit conditions added yet.</p>
          )}
          
          {errors.exitConditions && (
            <p className="text-red-500 text-sm mb-4">{errors.exitConditions}</p>
          )}
          
          {/* Add new exit condition */}
          <div className="bg-gray-50 p-4 rounded border border-gray-200">
            <h4 className="text-md font-medium mb-2">Add New Indicator:</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
              <div>
                <label className="block text-gray-700 mb-1">Indicator</label>
                <select
                  className={`w-full border rounded px-3 py-2 ${errors.exitIndicator ? 'border-red-500' : 'border-gray-300'}`}
                  value={exitIndicator}
                  onChange={(e) => {
                    setExitIndicator(e.target.value);
                    setExitParams({});
                    // Use code_name or value for variable name suggestion
                    const selectedInd = availableIndicators.find(ind => ind.value === e.target.value);
                    const suggestedVarName = selectedInd ? 
                      (selectedInd.code_name || e.target.value).toLowerCase() : 
                      e.target.value.toLowerCase();
                    setExitVariable(suggestedVarName);
                    setExitComparison('='); // Reset comparison operator when indicator changes
                  }}
                  disabled={isLoadingIndicators}
                >
                  <option value="">Select Indicator</option>
                  {Object.entries(indicatorsByCategory).map(([category, indicators]) => (
                    <optgroup key={category} label={category}>
                      {indicators.map((indicator) => (
                        <option 
                          key={indicator.value} 
                          value={indicator.value}
                          title={indicator.description || indicator.label}
                        >
                          {indicator.label}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
                {isLoadingIndicators && <p className="text-blue-500 text-sm mt-1">Loading indicators...</p>}
                {indicatorError && <p className="text-orange-500 text-sm mt-1">{indicatorError}</p>}
                {errors.exitIndicator && <p className="text-red-500 text-sm mt-1">{errors.exitIndicator}</p>}
              </div>
              
              <div>
                <label className="block text-gray-700 mb-1">Comparison</label>
                <select
                  className="w-full border border-gray-300 rounded px-3 py-2"
                  value={exitComparison}
                  onChange={(e) => setExitComparison(e.target.value)}
                  disabled={!exitIndicator}
                >
                  <option value="=">=</option>
                  <option value=">">&gt;</option>
                  <option value="<">&lt;</option>
                  <option value=">=">&gt;=</option>
                  <option value="<=">&lt;=</option>
                </select>
              </div>
              
              <div>
                <label className="block text-gray-700 mb-1">Variable Name</label>
                <input
                  type="text"
                  className="w-full border border-gray-300 rounded px-3 py-2"
                  value={exitVariable}
                  onChange={(e) => setExitVariable(e.target.value)}
                  placeholder="e.g., rsi_overbought"
                />
              </div>
            </div>
            
            {/* Indicator parameters */}
            {exitIndicator && (
              <div className="mb-3">
                <h5 className="text-sm font-medium mb-2">Parameters:</h5>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {availableIndicators.find(ind => ind.value === exitIndicator)?.params.map((param) => {
                    // Special handling for 'value' parameter
                    if (param.toLowerCase() === 'value' || param.toLowerCase() === 'price' || param.toLowerCase() === 'real') {
                      return (
                        <div key={param}>
                          <label className="block text-gray-700 text-sm mb-1">Price Series</label>
                          <select
                            className={`w-full border rounded px-3 py-2 ${errors[param] ? 'border-red-500' : 'border-gray-300'}`}
                            value={exitParams[param] || 'close'}
                            onChange={(e) => setExitParams({ ...exitParams, [param]: e.target.value })}
                          >
                            <option value="close">Close</option>
                            <option value="open">Open</option>
                            <option value="high">High</option>
                            <option value="low">Low</option>
                            <option value="volume">Volume</option>
                          </select>
                          {errors[param] && <p className="text-red-500 text-xs mt-1">{errors[param]}</p>}
                        </div>
                      );
                    }
                    
                    // Regular numeric parameters
                    return (
                      <div key={param}>
                        <label className="block text-gray-700 text-sm mb-1">{param}</label>
                        <input
                          type="number"
                          className={`w-full border rounded px-3 py-2 ${errors[param] ? 'border-red-500' : 'border-gray-300'}`}
                          value={exitParams[param] || ''}
                          onChange={(e) => setExitParams({ ...exitParams, [param]: e.target.value })}
                          placeholder={`Enter ${param}`}
                        />
                        {errors[param] && <p className="text-red-500 text-xs mt-1">{errors[param]}</p>}
                      </div>
                    );
                  })}
                  
                  {/* Add threshold value field */}
                  <div>
                    <label className="block text-gray-700 text-sm mb-1">Threshold</label>
                    <input
                      type="number"
                      step="any"
                      className={`w-full border rounded px-3 py-2 ${errors.threshold ? 'border-red-500' : 'border-gray-300'}`}
                      value={exitParams.threshold || ''}
                      onChange={(e) => setExitParams({ ...exitParams, threshold: parseFloat(e.target.value) })}
                      placeholder="Enter comparison value"
                    />
                    <p className="text-gray-500 text-xs mt-1">Value to compare the indicator against</p>
                    {errors.threshold && <p className="text-red-500 text-xs mt-1">{errors.threshold}</p>}
                  </div>
                </div>
              </div>
            )}
            
            <div className="flex justify-end">
              <button
                type="button"
                className="bg-green-600 text-white px-4 py-2 rounded flex items-center"
                onClick={handleAddExitIndicator}
              >
                <FaPlus className="mr-1" /> Add Indicator
              </button>
            </div>
          </div>
        </div>
        
        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            className="bg-blue-700 text-white px-6 py-3 rounded font-medium flex items-center disabled:bg-blue-300"
            disabled={loading}
          >
            {loading ? 'Saving...' : 'Save Strategy & Continue'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default StrategyCreation;
