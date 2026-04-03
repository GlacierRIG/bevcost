# Excel Export — Native Charts with openpyxl

When a user requests Excel export from any bevcost skill, generate a custom Python script (following `custom-scripts.md`) that creates a well-formatted workbook with **native Excel charts** embedded directly in the spreadsheet.

## Why native charts over PNGs

- Native charts are interactive in Excel (hover, resize, reformat)
- They update automatically if the user edits the underlying data
- No external image files to manage
- Professional appearance matching standard Excel workflows

## Dependencies

Add `openpyxl` to the script's inline dependency block:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["openpyxl"]
# ///
```

## Workbook structure

1. **Summary sheet first** — high-level totals (CAPEX, OPEX, TCO) with a comparison chart if multiple scenarios
2. **Detail sheets** — one per domain or breakdown (Annual CAPEX, Annual OPEX, etc.)
3. **Charts on the same sheet as their data** — place charts below or beside the data table they reference

## Chart type guidance

Match the chart type to the data shape:

- **Bar charts** (`BarChart`) — comparisons across categories or scenarios
- **Stacked bar charts** (`BarChart` with `grouping="stacked"`) — composition/breakdown within categories
- **Line charts** (`LineChart`) — trends over time (annual costs, cumulative spend)
- **Pie charts** (`PieChart`) — proportional breakdown of a single total (use sparingly)

Use `openpyxl.chart` classes (`BarChart`, `LineChart`, `PieChart`, `Reference`). Build chart data from cell references so charts stay linked to the data.

## Formatting conventions

- **Headers**: Bold white text on dark blue fill (`#2F5496`)
- **Section headers**: Bold on light green fill (`#E2EFDA`)
- **Currency**: `#,##0` number format (no decimals for large values)
- **Percentages**: `0.0%` number format
- **Column widths**: Auto-size based on content
- **Chart sizing**: `width=22, height=14` for standard charts; increase for charts with many categories
- **Chart axis formatting**: Use `'$#,##0,,"M"'` for large dollar amounts to show in millions

## FILE: protocol

The script **must** emit `FILE:<path>` on stderr for the generated `.xlsx` file. After running the script, follow `file-handling.md` as usual.

```python
print(f"FILE:{output_path}", file=sys.stderr)
```

## Example snippet

```python
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
ws = wb.active
ws.title = "Summary"

# Write data to cells, then create a chart referencing those cells
chart = BarChart()
chart.title = "CAPEX vs OPEX"
chart.y_axis.numFmt = '$#,##0,,"M"'
cats = Reference(ws, min_col=1, min_row=2, max_row=4)
data = Reference(ws, min_col=2, max_col=3, min_row=1, max_row=4)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
ws.add_chart(chart, "A7")
```
