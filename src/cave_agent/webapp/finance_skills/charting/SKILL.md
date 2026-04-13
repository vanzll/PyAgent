---
name: charting
description: Render price history and relative performance charts for the financial UI
---

# Charting Skill

Use this skill to create chart artifacts for the financial workbench.

After activation:

- Use `plot_price_history(ticker, filename='price-history')` for a single-security price chart.
- Use `plot_relative_performance(filename='normalized-returns')` for normalized returns across all loaded tickers.
