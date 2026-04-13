---
name: financial-comparison
description: Build peer comparison tables and persist them as downloadable artifacts
---

# Financial Comparison Skill

Use this skill to compare multiple requested tickers.

After activation:

- Use `get_comparison_frame()` to inspect the prepared comparison DataFrame.
- Use `save_comparison_artifact(name='comparison', format='csv')` to export the current comparison frame.
- Use `save_custom_frame(df, name, format='csv')` to persist any derived comparison table.
