---
name: infra-tco
description: Analyze the Total Cost of Ownership for BEV charging infrastructure in mining operations. Use when the user asks about charging station costs, EVSE costs, infrastructure construction costs, or charging equipment costs.
---

# Infrastructure TCO Analysis

You help users analyze the total cost of ownership for BEV charging infrastructure in mining operations — charging stations, EVSE equipment, construction, and BaaS costs.

## Workflow

1. **Gather inputs** — Ask what infrastructure the user wants to analyze. Show key parameters and defaults.
2. **Build overrides JSON** — Map user inputs to override format.
3. **Run the script**:

   Write the JSON to a temp file, then pipe it in — never interpolate JSON into the shell:

   ```bash
   cat <<'JSONEOF' | uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_infra_analysis.py
   <overrides_json>
   JSONEOF
   ```

4. **Explain results** — Present CAPEX/OPEX breakdown, equipment costs, construction costs.
5. **Handle generated files** — After running any script, check stderr for `FILE:` lines. If **any** files were generated, you MUST read `${CLAUDE_PLUGIN_ROOT}/skills/_shared/file-handling.md` using the Read tool and follow its instructions exactly. Do NOT improvise file display, saving, or opening — the shared file defines the complete workflow. This applies to all generated files, not just charts.

6. **Excel export** — If the user requests Excel export, write a custom script following `${CLAUDE_PLUGIN_ROOT}/skills/_shared/excel-export.md`. Use the analysis JSON results as input data. Read the shared doc with the Read tool before generating the script.

## Key Parameters (defaults)

| Parameter            | Default   | Override path                         |
| -------------------- | --------- | ------------------------------------- |
| Infrastructure index | 0         | `infra_index`                         |
| Location             | "level 1" | `infrastructure.location`             |
| Construction costs   | "True"    | `infrastructure.construction costs`   |
| Charger-cooler ratio | 2         | `infrastructure.charger-cooler ratio` |
| Cable length (m)     | 150       | `infrastructure.cable length`         |
| Battery count        | 6         | `infrastructure.batteries`            |
| Generate charts      | false     | `generate_charts`                     |

## Available Infrastructure in Default Data

- **Infra 0**: Level 1 charging station — 5x LHD 1 Chargers, 150m cable, construction included
- **Infra 1**: Level 2 charging station — 4x LHD 2 Chargers + 1x Substation, 400m cable
- **Infra 2**: Workshop — 1x Workshop Charger, no construction

## Override JSON Format

```json
{
  "infra_index": 0,
  "infrastructure": {
    "cable length": 200,
    "batteries": 8,
    "charger-cooler ratio": 3
  },
  "generate_charts": true
}
```
