import React, { useState } from 'react';

const BacktestReportButton = ({ backtestId, strategyId }) => {
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  const handleGetBacktestReport = async () => {
    setIsGeneratingReport(true);
    try {
      console.log(`Generating backtest report for strategy ${strategyId}, backtest ${backtestId}`);
      
      // Make API request to generate report
      const response = await fetch(`/api/backtest-report/${backtestId}?strategy_id=${strategyId}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to generate backtest report');
      }
      
      // Get the file as a blob
      const blob = await response.blob();
      
      // Create a download link and trigger download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `backtest_report_${backtestId}.md`;
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      console.log('Backtest report downloaded successfully');
    } catch (error) {
      console.error('Error generating backtest report:', error);
      alert(`Failed to generate backtest report: ${error.message}`);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  return (
    <button
      onClick={handleGetBacktestReport}
      className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded font-medium flex items-center disabled:bg-green-300 mt-4"
      disabled={isGeneratingReport}
    >
      {isGeneratingReport ? 'Generating Report...' : 'Get Backtest Report'}
    </button>
  );
};

export default BacktestReportButton;
