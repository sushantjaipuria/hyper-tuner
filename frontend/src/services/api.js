import axios from 'axios';

const API_URL = 'http://localhost:3001/api'; // Ensure this matches the port in backend's app.py

const api = {
  // Test API connectivity
  testConnection: async () => {
    try {
      const response = await axios.get(`${API_URL}/test`);
      return response.data;
    } catch (error) {
      console.error('API connection test failed:', error);
      return { success: false, error: error.message };
    }
  },
  
  // Test function for debugging API responses
  testStrategyAPI: async (strategyId) => {
    try {
      console.log(`TEST: Making API request to: ${API_URL}/get-strategy/${strategyId}`);
      const response = await axios.get(`${API_URL}/get-strategy/${strategyId}`);
      console.log("TEST: Raw API response:", response);
      console.log("TEST: Response data structure:", response.data);
      return response.data;
    } catch (error) {
      console.error("TEST: API test error:", error);
      return { success: false, error: error.message };
    }
  },
  
  // Strategy endpoints
  saveStrategy: async (strategyData) => {
    const response = await axios.post(`${API_URL}/save-strategy`, strategyData);
    return response.data;
  },
  
  getStrategy: async (strategyId) => {
    try {
      console.log(`Making API request to: ${API_URL}/get-strategy/${strategyId}`);
      const response = await axios.get(`${API_URL}/get-strategy/${strategyId}`);
      console.log("API response structure:", {
        status: response.status,
        responseObject: response,
        responseData: response.data
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching strategy ${strategyId}:`, error);
      if (error.response) {
        console.error('Error response:', error.response.data);
      }
      throw error; // Re-throw to allow the component to handle it
    }
  },
  
  // Backtest endpoints
  runBacktest: async (backtestData) => {
    const response = await axios.post(`${API_URL}/run-backtest`, backtestData);
    return response.data;
  },
  
  // Optimization endpoints
  runOptimization: async (optimizationData) => {
    const response = await axios.post(`${API_URL}/run-optimization`, optimizationData);
    return response.data;
  },
  
  getOptimizationStatus: async (optimizationId) => {
    try {
      console.log(`Requesting optimization status for ID: ${optimizationId}`);
      const response = await axios.get(`${API_URL}/optimization-status/${optimizationId}`);
      console.log(`Optimization status full response:`, response);
      console.log(`Optimization status data:`, response.data);
      return response.data;
    } catch (error) {
      console.error('Error getting optimization status:', error);
      
      // Log more detailed error information
      if (error.response) {
        // The request was made and the server responded with a status code outside 2xx
        console.error('Error response data:', error.response.data);
        console.error('Error response status:', error.response.status);
        console.error('Error response headers:', error.response.headers);
      } else if (error.request) {
        // The request was made but no response was received
        console.error('Error request:', error.request);
      } else {
        // Something happened in setting up the request that triggered an Error
        console.error('Error message:', error.message);
      }
      
      return { success: false, error: error.message };
    }
  },
  
  // Health check
  healthCheck: async () => {
    const response = await axios.get(`${API_URL}/health`);
    return response.data;
  },
  
  // Get data provider info
  getDataProviderInfo: async () => {
    const response = await axios.get(`${API_URL}/health`);
    return {
      provider: response.data.data_provider,
      timestamp: response.data.timestamp
    };
  },
  
  // Get available technical indicators
  getAvailableIndicators: async () => {
    const response = await axios.get(`${API_URL}/get-available-indicators`);
    return response.data;
  },
  
  // Export optimization CSV report
  exportOptimizationCSV: (optimizationId) => {
    // This doesn't use axios because we need to trigger a file download
    // Instead, we create a direct link to the endpoint
    const downloadUrl = `${API_URL}/export-optimization-csv/${optimizationId}`;
    return downloadUrl;
  },
  
  // Save optimized strategy
  saveOptimizedStrategy: async (data) => {
    try {
      console.log('Calling save-optimized-strategy API with data:', data);
      const response = await axios.post(`${API_URL}/save-optimized-strategy`, data);
      console.log('API response for save-optimized-strategy:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error saving optimized strategy:', error);
      
      // Provide more detailed error information
      if (error.response) {
        console.error('Error response:', error.response.data);
        return { 
          success: false, 
          error: error.response.data.error || 'Error from server' 
        };
      }
      
      return { 
        success: false, 
        error: error.message || 'Unknown error saving strategy' 
      };
    }
  }
};

export default api;