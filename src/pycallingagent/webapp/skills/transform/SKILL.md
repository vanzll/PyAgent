---
name: transform
description: Apply common data-cleaning and joining helpers to uploaded tables
---

# Transform Skill

Use this skill for common data cleaning patterns.

After activation:

- Use `standardize_columns(df)` to convert column names to snake_case.
- Use `merge_frames(left_name, right_name, on, how='inner', output_name=None)` to join tables and optionally keep the result in `dataframes`.

You can still write direct pandas code when needed, but prefer these helpers for repetitive cleanup.
