---
name: tabular-ingest
description: Inspect uploaded CSV and Excel tables, preview schemas, and persist cleaned tabular outputs
---

# Tabular Ingest Skill

Use this skill when you need to inspect or persist uploaded tabular data.

After activation:

- Use `list_dataframes()` to inspect available DataFrame names, columns, and row counts.
- Access parsed tables via the `dataframes` variable.
- Use `save_dataframe_artifact(df, name, format='csv')` to export a processed table.

Always save tables that should appear in the UI through `save_dataframe_artifact`.
