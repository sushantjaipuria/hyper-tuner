# Hyper-Tuner Project Structure

This document provides a comprehensive overview of the Hyper-Tuner project structure. The application is designed to hyperparameter-tune variables in user-defined trading strategies.

## Project Overview

The project is organized as a full-stack application with frontend and backend components:

- The **backend** is a Python Flask application that handles trading strategy execution, backtesting, and optimization
- The **frontend** is a React application that provides a user interface for strategy creation, optimization configuration, and results visualization

## Root Directory Structure

```
/
├── .devcontainer/                  # Development container configuration
│   ├── Dockerfile                  # Docker configuration for development
│   ├── devcontainer.json           # VS Code dev container settings
│   └── docker-compose.yml          # Docker compose configuration
├── .gitignore                      # Git ignore file
├── DATA_PROVIDER_IMPLEMENTATION.md # Guide for implementing data providers
├── README.md                       # Project overview and documentation
├── SETUP_GUIDE.md                  # Setup instructions
├── masterplan.md                   # Development roadmap and plan
├── update_files.js                 # Utility script for updating files
├── backend/                        # Backend application (Python/Flask)
└── frontend/                       # Frontend application (React)
```

## Backend Structure

```
/backend/
├── app.py                          # Main Flask application entry point
├── backtest_engine.py              # Backtesting logic implementation
├── config.py                       # Configuration settings
├── data_provider.py                # Abstract data provider interface
├── data_provider_factory.py        # Factory for creating data providers
├── debug/                          # Debug utilities and logs
│   ├── .gitkeep                    # Empty file to ensure directory is tracked
│   ├── README.md                   # Debug documentation
│   ├── app.log                     # Application log
│   ├── gitkeep.txt                 # Tracker file
│   └── strategy-comparison.md      # Strategy comparison debug info
├── debug_utils.py                  # Debugging utility functions
├── indicator_mappings.json         # Mapping for technical indicators
├── indicators.py                   # Technical indicator implementations
├── kite_config.json                # Zerodha Kite API configuration
├── kite_config_satyam.json         # User-specific Kite configuration
├── kite_config_sushant.json        # User-specific Kite configuration
├── kite_integration.py             # Zerodha Kite API integration
├── logging_config.py               # Logging configuration
├── optimizer.py                    # Strategy optimization engine
├── report_generator.py             # Backtest and optimization report generator
├── requirements.txt                # Python dependencies
├── strategies/                     # Trading strategies storage
│   ├── [strategy-uuid].json        # Strategy configuration files
│   └── [strategy-uuid]/            # Strategy-specific directories
│       ├── backtests/              # Backtest results for the strategy
│       └── optimizations/          # Optimization results for the strategy
├── strategy_manager.py             # Strategy management utilities
├── test_logging.py                 # Logging test script
├── update_frontend.js              # Script to update frontend components
├── update_indicators.py            # Script to update technical indicators
├── utils.py                        # Utility functions
└── yahoo_finance_integration.py    # Yahoo Finance API integration
```

## Frontend Structure

```
/frontend/
├── package-lock.json                # NPM dependencies lock file
├── package.json                     # NPM configuration and dependencies
├── public/                          # Public static assets
├── src/                             # Source code
│   ├── App.css                      # Main application styles
│   ├── App.js                       # Main application component
│   ├── components/                  # Reusable UI components
│   │   ├── BacktestReportButton.js  # Button for generating backtest reports
│   │   ├── KiteAuthModal.js         # Zerodha Kite authentication modal
│   │   ├── KiteTokenExpiredModal.js # Token expiration notification
│   │   └── StrategyTuner.js         # Strategy parameter tuning component
│   ├── context/                     # React context providers
│   │   └── DataSourceContext.js     # Data source management context
│   ├── index.css                    # Global styles
│   ├── index.js                     # Application entry point
│   ├── reportWebVitals.js           # Performance monitoring
│   ├── screens/                     # Application screens/pages
│   │   ├── BacktestParameters.js    # Backtest configuration screen
│   │   ├── HyperTuning.js           # Hyperparameter tuning screen
│   │   ├── Results.js               # Results visualization screen
│   │   └── StrategyCreation.js      # Strategy creation screen
│   ├── services/                    # API and service integrations
│   │   └── api.js                   # Backend API client
│   └── utils/                       # Utility functions
│       ├── README.md                # Utilities documentation
│       ├── dateUtils.js             # Date handling utilities
│       └── dateUtils.test.js        # Tests for date utilities
└── tailwind.config.js               # Tailwind CSS configuration
```

## Strategy Structure

Strategies are stored as JSON files with a UUID-based naming convention. Each strategy has the following structure:

```json
{
  "name": "strategy_name",
  "type": "buy/sell",
  "symbol": "TICKER",
  "timeframe": "day/hour/minute/etc",
  "entry_conditions": [
    {
      "indicator": "INDICATOR_NAME",
      "comparison": "COMPARISON_OPERATOR",
      "params": {
        "param1": "value1",
        "param2": "value2"
      },
      "variable": "variable_name",
      "threshold": value
    }
  ],
  "exit_conditions": [],
  "stop_loss": value,
  "target_profit": value,
  "strategy_id": "UUID",
  "created_at": "TIMESTAMP",
  "updated_at": "TIMESTAMP"
}
```

Each strategy has its own directory for storing backtests and optimization results.

## Key Components

1. **Backend**:
   - `app.py`: Main Flask application with API endpoints
   - `backtest_engine.py`: Core backtesting logic
   - `optimizer.py`: Strategy optimization engine
   - `strategy_manager.py`: Manages strategy creation, updating, and deletion
   - `indicators.py`: Technical indicator implementations
   - Data providers: Modular system with Zerodha Kite and Yahoo Finance integrations

2. **Frontend**:
   - `App.js`: Main application with routing
   - Screens: Individual pages for different functionality
   - Components: Reusable UI elements
   - Context: State management using React Context
   - Services: Backend API communication

## Development Environment

The project includes a development container configuration with:
- Docker configuration for consistent development environment
- VSCode integration for seamless development
- Docker Compose for multi-container setup

## Data Providers

The application supports multiple data sources through a modular data provider system:
- Abstract data provider interface in `data_provider.py`
- Factory pattern for creating providers in `data_provider_factory.py`
- Implementations for Zerodha Kite and Yahoo Finance
