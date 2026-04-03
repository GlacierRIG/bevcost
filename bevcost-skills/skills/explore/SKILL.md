---
name: explore
description: Explore bevcost capabilities freely — generate custom Python code for any analysis. Use when the user wants to try something the pre-built skills don't cover, asks "what else can bevcost do", wants to see all available parameters, or needs custom analysis code.
---

# Freeform bevcost Exploration

You help users explore bevcost's full capabilities by generating custom Python code. Use this when the pre-built skills (fleet-tco, infra-tco, full-tco, compare-scenarios, visualize) don't cover what the user needs.

## How to Write and Run Custom Scripts

Follow the conventions in `skills/_shared/custom-scripts.md`. Write a self-contained Python script with **uv inline dependency metadata (PEP 723)** and run it directly:

```bash
uv run "$TMPDIR/bevcost_custom.py"        # macOS / Linux
uv run "$env:TEMP\bevcost_custom.py"      # Windows (PowerShell)
```

### Script template

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas",
#     "matplotlib",
#     "numpy",
#     "numpy_financial",
# ]
# ///

import sys, os
sys.path.insert(0, os.path.join(r'${CLAUDE_PLUGIN_ROOT}', 'lib'))
from bevcost.TCOmodel import FleetCell, InfraCell, DigitalSolutionsCell, WorkforceCell
from bevcost.TCOmodel import annual_cashflow_summary, stacked_bar_chart, spaghetti_line_plots
from bevcost.TCOmodel import list_to_dict, npv_calc, financial_analysis, tco_summary

# ... your analysis code ...

# After writing any output file:
# print(f"FILE:{output_path}", file=sys.stderr)
```

Only list dependencies the script actually imports — no extras. The `# /// script` block tells `uv` what to install automatically.

### Handle generated files

If your script writes **any** files for the user (charts, spreadsheets, CSVs, etc.), it **MUST emit `FILE:<path>` on stderr** for each file (see `custom-scripts.md`). After running the script, check stderr for `FILE:` lines. If any are present, you MUST read `${CLAUDE_PLUGIN_ROOT}/skills/_shared/file-handling.md` using the Read tool and follow its instructions exactly. Do NOT improvise file display, saving, or opening.

## Excel Export

If the user requests Excel export, follow the conventions in `${CLAUDE_PLUGIN_ROOT}/skills/_shared/excel-export.md`. Read the shared doc with the Read tool before generating the script. Use `openpyxl` with native Excel charts instead of embedding PNG images.

## Complete API Reference

### Classes

#### FleetCell(fleet_params, vehicles_params, evse_params, business_params, fleet_op_hours, capex_dates=None, opex_dates=None, production_sched=None, location=None)

Represents a homogeneous fleet of BEV vehicles. Call `execute_analysis()` after construction.

**Input parameters:**

`fleet_params` (dict):

- `model` (str): Vehicle model name (must match a key in vehicles data)
- `vehicles` (int): Number of vehicles in the fleet
- `batteries` (int): Total number of batteries
- `location` (str): Mine location identifier
- `fleet purchase schedule` (list): `[["YYYY-MM-DD", fraction], ...]`
- `subsidies` (list): `[["YYYY-MM-DD", fraction], ...]`
- `fleet operating hours` (list): `[["date", "V1", "V2", ...], ["YYYY-MM-DD", hours, hours, ...], ...]`

`vehicles_params` (dict):

- `model` (str): Vehicle model name
- `make` (str): Manufacturer
- `type` (str): Vehicle type (e.g., "LHD")
- `powertrain` (str): "BEV"
- `daily_operating_hours` (float): Max hours per day
- `tonnes per bucket` (float): Payload capacity
- `battery capacity` (int): kWh
- `usable battery capacity` (float): Fraction (e.g., 0.85)
- `energy consumption` (int): kWh per operating unit
- `charging time` (int): Hours to charge
- `charging power` (int): kW
- `evse model` (str): Charger model name
- `BaaS monthly rate` (int): $/month for Battery-as-a-Service
- `unit price` (int): Purchase price per vehicle
- `maintenance costs` (dict): `{"Machine Hours": [intervals], "Major Components": [costs]}`

`evse_params` (dict):

- `evse type` (str): "charger" or "transformer"
- `model` (str): Equipment model name
- `charge current` (int): Amps
- `cooling cube power` (int): kW
- `efficiency` (float): 0-1
- `power factor` (float): 0-1
- `current derating` (float): 0-1
- `BaaS charger monthly rate` (int): $/month
- `unit price` (int): Purchase price

`business_params` (dict):

- `financial.CAPEX contingency` (float): e.g., 0.15
- `financial.discount rate` (float): e.g., 0.03
- `energy costs.cost per kWh` (float): $/kWh
- `energy costs.cost per kVA` (float): $/kVA
- `energy costs.diesel cost` (float): $/L
- `emissions factors.diesel CO2e emissions` (float)
- `emissions factors.grid CO2e emissions` (float)
- `subsidies.fuel rebate` (float): $ amount
- `labour rates.frequency` (str): "annual"
- `labour rates.<role>` (int): Annual salary

**Output attributes (after `execute_analysis()`):**

- `fleet_costs` (DataFrame): Vehicle purchase CAPEX
- `maintenance_costs` (DataFrame): Monthly maintenance per vehicle
- `energy_consumed` (DataFrame): Monthly energy consumption (kWh)
- `energy_costs` (DataFrame): Monthly electricity costs ($)
- `power_consumed` (DataFrame): Peak power draw
- `power_costs` (DataFrame): Monthly demand charges ($)
- `baas_costs` (DataFrame): Monthly BaaS fees ($)
- `GHG_emissions` (DataFrame): Monthly GHG emissions
- `opex_subsidies` (DataFrame): Monthly OPEX subsidies
- `capex_timeline` (DataFrame): Monthly CAPEX timeline
- `opex_timeline` (DataFrame): Monthly OPEX timeline
- `capex_variables` (dict): CAPEX cost breakdown
- `opex_variables` (dict): OPEX cost breakdown
- `info` (str): Object description
- `location` (str): Location identifier

#### InfraCell(infra_params, facility_params, evse_params, capex_dates=None, opex_dates=None, location=None)

Represents BEV charging infrastructure. Call `execute_analysis()` after construction.

**Input `infra_params`:**

- `location` (str): Mine location
- `infrastructure type` (str): e.g., "charging station"
- `construction costs` (str): "True" or "False"
- `charger-cooler ratio` (int): Chargers per cooler
- `cable length` (int): Meters
- `batteries` (int): Battery count
- `evse` (dict): `{"model_name": count, ...}`
- `construction schedule` (list): `[["YYYY-MM-DD", fraction], ...]`
- `capex schedule` (list): `[["YYYY-MM-DD", fraction], ...]`
- `BaaS subscription` (dict): `{"frequency": "monthly", "dates": {"start date": ..., "end date": ...}}`

**Output attributes:**

- `equipment_costs` (DataFrame): EVSE purchase costs
- `construction_costs` (DataFrame): Infrastructure construction
- `baas_costs` (DataFrame): Equipment BaaS fees
- `capex_timeline`, `opex_timeline` (DataFrame)
- `capex_variables`, `opex_variables` (dict)

#### DigitalSolutionsCell(data, solutions_params, capex_dates=None, opex_dates=None, location=None)

Represents digital solutions (software). Call `execute_analysis()` after construction.

**Input `data`:**

- `location` (str)
- `type` (str): e.g., "software"
- `capex schedule` (list): `[["YYYY-MM-DD", fraction], ...]`
- `opex schedule` (list): `[["YYYY-MM-DD", fraction], ...]`

**Input `solutions_params`:**

- `solution name` (str)
- `unit price` (int): Purchase price
- `subscription price` (int): Annual subscription

**Output attributes:**

- `software_costs` (DataFrame): Software CAPEX
- `software_subs` (DataFrame): Subscription OPEX
- `capex_timeline`, `opex_timeline` (DataFrame)
- `capex_variables`, `opex_variables` (dict)

#### WorkforceCell(data, business_params, opex_dates=None, location=None)

Represents a group of workers. Call `execute_analysis()` after construction.

**Input `data`:**

- `name` (str): Group identifier
- `role` (str): Must match a key in `business_params.labour rates`
- `description` (str)
- `location` (str)
- `department` (str)
- `personnel` (dict): `{"date": [years], "workforce size": [counts]}`

**Output attributes:**

- `workforce` (DataFrame): Personnel count per year
- `labour` (DataFrame): Labour costs per year
- `variables` (dict): Cost breakdown

### Standalone Functions

- `annual_cashflow_summary(fleet_objects=None, infra_objects=None, labour_objects=None, digital_solution_objects=None)` → `(opex_objects, opex_vars, capex_objects, capex_vars)` — Aggregates annual costs across all object types
- `tco_summary(fleet_objects, infra_objects, labour_objects, digital_solution_objects, verbose=True)` → `(capex, opex, production, consumption, waste)` — Summary across all domains
- `npv_calc(start_year, npv_df, discount)` → DataFrame — Net Present Value calculation
- `financial_analysis(start_year, costs_list, business_params, costs_dict)` — Comprehensive financial analysis
- `list_to_dict(input_list, key_name)` → dict — Convert list of dicts to dict keyed by a field

### Visualization Functions

- `stacked_bar_chart(ax, data, x_label=None, label_formats={'x': '${x:,.2f}', 'y': None}, out_format='svg')` — Stacked bar chart. `data` format: `{'x': [...], 'cost labels': [...] or None, 'data': [[...], ...] or [pd.Series, ...]}`
- `spaghetti_line_plots(axes, title, df, palette)` — Grid of line plots. `df` must have an 'x' column plus one column per cost category.

### Bundled Data Files

The plugin bundles example data at `${CLAUDE_PLUGIN_ROOT}/data/`:

- `data.json` — Equipment catalog (vehicles, chargers, infrastructure specs, digital solutions)
- `analysis.json` — Analysis configuration (dates, business params, fleet specs, workforce)

Load them with:

```python
import json, os
plugin_root = r'${CLAUDE_PLUGIN_ROOT}'
with open(os.path.join(plugin_root, 'data', 'data.json')) as f:
    equipment_data = json.load(f)
with open(os.path.join(plugin_root, 'data', 'analysis.json')) as f:
    analysis_data = json.load(f)
```
