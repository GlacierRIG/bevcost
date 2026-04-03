---
name: compare-scenarios
description: Compare multiple BEV mining TCO scenarios side by side. Use when the user wants to compare different fleet sizes, energy costs, equipment configurations, or any "what if" analysis.
---

# Scenario Comparison

You help users compare multiple TCO scenarios side by side. Each scenario runs a full TCO analysis with different parameters, then the results are presented in a comparison table.

## Workflow

1. **Define scenarios** — Help the user define 2+ scenarios. Each scenario is a name + a set of overrides. Examples:
   - "Baseline" vs "6 LHDs instead of 4"
   - "Low energy cost" vs "High energy cost"
   - "With construction" vs "Pre-built infrastructure"

2. **Build input JSON** — Each scenario uses the same override format as the full-tco skill.

3. **Run the script**:

   Write the JSON to a temp file, then pipe it in — never interpolate JSON into the shell:

   ```bash
   cat <<'JSONEOF' | uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_comparison.py
   <config_json>
   JSONEOF
   ```

4. **Handle generated files** — After running any script, check stderr for `FILE:` lines. If **any** files were generated, you MUST read `${CLAUDE_PLUGIN_ROOT}/skills/_shared/file-handling.md` using the Read tool and follow its instructions exactly. Do NOT improvise file display, saving, or opening — the shared file defines the complete workflow. This applies to all generated files, not just charts.

5. **Present comparison** — Show a clear comparison table:
   - Scenario names
   - Total CAPEX, Total OPEX, Total TCO
   - Key differences and which scenario is more cost-effective

## Input Format

```json
{
  "scenarios": [
    {
      "name": "Baseline (4 LHDs)",
      "overrides": {}
    },
    {
      "name": "Expanded Fleet (8 LHDs)",
      "overrides": {
        "fleet_overrides": [{ "vehicles": 8, "batteries": 16 }]
      }
    },
    {
      "name": "High Energy Cost",
      "overrides": {
        "business": { "energy costs": { "cost per kWh": 0.15 } }
      }
    }
  ],
  "generate_charts": true
}
```

## Tips

- Start with 2 scenarios to keep it simple
- Vary one parameter at a time for clearest insights
- Always include a "baseline" scenario using defaults for reference
