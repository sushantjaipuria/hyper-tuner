import axios from 'axios';

// Determine the appropriate API URL based on the environment
const determineApiUrl = () => {
  // Check for manual override in localStorage
  const overrideUrl = localStorage.getItem('api_url_override');
  if (overrideUrl) {
    console.log('Using API URL override from localStorage:', overrideUrl);
    return overrideUrl;
  }
  
  // Check if we're in GitHub Codespaces
  const isCodespaces = window.location.hostname.includes('.github.dev') || 
                       window.location.hostname.includes('.preview.app.github.dev');
  
  if (isCodespaces) {
    // For Codespaces: Use the same domain but with the backend port
    // GitHub Codespaces URLs follow the pattern: something-port.preview.app.github.dev
    // We need to replace the port number in this pattern
    const currentHostname = window.location.hostname;
    
    // Extract port from current hostname or default to 3000
    const portMatch = currentHostname.match(/-([0-9]+)\./); 
    const currentPort = portMatch ? portMatch[1] : '3000';
    
    // Create backend URL by replacing the port (e.g., 3000 → 3001)
    const backendHostname = currentHostname.replace(
      `-${currentPort}.`, 
      `-3001.`
    );
    
    console.log(`Running in Codespaces. Backend hostname: ${backendHostname}`);
    return `${window.location.protocol}//${backendHostname}/api`;
  }
  
  // For local development, use localhost
  return 'http://localhost:3001/api';
};

// Helper function to set a manual override for the API URL
// Can be used from the browser console like: setApiUrlOverride('https://your-backend-url/api')
window.setApiUrlOverride = (url) => {
  if (url) {
    localStorage.setItem('api_url_override', url);
    console.log(`API URL override set to: ${url}. Refresh the page to apply.`);
  } else {
    localStorage.removeItem('api_url_override');
    console.log('API URL override removed. Refresh the page to apply.');
  }
};

// Set the API URL dynamically
const API_URL = determineApiUrl();
console.log('Using API URL:', API_URL);

const api = {
  // Utility method to get the API URL (for logging/debugging)
  getApiUrl: () => API_URL,
  
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