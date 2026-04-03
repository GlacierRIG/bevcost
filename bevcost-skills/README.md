# bevcost — BEV Mining Fleet TCO Analysis

Analyze Total Cost of Ownership for battery electric vehicle fleets in mining operations through natural conversation.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — used to run the plugin's Python scripts with inline dependencies

## Quick Start

Just ask Claude what you need:

> Analyze the TCO for my LHD 1 fleet with 6 vehicles

> Compare two scenarios: baseline 4 LHDs vs expanded 8 LHDs with $0.10/kWh energy

> Show me OPEX breakdown and energy consumption charts

The plugin ships with a complete example dataset (two LHD fleets, three charging stations, workforce, and digital solutions) so you can start exploring immediately.

---

## Skills

### Fleet TCO

Analyze costs for a single BEV fleet — vehicles, energy, maintenance, and Battery-as-a-Service.

**Examples:**

> Analyze the total cost of ownership for 4 LHD 1 vehicles with 8 batteries

> What does it cost to run an LHD 1 fleet if energy is $0.08 per kWh?

> Show me the fleet TCO for LHD 2 vehicles at level 2 with charts

> Analyze fleet costs with a 5% discount rate and 20% CAPEX contingency

> What are the maintenance costs for 6 LHD 1 vehicles over the project life?

> Generate an Excel report for the LHD 1 fleet with $0.08/kWh energy

**What you get:** Total CAPEX and OPEX breakdown, energy consumption (kWh), energy costs, maintenance costs per vehicle, BaaS subscription costs, GHG emissions, and annual cost summaries. Can generate charts, Excel spreadsheets, or Word reports with embedded visuals.

---

### Infrastructure TCO

Analyze costs for BEV charging infrastructure — stations, equipment, construction, and cabling.

**Examples:**

> What does the level 1 charging station cost over the project lifetime?

> Analyze infrastructure costs for a station with 300 meters of cable

> How much does the level 2 charging station cost with 8 batteries instead of 6?

> Compare the workshop charger setup costs to a full charging station

> What are the infrastructure CAPEX and OPEX for all three charging stations?

> Export the level 1 charging station costs to Excel

**What you get:** Equipment purchase costs (EVSE), construction and development costs, cable installation costs, BaaS equipment fees, and CAPEX/OPEX timelines with annual breakdowns. Can export to Excel or Word with charts.

---

### Full TCO

Run a complete mine-wide analysis covering every cost domain: fleet vehicles, charging infrastructure, digital solutions, and workforce.

**Examples:**

> Run a complete TCO analysis for the entire mining operation

> What's the total cost of ownership across all domains with energy at $0.10/kWh?

> Full TCO analysis with a 5% discount rate and 6 LHD 1 vehicles

> Run a complete analysis with 200-meter cable lengths at level 1 and generate charts

> What does the full mine electrification cost with 20 level 1 operators?

> Run a full TCO and generate a Word report with charts

**What you get:** Grand totals across all domains, domain-by-domain breakdown (fleet, infrastructure, digital, workforce), year-by-year cost trends, total energy consumption and GHG emissions, and a complete financial picture from 2022 to 2030. Can generate Excel workbooks or Word reports with embedded charts.

**Default scenario includes:**

- 2 fleets — LHD 1 (4 vehicles at level 1) and LHD 2 (at level 2)
- 3 charging stations — level 1, level 2, and workshop
- 1 Fleet Management System (FMS)
- 3 workforce groups — level 1 operators, level 2 operators, electricians

---

### Compare Scenarios

Compare multiple configurations side by side to support decision-making.

**Examples:**

> Compare two scenarios: baseline with 4 LHDs versus an expanded fleet of 8 LHDs

> What happens to total costs if energy goes from $0.05 to $0.10 to $0.15 per kWh?

> Compare the baseline scenario against one with a 5% discount rate and 20% contingency

> Run a comparison: current fleet size vs adding 2 more LHD 2 vehicles at level 2

> Compare costs with and without construction costs at the level 1 station

> Compare baseline vs expanded fleet and export the results to Excel

**What you get:** A comparison table showing Total CAPEX, Total OPEX, and Total TCO for each scenario. Highlights which scenario is most cost-effective and where the differences come from. Can generate comparison charts, Excel reports, or Word documents.

**Tips:**

- Always include a baseline scenario (defaults) as your reference point
- Vary one parameter at a time for the clearest insights
- Start with 2 scenarios, then add more to refine

---

### Visualize

Generate charts and visualizations from TCO analysis results.

**Examples:**

> Show me OPEX breakdown charts for the full analysis

> Generate CAPEX breakdown and energy consumption charts

> Create maintenance cost charts for all fleets

> Show me OPEX trends over the project lifetime

> Generate all available chart types for the baseline scenario

**Available chart types:**

- **OPEX Breakdown** — stacked bar chart of annual operating costs by domain
- **CAPEX Breakdown** — stacked bar chart of annual capital costs by domain
- **OPEX Trends** — line plots showing all OPEX categories over time
- **Energy Consumption** — bar chart of annual energy use per fleet
- **Maintenance Costs** — bar chart of annual maintenance costs per fleet

**What you get:** PNG chart images displayed directly in the conversation, or embedded in Excel/Word reports. Charts use the full analysis dataset, so you can generate visuals for any scenario or parameter configuration.

---

### Explore

Go beyond the pre-built skills with freeform analysis. Claude generates custom Python code using the bevcost library to answer questions the other skills don't cover.

**Examples:**

> What parameters can I configure in the TCO model?

> Write a custom analysis that calculates NPV across discount rates from 1% to 10%

> Show me how energy consumption changes as fleet size scales from 2 to 12 vehicles

> Calculate the breakeven point where BaaS becomes cheaper than outright battery purchase

> What's the sensitivity of total OPEX to energy price changes?

> Build an Excel workbook with NPV sensitivity analysis across discount rates from 1% to 10%

**What you get:** Custom analysis results tailored to your question. Claude writes and executes Python code using the bevcost library (FleetCell, InfraCell, DigitalSolutionsCell, WorkforceCell) to compute exactly what you need. Results can be exported to Excel, Word, or any other document format.

---

## Common Workflows

### New Mine Evaluation

Evaluating the full cost of electrifying a new underground mine:

> Run a complete TCO analysis for the entire operation

Review the grand totals and domain breakdown to understand the cost landscape.

> That fleet cost looks high. Drill into the LHD 1 fleet — show me the cost drivers

Identify whether it's energy, maintenance, or BaaS driving costs.

> Compare three scenarios: baseline, one with $0.03/kWh energy, and one with 6 vehicles instead of 4

Test sensitivity to energy pricing and fleet size.

> Generate OPEX breakdown and CAPEX breakdown charts for the baseline

Produce visuals for your evaluation report.

---

### Fleet Expansion Decision

Deciding whether to add vehicles to an existing fleet:

> Compare two scenarios: current 4 LHD 1 vehicles vs expanding to 8 vehicles with 16 batteries

See the cost impact of doubling the fleet.

> The expanded fleet looks viable. Show me the detailed fleet TCO for 8 LHD 1 vehicles with charts

Get the full breakdown for the expansion option.

> What are the energy consumption and maintenance cost trends for the expanded fleet?

Understand the operational cost trajectory before committing.

> Now compare the expansion against switching to 4 LHD 2 vehicles instead

Evaluate whether a larger vehicle model is more cost-effective than adding more smaller ones.

---

### Report Generation

Producing deliverables for stakeholders:

> Run a full TCO and generate an Excel workbook with all the cost breakdowns

Get a multi-sheet spreadsheet with summary, annual breakdown, monthly details, and energy data.

> Now create a Word report with the OPEX and CAPEX charts embedded

Generate a formatted document with charts inline, ready to share.

> Compare baseline vs expanded fleet and export the comparison to Excel with charts

Side-by-side scenario analysis in a single workbook with visual summaries.

---

### Infrastructure Planning

Planning charging infrastructure for a new mining level:

> Analyze the level 1 charging station costs with 150 meters of cable

Get the baseline infrastructure cost.

> What if we need 400 meters of cable instead? How does that change the costs?

Test the impact of longer cable runs to deeper locations.

> Compare three infrastructure setups: 150m cable with construction, 400m cable with construction, and 400m cable without construction

Evaluate trade-offs between location and construction scope.

> Generate CAPEX breakdown charts for the comparison

Produce visuals for the infrastructure planning review.

---

## Reference

### Default Scenario

The plugin includes a complete example scenario covering an 8-year analysis period (CAPEX: 2022-2030, OPEX: 2023-2030).

| Domain            | Details                                                        |
| ----------------- | -------------------------------------------------------------- |
| Fleet 1           | LHD 1 — 4 vehicles, 8 batteries, level 1                       |
| Fleet 2           | LHD 2 — at level 2                                             |
| Infrastructure 1  | Level 1 — 5x LHD 1 Chargers, 150m cable, construction included |
| Infrastructure 2  | Level 2 — 4x LHD 2 Chargers + 1 Substation, 400m cable         |
| Infrastructure 3  | Workshop — 1x Workshop Charger, no construction                |
| Digital Solutions | Fleet Management System (FMS)                                  |
| Workforce 1       | 12 LHD operators (level 1)                                     |
| Workforce 2       | 15 LHD operators (level 2)                                     |
| Workforce 3       | 4 electricians (maintenance)                                   |

### Key Parameters

**Business & Financial**

| Parameter         | Default   | Description            |
| ----------------- | --------- | ---------------------- |
| Energy cost       | $0.05/kWh | Electricity rate       |
| Demand charge     | $9.50/kVA | Peak power charge      |
| CAPEX contingency | 15%       | Added to capital costs |
| Discount rate     | 3%        | For NPV calculations   |
| Diesel cost       | $1.85/L   | Comparison baseline    |

**Vehicles**

| Parameter          | LHD 1      | LHD 2      |
| ------------------ | ---------- | ---------- |
| Battery capacity   | 250 kWh    | 500 kWh    |
| Energy consumption | 50 kWh/hr  | 90 kWh/hr  |
| Unit price         | $1,500,000 | $2,000,000 |
| BaaS monthly rate  | $12,000    | $18,000    |
| Charging power     | 250 kW     | —          |

**Infrastructure**

| Parameter              | Default  | Description            |
| ---------------------- | -------- | ---------------------- |
| Development rate       | $180/m3  | Underground excavation |
| Fixed development cost | $200,000 | Per charging station   |
| Cable pull cost        | $75/m    | Per meter of cable     |

**Workforce**

| Parameter                | Default       |
| ------------------------ | ------------- |
| Underground miner salary | $130,000/year |
| Trades position salary   | $150,000/year |
