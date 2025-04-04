# Strategy Debug Directory

This directory contains debug files that capture the state of trading strategies as they are executed by the backtest engine.

## Debug File Format

Each debug file is a Markdown (.md) file that contains:

1. **Original User-Defined Strategy** - The strategy configuration as defined by the user
2. **Backtrader Strategy Information** - How the strategy was translated for Backtrader
3. **Dynamically Created Backtrader Strategy Class** - The actual Python code of the strategy class
4. **Backtest Results** - A summary of the backtest execution results and trades

## Filename Format

Debug files follow this naming convention:
`{strategy_id}_{timestamp}_{debug_id}_debug.md`

## Purpose

These files are useful for:
- Understanding how user-defined strategies are translated into Backtrader classes
- Debugging issues with strategy execution
- Comparing different strategy implementations
- Analyzing backtest results in detail

## Manual Generation

You can manually generate a debug file by running a backtest through the API or UI.
