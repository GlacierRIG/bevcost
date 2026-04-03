---
name: visualize
description: Generate charts and visualizations from BEV mining TCO analysis results. Use when the user asks for charts, plots, graphs, visualizations, or to "show me" cost data.
---

# TCO Visualization

You generate charts from bevcost TCO analysis results. The script runs a full analysis and produces specific chart types.

## Workflow

1. **Ask what to visualize** — Which chart types does the user want?
2. **Run the script**:

   Write the JSON to a temp file, then pipe it in — never interpolate JSON into the shell:

   ```bash
   cat <<'JSONEOF' | uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_visualization.py
   <config_json>
   JSONEOF
   ```

3. **Handle generated files** — You MUST read `${CLAUDE_PLUGIN_ROOT}/skills/_shared/file-handling.md` using the Read tool and follow its instructions exactly. Do NOT improvise file display, saving, or opening — the shared file defines the complete workflow.

## Available Chart Types

| Chart              | Key               | Description                                           |
| ------------------ | ----------------- | ----------------------------------------------------- |
| OPEX Breakdown     | `opex_breakdown`  | Stacked bar chart of annual OPEX by domain            |
| CAPEX Breakdown    | `capex_breakdown` | Stacked bar chart of annual CAPEX by domain           |
| OPEX Trends        | `opex_trends`     | Spaghetti line plots of all OPEX categories over time |
| Energy Consumption | `energy`          | Bar chart of annual energy consumption per fleet      |
| Maintenance Costs  | `maintenance`     | Bar chart of annual maintenance costs per fleet       |

## Input Format

```json
{
  "overrides": {},
  "charts": ["opex_breakdown", "capex_breakdown", "energy", "maintenance"]
}
```

The `overrides` field uses the same format as the full-tco skill. Omit it to use defaults.

Generated file paths are printed to stderr prefixed with `FILE:`. Read each image file to display it inline; list other files by name and size.
