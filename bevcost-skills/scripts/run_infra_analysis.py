#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "pandas>=2.0.3",
#   "matplotlib>=3.7.2",
#   "numpy>=1.24.3",
#   "numpy_financial>=1.0.0",
# ]
# ///
"""Run an infrastructure TCO analysis using bevcost.

Override format (stdin):
{
  "infra_index": 0,              // which infrastructure from analysis.json (default: 0)
  "analysis": { ... },           // overrides for analysis config
  "infrastructure": { ... },     // overrides for selected infrastructure params
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

    if 'analysis' in overrides:
        analysis_data['analysis'] = deep_merge(analysis_data['analysis'], overrides['analysis'])

    infra_index = overrides.get('infra_index', 0)
    if 'infrastructure' in overrides:
        analysis_data['infrastructure'][infra_index] = deep_merge(
            analysis_data['infrastructure'][infra_index], overrides['infrastructure']
        )

    generate_charts = overrides.get('generate_charts', False)

    capex_dates = analysis_data['analysis']['CAPEX']
    opex_dates = analysis_data['analysis']['OPEX']
    infra_params = analysis_data['infrastructure'][infra_index]

    infrastructure_data = equipment_data['infrastructure']
    facility_params = infrastructure_data[0]

    evse_dict = tco.list_to_dict(equipment_data['support equipment'], 'model')
    evse_params = [evse_dict[model] for model in infra_params['evse']]

    infra = tco.InfraCell(
        infra_params, facility_params, evse_params,
        capex_dates=capex_dates, opex_dates=opex_dates,
        location=infra_params.get('location')
    )
    infra.execute_analysis()

    results = {
        'summary': {
            'location': infra.location,
            'info': infra.info,
            'infrastructure_type': infra_params.get('infrastructure type'),
            'evse_models': list(infra_params.get('evse', {}).keys()),
        },
        'capex_timeline': df_to_serializable(infra.capex_timeline),
        'opex_timeline': df_to_serializable(infra.opex_timeline),
        'equipment_costs': df_to_serializable(getattr(infra, 'equipment_costs', None)),
        'construction_costs': df_to_serializable(getattr(infra, 'construction_costs', None)),
        'baas_costs': df_to_serializable(getattr(infra, 'baas_costs', None)),
        'capex_variables': {k: df_to_serializable(v) if isinstance(v, pd.DataFrame) else v
                           for k, v in infra.capex_variables.items()},
        'opex_variables': {k: df_to_serializable(v) if isinstance(v, pd.DataFrame) else v
                          for k, v in infra.opex_variables.items()},
    }

    # Annual summary
    opex_objects, opex_vars, capex_objects, capex_vars = tco.annual_cashflow_summary(
        infra_objects=[infra]
    )
    annual_opex = {}
    for name, costs in opex_objects.items():
        annual_opex[name] = {k: df_to_serializable(v) for k, v in costs.items()}
    annual_capex = {}
    for name, costs in capex_objects.items():
        annual_capex[name] = {k: df_to_serializable(v) for k, v in costs.items()}

    results['annual_opex'] = annual_opex
    results['annual_capex'] = annual_capex

    if generate_charts:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        chart_dir = tempfile.mkdtemp(prefix='bevcost_charts_')

        fig, ax = plt.subplots(figsize=(10, 6))
        for name, costs in capex_objects.items():
            series_list = []
            for cost_name, cost_series in costs.items():
                series_list.append(pd.Series(
                    data=cost_series.values, index=cost_series.index, name=cost_name
                ))
            if series_list:
                years = [idx.year for idx in series_list[0].index]
                tco.stacked_bar_chart(ax, {'x': years, 'cost labels': None, 'data': series_list}, x_label='Year')
                ax.set_title(f'Infrastructure CAPEX — {name}', fontweight='bold')
        chart_path = os.path.join(chart_dir, 'infra_capex_breakdown.png')
        fig.tight_layout()
        fig.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f'FILE:{chart_path}', file=sys.stderr)

    json.dump(results, sys.stdout, default=str)


if __name__ == '__main__':
    main()
