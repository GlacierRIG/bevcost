#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "pandas>=2.0.3",
#   "matplotlib>=3.7.2",
#   "numpy>=1.24.3",
#   "numpy_financial>=1.0.0",
# ]
# ///
"""Generate TCO charts from analysis results.

Runs the full TCO analysis (same as run_full_tco.py) and produces
specific chart types based on the request.

Input format (stdin):
{
  "overrides": { ... },          // same as run_full_tco.py overrides
  "charts": ["opex_breakdown", "capex_breakdown", "opex_trends", "energy", "maintenance"]
}

Available chart types:
  - "opex_breakdown": Stacked bar of annual OPEX by cost category
  - "capex_breakdown": Stacked bar of annual CAPEX by cost category
  - "opex_trends": Spaghetti line plot of OPEX categories over time
  - "energy": Bar chart of annual energy consumption
  - "maintenance": Bar chart of annual maintenance costs
"""
import json
import os
import sys
import tempfile
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_SCRIPT_DIR, '..', 'lib'))
sys.path.insert(0, _SCRIPT_DIR)
import bevcost.TCOmodel as tco
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from _shared import deep_merge


def run_full_analysis(plugin_root, overrides):
    """Run the complete TCO analysis and return objects."""
    with open(os.path.join(plugin_root, 'data', 'data.json'), 'r') as f:
        equipment_data = json.load(f)
    with open(os.path.join(plugin_root, 'data', 'analysis.json'), 'r') as f:
        analysis_data = json.load(f)

    if 'business' in overrides:
        analysis_data['business'] = deep_merge(analysis_data['business'], overrides['business'])
    if 'analysis' in overrides:
        analysis_data['analysis'] = deep_merge(analysis_data['analysis'], overrides['analysis'])

    capex_dates = analysis_data['analysis']['CAPEX']
    opex_dates = analysis_data['analysis']['OPEX']
    business_params = analysis_data['business']

    LHD_dict = tco.list_to_dict(equipment_data['vehicles'], 'model')
    evse_dict = tco.list_to_dict(equipment_data['support equipment'], 'model')

    fleet_stock = []
    fleet_overrides = overrides.get('fleet_overrides', [])
    for i, fleet_params in enumerate(analysis_data['fleet']):
        if i < len(fleet_overrides) and fleet_overrides[i]:
            fleet_params = deep_merge(fleet_params, fleet_overrides[i])
        fleet_op_hours = pd.DataFrame(
            data=fleet_params['fleet operating hours'][1:],
            columns=fleet_params['fleet operating hours'][0]
        )
        fleet_op_hours['date'] = pd.to_datetime(fleet_op_hours['date'])
        vehicles_params = LHD_dict[fleet_params['model']]
        evse_params = evse_dict[vehicles_params['evse model']]
        fleet = tco.FleetCell(
            fleet_params, vehicles_params, evse_params, business_params,
            fleet_op_hours, capex_dates=capex_dates, opex_dates=opex_dates,
            location=fleet_params.get('location')
        )
        fleet.execute_analysis()
        fleet_stock.append(fleet)

    infrastructure_data = equipment_data['infrastructure']
    facility_params = infrastructure_data[0]
    infra_stock = []
    infra_overrides_list = overrides.get('infra_overrides', [])
    for i, infra_params in enumerate(analysis_data['infrastructure']):
        if i < len(infra_overrides_list) and infra_overrides_list[i]:
            infra_params = deep_merge(infra_params, infra_overrides_list[i])
        evse_params_list = [evse_dict[model] for model in infra_params['evse']]
        infra = tco.InfraCell(
            infra_params, facility_params, evse_params_list,
            capex_dates=capex_dates, opex_dates=opex_dates,
            location=infra_params.get('location')
        )
        infra.execute_analysis()
        infra_stock.append(infra)

    digital_solutions_data = equipment_data['digital solutions']
    solutions_params = digital_solutions_data[0]
    digital_stock = []
    digital_overrides_list = overrides.get('digital_overrides', [])
    for i, solutions_data in enumerate(analysis_data['digital solutions']):
        if i < len(digital_overrides_list) and digital_overrides_list[i]:
            solutions_data = deep_merge(solutions_data, digital_overrides_list[i])
        digital = tco.DigitalSolutionsCell(
            solutions_data, solutions_params,
            capex_dates=capex_dates, opex_dates=opex_dates,
            location=solutions_data.get('location')
        )
        digital.execute_analysis()
        digital_stock.append(digital)

    workforce_pool = []
    workforce_overrides_list = overrides.get('workforce_overrides', [])
    for i, workforce_params in enumerate(analysis_data['workforce']):
        if i < len(workforce_overrides_list) and workforce_overrides_list[i]:
            workforce_params = deep_merge(workforce_params, workforce_overrides_list[i])
        workforce = tco.WorkforceCell(
            workforce_params, business_params,
            opex_dates=opex_dates, location=workforce_params.get('location')
        )
        workforce.execute_analysis()
        workforce_pool.append(workforce)

    return fleet_stock, infra_stock, digital_stock, workforce_pool


def main():
    plugin_root = os.path.join(_SCRIPT_DIR, '..')

    config = {}
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if raw:
            try:
                config = json.loads(raw)
            except json.JSONDecodeError as e:
                json.dump({'error': f'Invalid JSON input: {e}'}, sys.stdout)
                sys.exit(1)

    analysis_overrides = config.get('overrides', {})
    requested_charts = config.get('charts', ['opex_breakdown', 'capex_breakdown'])

    fleet_stock, infra_stock, digital_stock, workforce_pool = run_full_analysis(
        plugin_root, analysis_overrides
    )

    opex_objects, opex_vars, capex_objects, capex_vars = tco.annual_cashflow_summary(
        fleet_objects=fleet_stock, infra_objects=infra_stock,
        labour_objects=workforce_pool, digital_solution_objects=digital_stock
    )

    chart_dir = tempfile.mkdtemp(prefix='bevcost_charts_')
    chart_paths = []

    if 'opex_breakdown' in requested_charts:
        fig, ax = plt.subplots(figsize=(12, 6))
        opex_by_domain = {}
        for name, costs in opex_objects.items():
            total = pd.DataFrame(costs).sum(axis=1)
            opex_by_domain[name] = total
        if opex_by_domain:
            opex_df = pd.DataFrame(opex_by_domain)
            years = [idx.year for idx in opex_df.index]
            series_list = [pd.Series(data=opex_df[col].values, name=col) for col in opex_df.columns]
            tco.stacked_bar_chart(ax, {'x': years, 'cost labels': None, 'data': series_list}, x_label='Year')
            ax.set_title('Annual OPEX Breakdown by Domain', fontweight='bold')
        path = os.path.join(chart_dir, 'opex_breakdown.png')
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        chart_paths.append(path)
        print(f'FILE:{path}', file=sys.stderr)

    if 'capex_breakdown' in requested_charts:
        fig, ax = plt.subplots(figsize=(12, 6))
        capex_by_domain = {}
        for name, costs in capex_objects.items():
            total = pd.DataFrame(costs).sum(axis=1)
            capex_by_domain[name] = total
        if capex_by_domain:
            capex_df = pd.DataFrame(capex_by_domain)
            years = [idx.year for idx in capex_df.index]
            series_list = [pd.Series(data=capex_df[col].values, name=col) for col in capex_df.columns]
            tco.stacked_bar_chart(ax, {'x': years, 'cost labels': None, 'data': series_list}, x_label='Year')
            ax.set_title('Annual CAPEX Breakdown by Domain', fontweight='bold')
        path = os.path.join(chart_dir, 'capex_breakdown.png')
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        chart_paths.append(path)
        print(f'FILE:{path}', file=sys.stderr)

    if 'opex_trends' in requested_charts and opex_objects:
        # Spaghetti line plot of OPEX categories
        all_costs = {}
        for name, costs in opex_objects.items():
            for cost_name, cost_series in costs.items():
                label = f'{name} — {cost_name}'
                all_costs[label] = cost_series

        if all_costs:
            cost_df = pd.DataFrame(all_costs)
            cost_df.insert(0, 'x', [idx.year for idx in cost_df.index])
            n_cols = len(cost_df.columns) - 1  # minus 'x'
            n_rows = int(np.ceil(n_cols / 3))
            fig, axes = plt.subplots(n_rows, 3, figsize=(16, 4 * n_rows))
            palette = plt.get_cmap('Dark2')
            tco.spaghetti_line_plots(axes, 'OPEX Cost Trends', cost_df, palette)
            fig.suptitle('OPEX Cost Trends', fontsize=16, fontweight='bold', y=0.98)
            fig.tight_layout(rect=[0, 0.03, 1, 0.95])
            path = os.path.join(chart_dir, 'opex_trends.png')
            fig.savefig(path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            chart_paths.append(path)
            print(f'FILE:{path}', file=sys.stderr)

    if 'energy' in requested_charts and fleet_stock:
        fig, ax = plt.subplots(figsize=(10, 6))
        for fleet in fleet_stock:
            annual_energy = fleet.energy_consumed.set_index('date').resample('YE').sum()
            years = [idx.year for idx in annual_energy.index]
            ax.bar(years, annual_energy.values.flatten(), alpha=0.7, label=f'{fleet.info} {fleet.location}')
        ax.set_title('Annual Energy Consumption (kWh)', fontweight='bold')
        ax.set_xlabel('Year')
        ax.legend()
        path = os.path.join(chart_dir, 'energy_consumption.png')
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        chart_paths.append(path)
        print(f'FILE:{path}', file=sys.stderr)

    if 'maintenance' in requested_charts and fleet_stock:
        fig, ax = plt.subplots(figsize=(10, 6))
        n_fleets = len(fleet_stock)
        bar_width = 0.8 / n_fleets
        for i, fleet in enumerate(fleet_stock):
            mc = fleet.maintenance_costs.copy()
            mc['date'] = pd.to_datetime(mc['date'])
            mc = mc.set_index('date')
            annual_maint = mc.resample('YE').sum()
            total_maint = annual_maint.sum(axis=1)
            years = np.array([idx.year for idx in total_maint.index])
            offset = (i - (n_fleets - 1) / 2) * bar_width
            ax.bar(years + offset, total_maint.values, width=bar_width, alpha=0.7, label=f'{fleet.info} {fleet.location}')
        ax.set_title('Annual Maintenance Costs ($)', fontweight='bold')
        ax.set_xlabel('Year')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax.legend()
        path = os.path.join(chart_dir, 'maintenance_costs.png')
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        chart_paths.append(path)
        print(f'FILE:{path}', file=sys.stderr)

    json.dump({'charts_generated': chart_paths}, sys.stdout)


if __name__ == '__main__':
    main()
