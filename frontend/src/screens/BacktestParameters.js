import React, { useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

const BacktestParameters = ({ backtestParams, onSubmit, loading }) => {
  const [initialCapital, setInitialCapital] = useState(
    backtestParams.initial_capital || 100000
  );
  const [startDate, setStartDate] = useState(
    backtestParams.start_date ? new Date(backtestParams.start_date) : null
  );
  const [endDate, setEndDate] = useState(
    backtestParams.end_date ? new Date(backtestParams.end_date) : null
  );
  
  // Validation errors
  const [errors, setErrors] = useState({});
  
  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate form
    const formErrors = {};
    
    if (!initialCapital || initialCapital <= 0) {
      formErrors.initialCapital = 'Initial capital must be a positive number';
    }
    
    if (!startDate) {
      formErrors.startDate = 'Start date is required';
    }
    
    if (!endDate) {
      formErrors.endDate = 'End date is required';
    }
    
    if (startDate && endDate && startDate >= endDate) {
      formErrors.dateRange = 'End date must be after start date';
    }
    
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      return;
    }
    
    // Format dates
    const formattedStartDate = startDate.toISOString().split('T')[0];
    const formattedEndDate = endDate.toISOString().split('T')[0];
    
    // Prepare backtest parameters
    const backtestData = {
      initial_capital: Number(initialCapital),
      start_date: formattedStartDate,
      end_date: formattedEndDate
    };
    
    // Submit backtest parameters
    onSubmit(backtestData);
  };
  
  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Backtest Parameters</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-gray-700 mb-2">Initial Capital</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span className="text-gray-500">₹</span>
              </div>
              <input
                type="number"
                className={`w-full border rounded pl-7 pr-3 py-2 ${
                  errors.initialCapital ? 'border-red-500' : 'border-gray-300'
                }`}
                value={initialCapital}
                onChange={(e) => setInitialCapital(e.target.value)}
                placeholder="e.g., 100000"
              />
            </div>
            {errors.initialCapital && (
              <p className="text-red-500 text-sm mt-1">{errors.initialCapital}</p>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-700 mb-2">Start Date</label>
              <DatePicker
                selected={startDate}
                onChange={(date) => setStartDate(date)}
                className={`w-full border rounded px-3 py-2 ${
                  errors.startDate ? 'border-red-500' : 'border-gray-300'
                }`}
                dateFormat="yyyy-MM-dd"
                placeholderText="Select start date"
                maxDate={new Date()}
              />
              {errors.startDate && (
                <p className="text-red-500 text-sm mt-1">{errors.startDate}</p>
              )}
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2">End Date</label>
              <DatePicker
                selected={endDate}
                onChange={(date) => setEndDate(date)}
                className={`w-full border rounded px-3 py-2 ${
                  errors.endDate ? 'border-red-500' : 'border-gray-300'
                }`}
                dateFormat="yyyy-MM-dd"
                placeholderText="Select end date"
                minDate={startDate}
                maxDate={new Date()}
              />
              {errors.endDate && (
                <p className="text-red-500 text-sm mt-1">{errors.endDate}</p>
              )}
            </div>
          </div>
        </div>
        
        {errors.dateRange && (
          <p className="text-red-500 text-sm mb-4">{errors.dateRange}</p>
        )}
        
        <div className="bg-blue-50 p-4 rounded border border-blue-200 mb-6">
          <h3 className="text-lg font-medium mb-2">Backtest Configuration</h3>
          <p className="text-gray-600 mb-2">
            The backtest will be run with the following configuration:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-gray-700">
            <li>Initial Capital: ₹{initialCapital || '(Not set)'}</li>
            <li>
              Start Date:{' '}
              {startDate ? startDate.toLocaleDateString() : '(Not set)'}
            </li>
            <li>
              End Date: {endDate ? endDate.toLocaleDateString() : '(Not set)'}
            </li>
            <li>
              Duration:{' '}
              {startDate && endDate
                ? Math.ceil(
                    (endDate - startDate) / (1000 * 60 * 60 * 24)
                  ) + ' days'
                : '(Not set)'}
            </li>
          </ul>
        </div>
        
        <div className="flex justify-end">
          <button
            type="submit"
            className="bg-blue-700 text-white px-6 py-3 rounded font-medium flex items-center disabled:bg-blue-300"
            disabled={loading}
          >
            {loading ? 'Running Backtest...' : 'Run Backtest & Continue'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default BacktestParameters;
