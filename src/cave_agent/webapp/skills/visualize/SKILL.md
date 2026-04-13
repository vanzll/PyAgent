---
name: visualize
description: Create and export simple chart artifacts from processed DataFrames
---

# Visualize Skill

Use this skill to create chart artifacts for the web UI.

After activation:

- Use `plot_frame(df_name, kind, x, y, title, filename)` for quick charts.
- Supported `kind` values: `line`, `bar`, `scatter`, `hist`.

The helper saves the figure automatically through the workspace so it appears as a downloadable artifact.
