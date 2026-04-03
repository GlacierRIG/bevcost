#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "pandas>=2.0.3",
#   "matplotlib>=3.7.2",
#   "numpy>=1.24.3",
#   "numpy_financial>=1.0.0",
# ]
# ///
"""Run multiple TCO scenarios and compare results.

Input format (stdin):
{
  "scenarios": [
    {
      "name": "Baseline",
      "overrides": {}              // same format as run_full_tco.py overrides
    },
    {
      "name": "More vehicles",
      "overrides": {
        "fleet_overrides": [{"vehicles": 8}]
      }
    }
  ],
  "generate_charts": false
}
"""
import json
import os
import sys
import subprocess
import tempfile

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_SCRIPT_DIR, '..', 'lib'))


def main():
    plugin_root = os.path.join(_SCRIPT_DIR, '..')
    full_tco_script = os.path.join(_SCRIPT_DIR, 'run_full_tco.py')

    config = {}
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if raw:
            try:
                config = json.loads(raw)
            except json.JSONDecodeError as e:
                json.dump({'error': f'Invalid JSON input: {e}'}, sys.stdout)
                sys.exit(1)

    scenarios = config.get('scenarios', [
        {'name': 'Default', 'overrides': {}}
    ])
    generate_charts = config.get('generate_charts', False)

    results = []

    for scenario in scenarios:
        name = scenario['name']
        overrides = scenario.get('overrides', {})

        # Run the full TCO script as a subprocess
        proc = subprocess.run(
            ['uv', 'run', full_tco_script],
            input=json.dumps(overrides),
            capture_output=True,
            text=True,
            cwd=plugin_root
        )

        if proc.returncode != 0:
            results.append({
                'name': name,
                'error': proc.stderr
            })
            continue

        try:
            tco_result = json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            results.append({
                'name': name,
                'error': f'Invalid JSON output from subprocess: {e}'
            })
            continue

        # Extract summary metrics
        total_opex_data = tco_result.get('total_annual_opex', {})
        total_capex_data = tco_result.get('total_annual_capex', {})

        total_opex = sum(total_opex_data.get('total_opex', [0]))
        total_capex = sum(total_capex_data.get('total_capex', [0]))

        results.append({
            'name': name,
            'total_opex': total_opex,
            'total_capex': total_capex,
            'total_tco': total_opex + total_capex,
            'annual_opex': tco_result.get('annual_opex'),
            'annual_capex': tco_result.get('annual_capex'),
            'summary': tco_result.get('summary'),
        })

    # Build comparison table
    comparison = {
        'scenarios': results,
        'comparison_table': {
            'names': [r['name'] for r in results if 'error' not in r],
            'total_capex': [r['total_capex'] for r in results if 'error' not in r],
            'total_opex': [r['total_opex'] for r in results if 'error' not in r],
            'total_tco': [r['total_tco'] for r in results if 'error' not in r],
        }
    }

    if generate_charts and len([r for r in results if 'error' not in r]) >= 2:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np

        chart_dir = tempfile.mkdtemp(prefix='bevcost_charts_')
        valid = [r for r in results if 'error' not in r]

        fig, ax = plt.subplots(figsize=(10, 6))
        names = [r['name'] for r in valid]
        capex_vals = [r['total_capex'] for r in valid]
        opex_vals = [r['total_opex'] for r in valid]
        x = np.arange(len(names))
        width = 0.35

        ax.bar(x - width/2, capex_vals, width, label='Total CAPEX', color='#2196F3')
        ax.bar(x + width/2, opex_vals, width, label='Total OPEX', color='#FF9800')
        ax.set_xticks(x)
        ax.set_xticklabels(names)
        ax.set_title('Scenario Comparison: CAPEX vs OPEX', fontweight='bold')
        ax.legend()
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

        chart_path = os.path.join(chart_dir, 'scenario_comparison.png')
        fig.tight_layout()
        fig.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f'FILE:{chart_path}', file=sys.stderr)

    json.dump(comparison, sys.stdout, default=str)


if __name__ == '__main__':
    main()
