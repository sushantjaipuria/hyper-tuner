import React, { useState } from 'react';

const IndicatorsDownloadButton = ({ backtestId, strategyId, className }) => {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownloadIndicators = async () => {
    // Validate required parameters
    if (!backtestId || !strategyId) {
      console.error('Missing required parameters:', { backtestId, strategyId });
      alert('Cannot download indicators: Missing backtest or strategy information.');
      return;
    }

    setIsDownloading(true);
    try {
      console.log(`Downloading indicators data for strategy ${strategyId}, backtest ${backtestId}`);
      
      // Make API request to download indicators
      const response = await fetch(`/api/backtest-indicators/${backtestId}?strategy_id=${strategyId}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to download indicators data');
      }
      
      // Get the file as a blob
      const blob = await response.blob();
      
      // Create a download link and trigger download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `backtest_indicators_${backtestId}.csv`;
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      console.log('Indicators data downloaded successfully');
    } catch (error) {
      console.error('Error downloading indicators data:', error);
      alert(`Failed to download indicators data: ${error.message}`);
    } finally {
      setIsDownloading(false);
    }
  };

  // Disable the button if required parameters are missing
  const isDisabled = !backtestId || !strategyId || isDownloading;

  return (
    <button
      onClick={handleDownloadIndicators}
      className={`bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded font-medium flex items-center disabled:bg-purple-300 ${className || ''}`}
      disabled={isDisabled}
    >
      {isDownloading ? 'Downloading...' : 'Download Indicators File'}
    </button>
  );
};

export default IndicatorsDownloadButton;
