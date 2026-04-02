---
name: fleet-tco
description: Analyze the Total Cost of Ownership for a BEV (Battery Electric Vehicle) mining fleet. Use when the user asks about fleet costs, vehicle operating costs, LHD costs, energy consumption, maintenance costs, or BaaS (Battery-as-a-Service) costs for mining vehicles.
---

# Fleet TCO Analysis

You help users analyze the total cost of ownership for a Battery Electric Vehicle (BEV) mining fleet. You run the bevcost analysis engine to compute CAPEX, OPEX, energy consumption, maintenance, BaaS, and GHG emissions.

## Workflow

1. **Gather inputs** — Ask the user what they want to analyze. Show them the key parameters they can configure (below) and the defaults. Only ask about parameters they want to change.

2. **Build overrides JSON** — Map the user's inputs to the override format below.

3. **Run the script** — Execute:

   Write the JSON to a temp file, then pipe it in — never interpolate JSON into the shell:

   ```bash
   cat <<'JSONEOF' | uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_fleet_analysis.py
   <overrides_json>
   JSONEOF
   ```

   Capture stdout (JSON results) and stderr (chart paths prefixed with `CHART:`).

4. **Explain results** — Present the key findings conversationally:
   - Total CAPEX and OPEX over the analysis period
   - Biggest cost drivers (energy, maintenance, BaaS)
   - Energy consumption and GHG emissions
   - Annual cost breakdown

5. **Handle charts** — If `generate_charts` was true, follow the instructions in `skills/_shared/chart-handling.md` to display, offer to save, and offer to open the generated charts.

## Key Parameters (with defaults from bundled example data)

Tell the user these are the main things they can tweak:

| Parameter                 | Default         | Override path                          |
| ------------------------- | --------------- | -------------------------------------- |
| Fleet index (which fleet) | 0 (first fleet) | `fleet_index`                          |
| Vehicle count             | 4               | `fleet.vehicles`                       |
| Battery count             | 8               | `fleet.batteries`                      |
| Vehicle model             | "LHD 1"         | `fleet.model`                          |
| Energy cost ($/kWh)       | $0.05           | `business.energy costs.cost per kWh`   |
| Demand charge ($/kVA)     | $9.50           | `business.energy costs.cost per kVA`   |
| CAPEX contingency         | 15%             | `business.financial.CAPEX contingency` |
| Discount rate             | 3%              | `business.financial.discount rate`     |
| BaaS monthly rate         | $12,000         | `vehicles.BaaS monthly rate`           |
| Vehicle unit price        | $1,500,000      | `vehicles.unit price`                  |
| Generate charts           | false           | `generate_charts`                      |

## Override JSON Format

```json
{
  "fleet_index": 0,
  "fleet": {
    "vehicles": 4,
    "batteries": 8
  },
  "business": {
    "energy costs": {
      "cost per kWh": 0.05,
      "cost per kVA": 9.5
    },
    "financial": {
      "CAPEX contingency": 0.15,
      "discount rate": 0.03
    }
  },
  "vehicles": {
    "unit price": 1500000,
    "BaaS monthly rate": 12000
  },
  "generate_charts": true
}
```

Only include fields the user wants to change. Unspecified fields use defaults.

## Available Fleets in Default Data

- **Fleet 0**: LHD 1 — 4 vehicles, 8 batteries, level 1 location
- **Fleet 1**: LHD 2 — different vehicle specs (check `fleet_index: 1`)

## Output Structure

The script returns JSON with these keys:

- `summary` — vehicle model, count, batteries, location
- `capex_timeline` — monthly CAPEX costs
- `opex_timeline` — monthly OPEX costs
- `energy_consumed` — monthly energy consumption (kWh)
- `energy_costs` — monthly electricity costs ($)
- `maintenance_costs` — monthly maintenance costs per vehicle ($)
- `baas_costs` — monthly Battery-as-a-Service costs ($)
- `GHG_emissions` — monthly greenhouse gas emissions
- `fleet_costs` — vehicle purchase costs
- `annual_opex` — annual OPEX summary by cost category
- `annual_capex` — annual CAPEX summary by cost category
