---
name: full-tco
description: Run a complete Total Cost of Ownership analysis across all cost domains — fleet vehicles, charging infrastructure, digital solutions, and workforce. Use when the user wants a comprehensive mine-wide BEV cost analysis or total cost picture.
---

# Full TCO Analysis

You help users run a complete Total Cost of Ownership analysis for a BEV mining operation, covering all four cost domains: fleet vehicles, charging infrastructure, digital solutions, and workforce.

## Workflow

1. **Explain what's included** — The default scenario includes:
   - **2 fleets**: LHD 1 (4 vehicles, level 1) and LHD 2 (level 2)
   - **3 charging stations**: level 1, level 2, and workshop
   - **1 digital solution**: Fleet Management System
   - **3 workforce groups**: level 1 miners, level 2 miners, electricians
   - **Analysis period**: CAPEX 2022–2030, OPEX 2023–2030

2. **Ask what to change** — The user can override any parameter. Common changes:
   - Fleet sizes, vehicle counts
   - Energy costs, discount rates
   - Additional/fewer infrastructure locations

3. **Run the script**:

   Write the JSON to a temp file, then pipe it in — never interpolate JSON into the shell:

   ```bash
   cat <<'JSONEOF' | uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_full_tco.py
   <overrides_json>
   JSONEOF
   ```

4. **Handle charts** — If `generate_charts` was true, follow the instructions in `skills/_shared/chart-handling.md` to display, offer to save, and offer to open the generated charts.

5. **Explain results** — Present:
   - Grand total CAPEX and OPEX
   - Breakdown by domain (fleet, infra, digital, workforce)
   - Biggest cost drivers
   - Year-by-year trends

## Override JSON Format

```json
{
  "business": {
    "energy costs": { "cost per kWh": 0.08 },
    "financial": { "discount rate": 0.05 }
  },
  "fleet_overrides": [{ "vehicles": 6 }, null],
  "infra_overrides": [{ "cable length": 200 }, null, null],
  "workforce_overrides": [
    { "personnel": { "workforce size": [15, 15, 15, 15, 15, 15, 15, 15] } }
  ],
  "generate_charts": true
}
```

Use `null` in override arrays to skip overriding a specific item.
