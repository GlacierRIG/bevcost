#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "pandas>=2.0.3",
#   "matplotlib>=3.7.2",
#   "numpy>=1.24.3",
#   "numpy_financial>=1.0.0",
# ]
# ///
"""Run a fleet TCO analysis using bevcost.

Reads bundled default data, applies JSON overrides from stdin,
and outputs structured results as JSON to stdout.

Override format (stdin):
{
  "fleet_index": 0,              // which fleet from analysis.json to analyze (default: 0)
  "analysis": { ... },           // overrides for analysis config
  "business": { ... },           // overrides for business params
  "fleet": { ... },              // overrides for fleet params (merged into selected fleet)
  "vehicles": { ... },           // overrides for vehicle params
  "generate_charts": false       // whether to generate chart PNGs
}
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

from _shared import deep_merge, df_to_serializable


def main():
    # Locate bundled data files
    plugin_root = os.path.join(_SCRIPT_DIR, '..')
    data_path = os.path.join(plugin_root, 'data', 'data.json')
    analysis_path = os.path.join(plugin_root, 'data', 'analysis.json')

    with open(data_path, 'r') as f:
        equipment_data = json.load(f)
    with open(analysis_path, 'r') as f:
        analysis_data = json.load(f)

    # Read overrides from stdin (if any)
    overrides = {}
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if raw:
            try:
                overrides = json.loads(raw)
            except json.JSONDecodeError as e:
                json.dump({'error': f'Invalid JSON input: {e}'}, sys.stdout)
                sys.exit(1)

    # Apply overrides
    if 'business' in overrides:
        analysis_data['business'] = deep_merge(analysis_data['business'], overrides['business'])
    if 'analysis' in overrides:
        analysis_data['analysis'] = deep_merge(analysis_data['analysis'], overrides['analysis'])

    fleet_index = overrides.get('fleet_index', 0)
    if 'fleet' in overrides:
        analysis_data['fleet'][fleet_index] = deep_merge(
            analysis_data['fleet'][fleet_index], overrides['fleet']
        )

    generate_charts = overrides.get('generate_charts', False)

    # Set up parameters
    capex_dates = analysis_data['analysis']['CAPEX']
    opex_dates = analysis_data['analysis']['OPEX']
    business_params = analysis_data['business']

    fleet_params = analysis_data['fleet'][fleet_index]

    # Build vehicle and EVSE lookups
    LHD_dict = tco.list_to_dict(equipment_data['vehicles'], 'model')
    evse_dict = tco.list_to_dict(equipment_data['support equipment'], 'model')

    if 'vehicles' in overrides:
        vehicle_model = fleet_params['model']
        LHD_dict[vehicle_model] = deep_merge(LHD_dict[vehicle_model], overrides['vehicles'])

    vehicles_params = LHD_dict[fleet_params['model']]
    evse_params = evse_dict[vehicles_params['evse model']]

    # Build operating hours DataFrame
    fleet_op_hours = pd.DataFrame(
        data=fleet_params['fleet operating hours'][1:],
        columns=fleet_params['fleet operating hours'][0]
    )
    fleet_op_hours['date'] = pd.to_datetime(fleet_op_hours['date'])

    # Create and run fleet analysis
    fleet = tco.FleetCell(
        fleet_params, vehicles_params, evse_params, business_params,
        fleet_op_hours,
        capex_dates=capex_dates, opex_dates=opex_dates,
        location=fleet_params.get('location')
    )
    fleet.execute_analysis()

    # Build results
    results = {
        'summary': {
            'location': fleet.location,
            'info': fleet.info,
            'vehicle_model': fleet_params['model'],
            'vehicle_count': fleet_params['vehicles'],
            'battery_count': fleet_params['batteries'],
        },
        'capex_timeline': df_to_serializable(fleet.capex_timeline),
        'opex_timeline': df_to_serializable(fleet.opex_timeline),
        'energy_consumed': df_to_serializable(fleet.energy_consumed),
        'energy_costs': df_to_serializable(fleet.energy_costs),
        'power_consumed': df_to_serializable(getattr(fleet, 'power_consumed', None)),
        'power_costs': df_to_serializable(getattr(fleet, 'power_costs', None)),
        'maintenance_costs': df_to_serializable(fleet.maintenance_costs),
        'baas_costs': df_to_serializable(fleet.baas_costs),
        'GHG_emissions': df_to_serializable(fleet.GHG_emissions),
        'fleet_costs': df_to_serializable(fleet.fleet_costs),
        'opex_subsidies': df_to_serializable(getattr(fleet, 'opex_subsidies', None)),
        'capex_variables': {k: df_to_serializable(v) if isinstance(v, pd.DataFrame) else v
                           for k, v in fleet.capex_variables.items()},
        'opex_variables': {k: df_to_serializable(v) if isinstance(v, pd.DataFrame) else v
                           for k, v in fleet.opex_variables.items()},
    }

    # Compute annual totals
    opex_objects, opex_vars, capex_objects, capex_vars = tco.annual_cashflow_summary(
        fleet_objects=[fleet]
    )
    annual_opex = {}
    for name, costs in opex_objects.items():
        annual_opex[name] = {k: df_to_serializable(v) for k, v in costs.items()}
    annual_capex = {}
    for name, costs in capex_objects.items():
        annual_capex[name] = {k: df_to_serializable(v) for k, v in costs.items()}

    results['annual_opex'] = annual_opex
    results['annual_capex'] = annual_capex

    # Generate charts if requested
    if generate_charts:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        chart_dir = tempfile.mkdtemp(prefix='bevcost_charts_')

        # Stacked bar chart of annual OPEX breakdown (one per entry)
        for entry_name, costs in opex_objects.items():
            fig, ax = plt.subplots(figsize=(10, 6))
            series_list = []
            for cost_name, cost_series in costs.items():
                series_list.append(pd.Series(
                    data=cost_series.values,
                    index=cost_series.index,
                    name=cost_name
                ))
            if series_list:
                years = [idx.year for idx in series_list[0].index]
                data_dict = {
                    'x': years,
                    'cost labels': None,
                    'data': series_list
                }
                tco.stacked_bar_chart(ax, data_dict, x_label='Year')
                ax.set_title(f'Annual OPEX Breakdown — {entry_name}', fontweight='bold')
            safe_name = entry_name.replace(' ', '_').replace('/', '_')
            chart_path = os.path.join(chart_dir, f'fleet_opex_breakdown_{safe_name}.png')
            fig.tight_layout()
            fig.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            print(f'FILE:{chart_path}', file=sys.stderr)

        # Stacked bar chart of annual CAPEX breakdown (one per entry)
        for entry_name, costs in capex_objects.items():
            fig, ax = plt.subplots(figsize=(10, 6))
            series_list = []
            for cost_name, cost_series in costs.items():
                series_list.append(pd.Series(
                    data=cost_series.values,
                    index=cost_series.index,
                    name=cost_name
                ))
            if series_list:
                years = [idx.year for idx in series_list[0].index]
                data_dict = {
                    'x': years,
                    'cost labels': None,
                    'data': series_list
                }
                tco.stacked_bar_chart(ax, data_dict, x_label='Year')
                ax.set_title(f'Annual CAPEX Breakdown — {entry_name}', fontweight='bold')
            safe_name = entry_name.replace(' ', '_').replace('/', '_')
            chart_path = os.path.join(chart_dir, f'fleet_capex_breakdown_{safe_name}.png')
            fig.tight_layout()
            fig.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            print(f'FILE:{chart_path}', file=sys.stderr)

    json.dump(results, sys.stdout, default=str)


if __name__ == '__main__':
    main()
