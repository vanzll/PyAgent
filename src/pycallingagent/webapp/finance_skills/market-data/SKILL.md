---
name: market-data
description: Inspect market snapshots, price history, macro series, and optional news for requested tickers
---

# Market Data Skill

Use this skill when you need to inspect the loaded market data before analysis.

After activation:

- Use `list_tickers()` to see which securities are loaded.
- Use `get_market_snapshot(ticker)` for the current market summary.
- Use `get_price_history(ticker)` for the raw price DataFrame.
- Use `list_macro_series()` to inspect available macroeconomic series.
- Use `get_news_items(ticker)` when the runtime includes recent headlines.
