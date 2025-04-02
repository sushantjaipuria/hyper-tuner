import React, { createContext, useState, useEffect } from 'react';
import api from '../services/api';

export const DataSourceContext = createContext();

export const DataSourceProvider = ({ children }) => {
  const [dataProvider, setDataProvider] = useState('yahoo');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [requiresAuth, setRequiresAuth] = useState(false);
  const [tokenValid, setTokenValid] = useState(false);
  const [lastTokenCheck, setLastTokenCheck] = useState(null);
  
  // Fetch initial data provider info
  useEffect(() => {
    const fetchDataProviderInfo = async () => {
      try {
        console.log("Fetching initial data provider info...");
        setLoading(true);
        
        const info = await api.getDataProviderInfo();
        console.log("Received data provider info:", info);
        
        setDataProvider(info.provider);
        
        // Check token validity if Kite is selected
        if (info.provider === 'kite') {
          await checkKiteToken();
        }
      } catch (err) {
        console.error("Failed to fetch data provider info:", err);
        setError('Failed to connect to backend');
      } finally {
        setLoading(false);
      }
    };

    fetchDataProviderInfo();
  }, []);
  
  // Change data provider
  const changeDataProvider = async (provider) => {
    try {
      setLoading(true);
      setError(null);
      
      console.log(`Changing data provider to: ${provider}`);
      
      const response = await api.setDataProvider(provider);
      
      if (response.success) {
        setDataProvider(response.provider);
        setRequiresAuth(response.requires_auth);
        
        // If provider is Kite and authentication is required, set state
        if (provider === 'kite') {
          setTokenValid(!response.requires_auth);
        }
      } else {
        setError(response.error || 'Failed to change data provider');
      }
    } catch (err) {
      console.error("Error changing data provider:", err);
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  // Check Kite token validity
  const checkKiteToken = async (force = false) => {
    try {
      // Check if we need to revalidate based on time
      const now = new Date();
      if (!force && lastTokenCheck) {
        const timeSinceLastCheck = now - lastTokenCheck;
        // Don't check more than once per hour unless forced
        if (timeSinceLastCheck < 3600000) { // 1 hour in milliseconds
          console.log("Skipping token check - checked recently");
          return tokenValid;
        }
      }
      
      console.log("Verifying Kite token validity...");
      const response = await api.verifyKiteToken();
      
      if (response.success) {
        console.log("Token verification result:", response.valid);
        setTokenValid(response.valid);
        setRequiresAuth(!response.valid);
        setLastTokenCheck(now);
        return response.valid;
      } else {
        console.error("Token verification failed:", response.error);
        setTokenValid(false);
        setRequiresAuth(true);
        setLastTokenCheck(now);
        return false;
      }
    } catch (err) {
      console.error('Error checking Kite token:', err);
      setTokenValid(false);
      setRequiresAuth(true);
      setLastTokenCheck(new Date());
      return false;
    }
  };
  
  // Check if token needs verification based on trading hours
  const shouldVerifyToken = () => {
    // Get current time in IST (UTC+5:30)
    const now = new Date();
    const istOffset = 330; // IST is UTC+5:30 (330 minutes)
    const istTime = new Date(now.getTime() + (istOffset - now.getTimezoneOffset()) * 60000);
    
    // Check if it's after 3:30:05 PM IST
    const isPastTradingHours = istTime.getHours() > 15 || 
                              (istTime.getHours() === 15 && istTime.getMinutes() >= 30 && istTime.getSeconds() >= 5);
    
    // If past trading hours and we're using Kite, we should verify
    return dataProvider === 'kite' && isPastTradingHours;
  };
  
  // Initiate Kite authentication
  const initiateKiteAuth = async () => {
    try {
      setLoading(true);
      console.log("Initiating Kite authentication...");
      
      const response = await api.getKiteLoginUrl();
      
      if (response.success) {
        console.log("Opening Kite login URL:", response.login_url);
        // Open login URL in a new window
        window.open(response.login_url, '_blank', 'width=800,height=600');
      } else {
        console.error("Failed to get Kite login URL:", response.error);
        setError(response.error || 'Failed to get Kite login URL');
      }
    } catch (err) {
      console.error("Error initiating Kite authentication:", err);
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <DataSourceContext.Provider
      value={{
        dataProvider,
        loading,
        error,
        requiresAuth,
        tokenValid,
        changeDataProvider,
        checkKiteToken,
        initiateKiteAuth,
        shouldVerifyToken
      }}
    >
      {children}
    </DataSourceContext.Provider>
  );
};
