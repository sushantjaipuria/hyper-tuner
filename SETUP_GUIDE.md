# Trading Strategy Hyper-Tuner - Setup Guide

This guide provides step-by-step instructions to set up and run the Trading Strategy Hyper-Tuner application.

## Step 1: Clone the Repository

First, make sure you have the project code:

```bash
# The project is already in your directory at:
/Users/sushant/Documents/Python/Spyder/candlesticks/hypertuner/
```

## Step 2: Install Dependencies

### Backend Dependencies

1. First, you need to install TA-Lib which is a dependency for technical indicators:

   **macOS**:
   ```bash
   brew install ta-lib
   ```

   **Windows**:
   Download the appropriate wheel file from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib) and install it with pip:
   ```bash
   pip install TA_Lib-0.4.24-cp38-cp38-win_amd64.whl
   ```
   (Make sure to download the correct wheel for your Python version and system architecture)

   **Linux**:
   ```bash
   wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
   tar -xzf ta-lib-0.4.0-src.tar.gz
   cd ta-lib/
   ./configure --prefix=/usr
   make
   sudo make install
   ```

2. Set up a Python virtual environment for the backend:

   ```bash
   # Navigate to the backend directory
   cd /Users/sushant/Documents/Python/Spyder/candlesticks/hypertuner/backend
   
   # Create virtual environment
   python3 -m venv venv
   
   # Activate the virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   # venv\Scripts\activate
   
   # Install Python dependencies
   pip install -r requirements.txt
   ```

### Frontend Dependencies

1. Install Node.js dependencies for the frontend:

   ```bash
   # Navigate to the frontend directory
   cd /Users/sushant/Documents/Python/Spyder/candlesticks/hypertuner/frontend
   
   # Install dependencies
   npm install
   ```

## Step 3: Configure the Application

1. Configure Market Data Provider:

   The application supports two data providers: Zerodha Kite API and Yahoo Finance (as a fallback).
   
   **Option 1: Use Zerodha Kite API (Recommended for Indian Markets)**
   
   Open `/Users/sushant/Documents/Python/Spyder/candlesticks/hypertuner/backend/kite_integration.py` and update the following lines with your Zerodha Kite API credentials:

   ```python
   self.api_key = "your_api_key"
   self.api_secret = "your_api_secret"
   ```
   
   **Option 2: Use Yahoo Finance (No configuration needed)**
   
   If you leave the Zerodha credentials as placeholders, the application will automatically use Yahoo Finance as the data source. This is useful for testing without a Zerodha account.
   
   ```python
   # Keep these as is to use Yahoo Finance
   self.api_key = "your_api_key"
   self.api_secret = "your_api_secret"
   ```

2. (Optional) Configure backend port:

   By default, the backend server will run on port 5000. If you need to change this, open `/Users/sushant/Documents/Python/Spyder/candlesticks/hypertuner/backend/app.py` and modify the following line:

   ```python
   app.run(debug=True, port=5000)
   ```

3. (Optional) Configure frontend to connect to backend:

   If you changed the backend port, you'll need to update the frontend API service. Open `/Users/sushant/Documents/Python/Spyder/candlesticks/hypertuner/frontend/src/services/api.js` and modify the API_URL:

   ```javascript
   const API_URL = 'http://localhost:5000/api';
   ```

## Step 4: Run the Application

To run the application, you need to start both the backend and frontend servers.

### Start the Backend Server

```bash
# Navigate to the backend directory (if not already there)
cd /Users/sushant/Documents/Python/Spyder/candlesticks/hypertuner/backend

# Make sure your virtual environment is activated
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Start the Flask server
python app.py
```

You should see output indicating that the server is running:
```
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

### Start the Frontend Server

Open a new terminal window and run:

```bash
# Navigate to the frontend directory
cd /Users/sushant/Documents/Python/Spyder/candlesticks/hypertuner/frontend

# Start the React development server
npm start
```

This will start the frontend development server and automatically open your browser to `http://localhost:3000`.

## Step 5: Access the Application

Once both servers are running, you can access the Trading Strategy Hyper-Tuner application at:

```
http://localhost:3000
```

## Troubleshooting

### Backend Issues

- **Dependencies not found**: Make sure you've installed all dependencies correctly, including TA-Lib.
- **Port already in use**: If port 5000 is already in use, change the port number in `app.py`.
- **Data Provider Issues**:
  - **Zerodha Kite API**: Make sure your credentials are correct and you have the necessary permissions. Note that if your credentials are left as placeholders, the application will automatically use Yahoo Finance.
  - **Yahoo Finance API**: If you're experiencing issues with Yahoo Finance, check your internet connection and verify the symbols you're using are valid. Some Indian market symbols may need to be mapped differently.

### Frontend Issues

- **Node modules issues**: Try deleting the `node_modules` folder and running `npm install` again.
- **Connection to backend fails**: Make sure the backend server is running and the API URL in `api.js` is correct.
- **Compilation errors**: Check the terminal for error messages and fix any issues in the code.

## Next Steps

1. Create your first trading strategy using the interface
2. Run a backtest on historical data
3. Optimize your strategy parameters
4. Compare original and optimized performance

For more information on how to use the application, refer to the README.md file or the user guide section.
