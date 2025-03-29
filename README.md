# Trading Strategy Hyper-Tuner

A full-stack application for creating, backtesting, and optimizing trading strategies using Bayesian optimization.

## Features

- Create trading strategies with technical indicators
- Define entry and exit conditions
- Run backtests on historical market data
- Optimize strategy parameters using Bayesian optimization
- Visualize performance improvements and results
- Multiple data sources with automatic fallback mechanism:
  - Zerodha Kite API (primary source for Indian markets)
  - Yahoo Finance (automatic fallback option)

## Technology Stack

### Backend

- Python 3.8+
- Flask (Web framework)
- TA-Lib (Technical indicators)
- Backtrader (Backtesting engine)
- scikit-optimize (Bayesian Optimization)
- Pandas (Data manipulation)
- Multiple market data sources:
  - Zerodha Kite API (primary source for Indian markets)
  - Yahoo Finance API (automatic fallback for testing without Zerodha credentials)

### Frontend

- React
- Recharts (Visualizations)
- Tailwind CSS (Styling)
- Axios (HTTP client)
- React Datepicker (Date input)

## Project Structure

```
hypertuner/
├── backend/                   # Python Flask backend
│   ├── app.py                 # Main Flask application
│   ├── backtest_engine.py     # Integrates with Backtrader for backtesting
│   ├── data_provider.py       # Abstract base class for data providers
│   ├── data_provider_factory.py # Factory for selecting appropriate data provider
│   ├── indicator_mappings.json # Mappings for technical indicators
│   ├── indicators.py          # Wrapper for TA-Lib indicators
│   ├── kite_integration.py    # Zerodha Kite API data provider
│   ├── optimizer.py           # Implements Bayesian Optimization
│   ├── requirements.txt       # Python dependencies
│   ├── strategies/           # Directory for storing saved strategies
│   ├── strategy_manager.py    # Handles strategy creation and management
│   └── yahoo_finance_integration.py # Yahoo Finance data provider
│
├── frontend/                  # React frontend
│   ├── public/                # Static files
│   ├── src/                   # Source code
│   │   ├── components/        # Reusable UI components
│   │   ├── screens/           # Application screens
│   │   │   ├── StrategyCreation.js   # Strategy creation screen
│   │   │   ├── BacktestParameters.js # Backtesting parameters screen
│   │   │   ├── HyperTuning.js        # Hyper-tuning screen
│   │   │   └── Results.js            # Results display screen
│   │   ├── services/          # API integration services
│   │   ├── App.js             # Main application component
│   │   └── index.js           # Entry point
│   ├── package.json           # Node.js dependencies
│   └── tailwind.config.js     # Tailwind CSS configuration
│
├── DATA_PROVIDER_IMPLEMENTATION.md  # Documentation for data provider implementation
├── SETUP_GUIDE.md            # Detailed setup instructions
├── masterplan.md             # Project development roadmap
└── README.md                 # Project documentation
```

## Data Provider Architecture

The application implements a flexible data provider architecture that allows seamless switching between different market data sources:

1. **Zerodha Kite API (Primary)**: Used when valid credentials are provided
2. **Yahoo Finance API (Fallback)**: Automatically used when Zerodha credentials are missing or authentication fails

This implementation allows users to test the application without requiring an actual Zerodha account, making it more accessible and easier to set up for demonstration purposes.

### Key Components:

- **DataProvider (Abstract Base Class)**: Defines the common interface for all data providers
- **KiteIntegration**: Implementation for Zerodha Kite API
- **YahooFinanceIntegration**: Implementation for Yahoo Finance API
- **DataProviderFactory**: Factory class that determines which provider to use

### Symbol Mapping System

The application includes a sophisticated mapping system between different data providers' symbol formats:

```python
# Example of Zerodha to Yahoo Finance symbol mapping
self.symbol_mapping = {
    "NIFTY 50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN",
    # More mappings...
}
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js and npm
- TA-Lib (can be challenging to install - see instructions below)

### Installing TA-Lib

Before installing the Python dependencies, you need to install TA-Lib which has C dependencies.

#### macOS

```bash
brew install ta-lib
```

#### Windows

Download the appropriate wheel file from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib) and install it with pip:

```bash
pip install TA_Lib-0.4.24-cp38-cp38-win_amd64.whl
```

(Make sure to download the correct wheel for your Python version and system architecture)

#### Linux

```bash
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
```

### Setting Up the Backend

1. Navigate to the backend directory:
   ```bash
   cd /Users/sushant/Documents/Python/Spyder/candlesticks/hypertuner/backend
   ```

2. Create and activate a virtual environment:
   ```bash
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   
   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure Market Data Provider:
   
   You have two options for market data:
   
   **Option 1: Use Zerodha Kite API (Recommended for Indian Markets)**
   
   Open `kite_integration.py` and replace the placeholder credentials with your actual Zerodha API key and secret:
   ```python
   self.api_key = "your_api_key"
   self.api_secret = "your_api_secret"
   ```
   
   **Option 2: Use Yahoo Finance (No configuration needed)**
   
   If you leave the Zerodha credentials as placeholders, the application will automatically use Yahoo Finance as the data source.

5. Start the Flask server:
   ```bash
   python app.py
   ```
   The server will run at `http://localhost:3001`.

### Setting Up the Frontend

1. Navigate to the frontend directory:
   ```bash
   cd /Users/sushant/Documents/Python/Spyder/candlesticks/hypertuner/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```
   The application will open in your browser at `http://localhost:3000`.

## User Guide

### Creating a Strategy

1. Navigate to the "Strategy Creation" tab
2. Fill in the basic strategy information:
   - Strategy Name
   - Strategy Type (Buy/Sell)
   - Symbol
   - Timeframe
3. Add entry conditions:
   - Select indicators
   - Configure parameters
   - Assign variable names
4. Add exit conditions:
   - Select indicators
   - Configure parameters
   - Assign variable names
5. Click "Save Strategy & Continue"

### Setting Up Backtest Parameters

1. Navigate to the "Backtest Parameters" tab
2. Enter the initial capital
3. Select start and end dates for the backtest
4. Click "Run Backtest & Continue"

### Running Optimization

1. Navigate to the "Hyper-Tuning" tab
2. Review the original backtest results
3. Click "Start Optimization"
4. Monitor the optimization progress
5. Once complete, proceed to the "Results" tab

### Viewing Results

1. Navigate to the "Results" tab
2. Compare original and optimized performance metrics
3. View the equity curve comparison
4. Check the optimized parameters
5. Download the CSV report or save the optimized strategy

## Data Providers

The application supports two data providers for market data:

### Zerodha Kite API

The Zerodha Kite API is the primary data source for Indian markets. It provides high-quality market data for backtesting and optimization. To use this data source, you need to:

1. Have a Zerodha trading account
2. Register for Kite Connect API access
3. Configure your API key and secret in the application

### Yahoo Finance API (Fallback)

Yahoo Finance API is automatically used as a fallback when:

- Zerodha Kite API credentials are not configured
- Zerodha Kite API authentication fails

This allows you to test the application without requiring a Zerodha account. The application automatically detects which data source to use, and displays the active source in the UI.

The application includes a comprehensive symbol mapping system to handle differences between Zerodha and Yahoo Finance symbols.

## Troubleshooting

### Common Issues

1. **TA-Lib Installation Errors**:
   - Make sure you've installed the C dependencies correctly
   - Try using a pre-built wheel file for your platform

2. **API Connection Issues**:
   - Verify your API key and secret
   - Check that you've authenticated with Kite
   - Ensure your API permissions are correctly set

3. **Backtest Engine Errors**:
   - Check that the symbol exists and data is available for the selected date range
   - Verify that indicators are correctly configured

4. **Frontend Connection Issues**:
   - Make sure the backend server is running
   - Check that the API URL in the frontend service matches your backend server address and port

### Getting Help

If you encounter issues not covered here, check the following resources:
- Backtrader documentation: https://www.backtrader.com/docu/
- TA-Lib documentation: https://mrjbq7.github.io/ta-lib/
- Zerodha Kite API documentation: https://kite.trade/docs/connect/v3/
- Yahoo Finance API documentation: https://pypi.org/project/yfinance/

## License

This project is licensed under the MIT License.
