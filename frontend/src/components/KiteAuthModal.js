import React, { useContext, useState } from 'react';
import { DataSourceContext } from '../context/DataSourceContext';

const KiteAuthModal = ({ isOpen, onClose }) => {
  const { initiateKiteAuth, changeDataProvider } = useContext(DataSourceContext);
  const [isLoading, setIsLoading] = useState(false);
  
  const handleLoginClick = async () => {
    setIsLoading(true);
    await initiateKiteAuth();
    setIsLoading(false);
  };
  
  const handleCancelClick = () => {
    // Switch back to Yahoo Finance
    changeDataProvider('yahoo');
    onClose();
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <h3 className="text-lg font-medium mb-4">Kite Authentication Required</h3>
        <p className="mb-4">
          To use Zerodha Kite as a data source, you need to authenticate with your Kite account.
          Click the button below to start the authentication process.
        </p>
        <div className="flex justify-end space-x-3">
          <button
            className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
            onClick={handleCancelClick}
          >
            Cancel
          </button>
          <button
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
            onClick={handleLoginClick}
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : 'Login to Kite'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default KiteAuthModal;
