#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "pandas>=2.0.3",
#   "matplotlib>=3.7.2",
#   "numpy>=1.24.3",
#   "numpy_financial>=1.0.0",
# ]
# ///
"""Run a complete TCO analysis across all cost domains using bevcost.

Mirrors the tco_example.py workflow: creates FleetCells, InfraCells,
DigitalSolutionsCells, and WorkforceCells, then aggregates with
annual_cashflow_summary().

Override format (stdin):
{
  "analysis": { ... },
  "business": { ... },
  "fleet_overrides": [{ ... }, ...],      // list of override dicts per fleet (by index)
  "infra_overrides": [{ ... }, ...],      // list of override dicts per infra (by index)
  "digital_overrides": [{ ... }, ...],    // list of override dicts per digital solution
  "workforce_overrides": [{ ... }, ...],  // list of override dicts per workforce group
  "generate_charts": false
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
    plugin_root = os.path.join(_SCRIPT_DIR, '..')
    with open(os.path.join(plugin_root, 'data', 'data.json'), 'r') as f:
        equipment_data = json.load(f)
    with open(os.path.join(plugin_root, 'data', 'analysis.json'), 'r') as f:
        analysis_data = json.load(f)

    overrides = {}
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if raw:
            try:
                overrides = json.loads(raw)
            except json.JSONDecodeError as e:
                json.dump({'error': f'Invalid JSON input: {e}'}, sys.stdout)
                sys.exit(1)

    if 'business' in overrides:
        analysis_data['business'] = deep_merge(analysis_data['business'], overrides['business'])
    if 'analysis' in overrides:
        analysis_data['analysis'] = deep_merge(analysis_data['analysis'], overrides['analysis'])

    generate_charts = overrides.get('generate_charts', False)
    capex_dates = analysis_data['analysis']['CAPEX']
    opex_dates = analysis_data['analysis']['OPEX']
    business_params = analysis_data['business']

    # --- Fleet analysis ---
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

    # --- Infrastructure analysis ---
    infrastructure_data = equipment_data['infrastructure']
    facility_params = infrastructure_data[0]

    infra_stock = []
    infra_overrides = overrides.get('infra_overrides', [])

    for i, infra_params in enumerate(analysis_data['infrastructure']):
        if i < len(infra_overrides) and infra_overrides[i]:
            infra_params = deep_merge(infra_params, infra_overrides[i])

        evse_params_list = [evse_dict[model] for model in infra_params['evse']]

        infra = tco.InfraCell(
            infra_params, facility_params, evse_params_list,
            capex_dates=capex_dates, opex_dates=opex_dates,
            location=infra_params.get('location')
        )
        infra.execute_analysis()
        infra_stock.append(infra)

    # --- Digital solutions analysis ---
    digital_solutions_data = equipment_data['digital solutions']
    solutions_params = digital_solutions_data[0]

    digital_stock = []
    digital_overrides = overrides.get('digital_overrides', [])

    for i, solutions_data in enumerate(analysis_data['digital solutions']):
        if i < len(digital_overrides) and digital_overrides[i]:
            solutions_data = deep_merge(solutions_data, digital_overrides[i])

        digital = tco.DigitalSolutionsCell(
            solutions_data, solutions_params,
            capex_dates=capex_dates, opex_dates=opex_dates,
            location=solutions_data.get('location')
        )
        digital.execute_analysis()
        digital_stock.append(digital)

    # --- Workforce analysis ---
    workforce_pool = []
    workforce_overrides = overrides.get('workforce_overrides', [])

    for i, workforce_params in enumerate(analysis_data['workforce']):
        if i < len(workforce_overrides) and workforce_overrides[i]:
            workforce_params = deep_merge(workforce_params, workforce_overrides[i])

        workforce = tco.WorkforceCell(
            workforce_params, business_params,
            opex_dates=opex_dates,
            location=workforce_params.get('location')
        )
        workforce.execute_analysis()
        workforce_pool.append(workforce)

    # --- Aggregate results ---
    opex_objects, opex_vars, capex_objects, capex_vars = tco.annual_cashflow_summary(
        fleet_objects=fleet_stock,
        infra_objects=infra_stock,
        labour_objects=workforce_pool,
        digital_solution_objects=digital_stock
    )

    # Build serializable results
    results = {
        'summary': {
            'project_name': analysis_data['analysis']['project name'],
            'capex_period': capex_dates,
            'opex_period': opex_dates,
            'fleet_count': len(fleet_stock),
            'infra_count': len(infra_stock),
            'digital_count': len(digital_stock),
            'workforce_count': len(workforce_pool),
        },
        'annual_opex': {},
        'annual_capex': {},
    }

    for name, costs in opex_objects.items():
        results['annual_opex'][name] = {k: df_to_serializable(v) for k, v in costs.items()}
    for name, costs in capex_objects.items():
        results['annual_capex'][name] = {k: df_to_serializable(v) for k, v in costs.items()}

    # Compute grand totals
    all_opex = pd.concat(
        [pd.DataFrame(costs) for costs in opex_objects.values()],
        axis=1
    )
    all_opex['total_opex'] = all_opex.sum(axis=1)
    results['total_annual_opex'] = df_to_serializable(all_opex[['total_opex']])

    all_capex = pd.concat(
        [pd.DataFrame(costs) for costs in capex_objects.values()],
        axis=1
    )
    all_capex['total_capex'] = all_capex.sum(axis=1)
    results['total_annual_capex'] = df_to_serializable(all_capex[['total_capex']])

    if generate_charts:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        chart_dir = tempfile.mkdtemp(prefix='bevcost_charts_')

        # Grand total OPEX + CAPEX stacked bar
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # OPEX by domain
        opex_by_domain = {}
        for name, costs in opex_objects.items():
            total = pd.DataFrame(costs).sum(axis=1)
            opex_by_domain[name] = total

        if opex_by_domain:
            opex_df = pd.DataFrame(opex_by_domain)
            years = [idx.year for idx in opex_df.index]
            series_list = [pd.Series(data=opex_df[col].values, name=col) for col in opex_df.columns]
            tco.stacked_bar_chart(ax1, {'x': years, 'cost labels': None, 'data': series_list}, x_label='Year')
            ax1.set_title('Annual OPEX by Domain', fontweight='bold')

        # CAPEX by domain
        capex_by_domain = {}
        for name, costs in capex_objects.items():
            total = pd.DataFrame(costs).sum(axis=1)
            capex_by_domain[name] = total

        if capex_by_domain:
            capex_df = pd.DataFrame(capex_by_domain)
            years = [idx.year for idx in capex_df.index]
            series_list = [pd.Series(data=capex_df[col].values, name=col) for col in capex_df.columns]
            tco.stacked_bar_chart(ax2, {'x': years, 'cost labels': None, 'data': series_list}, x_label='Year')
            ax2.set_title('Annual CAPEX by Domain', fontweight='bold')

        chart_path = os.path.join(chart_dir, 'full_tco_overview.png')
        fig.tight_layout()
        fig.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f'CHART:{chart_path}', file=sys.stderr)

    json.dump(results, sys.stdout, default=str)


if __name__ == '__main__':
    main()
