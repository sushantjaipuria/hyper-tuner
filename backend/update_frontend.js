/**
 * This script updates the frontend components to handle the enhanced indicator data
 * 
 * Update the StrategyCreation.js file to leverage enhanced indicator information:
 * - Display better names in the dropdown
 * - Add tooltips for indicator descriptions
 * - Organize indicators by category
 */
const fs = require('fs');
const path = require('path');

// Path to StrategyCreation.js
const strategyCreationPath = path.join(__dirname, '..', 'frontend', 'src', 'screens', 'StrategyCreation.js');

// Read the current content
console.log('Reading StrategyCreation.js...');
let content;
try {
  content = fs.readFileSync(strategyCreationPath, 'utf8');
  console.log('File read successfully');
} catch (e) {
  console.error(`Error reading file: ${e}`);
  process.exit(1);
}

// Update the indicator transformation in fetchIndicators
console.log('Updating indicator transformation...');
const oldTransformCode = `// Transform the response to the format expected by the component
        const indicators = [];
        
        for (const [name, info] of Object.entries(response.indicators)) {
          indicators.push({
            value: name,
            label: info.description,
            params: info.params,
            category: info.category
          });
        }`;

const newTransformCode = `// Transform the response to the format expected by the component
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
        }`;

content = content.replace(oldTransformCode, newTransformCode);

// Add tooltips for indicators in the dropdown
console.log('Adding tooltips to indicator dropdown...');
const oldDropdownCode = `                <select
                  className={\`w-full border rounded px-3 py-2 \${errors.entryIndicator ? 'border-red-500' : 'border-gray-300'}\`}
                  value={entryIndicator}
                  onChange={(e) => {
                    setEntryIndicator(e.target.value);
                    setEntryParams({});
                    setEntryVariable(e.target.value.toLowerCase());
                  }}
                  disabled={isLoadingIndicators}
                >
                  <option value="">Select Indicator</option>
                  {Object.entries(indicatorsByCategory).map(([category, indicators]) => (
                    <optgroup key={category} label={category}>
                      {indicators.map((indicator) => (
                        <option key={indicator.value} value={indicator.value}>{indicator.label}</option>
                      ))}
                    </optgroup>
                  ))}
                </select>`;

const newDropdownCode = `                <select
                  className={\`w-full border rounded px-3 py-2 \${errors.entryIndicator ? 'border-red-500' : 'border-gray-300'}\`}
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
                </select>`;

content = content.replace(oldDropdownCode, newDropdownCode);

// Do the same for exit indicator dropdown
console.log('Updating exit indicator dropdown...');
const oldExitDropdownCode = `                <select
                  className={\`w-full border rounded px-3 py-2 \${errors.exitIndicator ? 'border-red-500' : 'border-gray-300'}\`}
                  value={exitIndicator}
                  onChange={(e) => {
                    setExitIndicator(e.target.value);
                    setExitParams({});
                    setExitVariable(e.target.value.toLowerCase());
                  }}
                  disabled={isLoadingIndicators}
                >
                  <option value="">Select Indicator</option>
                  {Object.entries(indicatorsByCategory).map(([category, indicators]) => (
                    <optgroup key={category} label={category}>
                      {indicators.map((indicator) => (
                        <option key={indicator.value} value={indicator.value}>{indicator.label}</option>
                      ))}
                    </optgroup>
                  ))}
                </select>`;

const newExitDropdownCode = `                <select
                  className={\`w-full border rounded px-3 py-2 \${errors.exitIndicator ? 'border-red-500' : 'border-gray-300'}\`}
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
                </select>`;

content = content.replace(oldExitDropdownCode, newExitDropdownCode);

// Update the hardcoded default indicators
console.log('Updating fallback indicators...');
const oldFallbackCode = `  // Fallback to default indicators if API fails
  const setDefaultIndicators = () => {
    setAvailableIndicators([
      { value: 'SMA', label: 'Simple Moving Average', params: ['timeperiod'], category: 'Overlap Studies' },
      { value: 'EMA', label: 'Exponential Moving Average', params: ['timeperiod'], category: 'Overlap Studies' },
      { value: 'RSI', label: 'Relative Strength Index', params: ['timeperiod'], category: 'Momentum Indicators' },
      { value: 'MACD', label: 'Moving Average Convergence Divergence', params: ['fastperiod', 'slowperiod', 'signalperiod'], category: 'Momentum Indicators' },
      { value: 'BBANDS', label: 'Bollinger Bands', params: ['timeperiod', 'nbdevup', 'nbdevdn'], category: 'Overlap Studies' },
      { value: 'STOCH', label: 'Stochastic', params: ['fastk_period', 'slowk_period', 'slowd_period'], category: 'Momentum Indicators' }
    ]);
  };`;

const newFallbackCode = `  // Fallback to default indicators if API fails
  const setDefaultIndicators = () => {
    setAvailableIndicators([
      { value: 'SMA', label: 'Simple Moving Average (SMA)', description: 'Average price over a specified period', params: ['timeperiod'], category: 'Overlap Studies', code_name: 'SMA' },
      { value: 'EMA', label: 'Exponential Moving Average (EMA)', description: 'Weighted moving average giving more importance to recent prices', params: ['timeperiod'], category: 'Overlap Studies', code_name: 'EMA' },
      { value: 'RSI', label: 'Relative Strength Index (RSI)', description: 'Momentum oscillator measuring speed and change of price movements (0-100)', params: ['timeperiod'], category: 'Momentum Indicators', code_name: 'RSI' },
      { value: 'MACD', label: 'Moving Average Convergence Divergence (MACD)', description: 'Trend-following momentum indicator showing relationship between two moving averages', params: ['fastperiod', 'slowperiod', 'signalperiod'], category: 'Momentum Indicators', code_name: 'MACD' },
      { value: 'BBANDS', label: 'Bollinger Bands (BB)', description: 'Volatility bands placed above and below a moving average', params: ['timeperiod', 'nbdevup', 'nbdevdn'], category: 'Overlap Studies', code_name: 'BBANDS' },
      { value: 'STOCH', label: 'Stochastic Oscillator', description: 'Compares closing price to price range over a period (0-100)', params: ['fastk_period', 'slowk_period', 'slowd_period'], category: 'Momentum Indicators', code_name: 'STOCH' }
    ]);
  };`;

content = content.replace(oldFallbackCode, newFallbackCode);

// Add tooltip/description display near the indicator dropdown
console.log('Adding indicator description display...');

// For entry conditions section
const afterEntryLabel = `              <div>
                <label className="block text-gray-700 mb-1">Indicator</label>`;
const entryDescriptionAddition = `              <div>
                <label className="block text-gray-700 mb-1">Indicator</label>
                {entryIndicator && (
                  <div className="text-xs text-gray-500 mb-1 italic">
                    {availableIndicators.find(ind => ind.value === entryIndicator)?.description || ''}
                  </div>
                )}`;

content = content.replace(afterEntryLabel, entryDescriptionAddition);

// For exit conditions section
const afterExitLabel = `              <div>
                <label className="block text-gray-700 mb-1">Indicator</label>`;
const exitDescriptionAddition = `              <div>
                <label className="block text-gray-700 mb-1">Indicator</label>
                {exitIndicator && (
                  <div className="text-xs text-gray-500 mb-1 italic">
                    {availableIndicators.find(ind => ind.value === exitIndicator)?.description || ''}
                  </div>
                )}`;

// We need to find only the second occurrence (exit section)
let firstOccurrenceIndex = content.indexOf(afterExitLabel);
let secondOccurrenceIndex = content.indexOf(afterExitLabel, firstOccurrenceIndex + 1);
if (secondOccurrenceIndex !== -1) {
  content = content.substring(0, secondOccurrenceIndex) + exitDescriptionAddition + content.substring(secondOccurrenceIndex + afterExitLabel.length);
}

// Write the updated content back to the file
console.log('Writing updated file...');
try {
  fs.writeFileSync(strategyCreationPath, content, 'utf8');
  console.log('StrategyCreation.js updated successfully!');
} catch (e) {
  console.error(`Error writing file: ${e}`);
  process.exit(1);
}
