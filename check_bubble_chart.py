"""Run with the course uv environment: uv run python homework-draft/check_bubble_chart.py APP_REPO.

Checks actual backend code and extracts pure UI formatters without starting Streamlit.
This is an AI-authored check; it does not establish browser rendering or raw-source accuracy.
"""
import ast
from decimal import Decimal
from pathlib import Path
import sys

import pandas as pd

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
from analysis import backend

tree = ast.parse((root / 'app.py').read_text())
functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
             and n.name in {'missing', 'percentage', 'growth'}]
namespace = {'pd': pd}
exec(compile(ast.Module(body=functions, type_ignores=[]), 'app.py', 'exec'), namespace)

occupations, _ = backend.load_clean_data(root / 'data/cleaned')
chart = backend.comparison_data(occupations)
for row in chart.itertuples():
    expected = float(Decimal(str(row.observed_exposure)) * Decimal('100'))
    assert abs(row.observed_exposure_percent - expected) < 1e-10
    assert namespace['percentage'](row.observed_exposure) == f'{expected:.2f}%'
print(f'PASS: percentage scaling and tooltip formatting for {len(chart)} occupations; '
      f'{len(occupations) - len(chart)} omitted.')

base = occupations.iloc[[0]].copy()
base['observed_exposure'] = 0.25
base['employment_change_percent_2025_35'] = -7.3
base['median_annual_wage_2025'] = float('nan')
result = backend.comparison_data(base)
assert len(result) == 1
assert result.iloc[0].observed_exposure_percent == 25
assert result.iloc[0].employment_change_percent_2025_35 == -7.3
assert namespace['percentage'](0.25) == '25.00%'
assert namespace['growth'](-7.3) == '-7.3%'
print('PASS: synthetic exposure 0.25 -> 25.00%; growth -7.3 -> -7.3%; missing wage retained.')
for column, value in [('observed_exposure', float('nan')),
                      ('employment_change_percent_2025_35', float('nan')),
                      ('employment_2025', float('nan')),
                      ('employment_2025', 0), ('employment_2025', -1)]:
    sample = base.copy()
    sample[column] = value
    assert backend.comparison_data(sample).empty
assert backend.comparison_data(base.iloc[:0]).empty
print('PASS: missing chart inputs, zero/negative employment excluded; empty input handled.')

programmer = chart.loc[chart.soc_code.eq('15-1251')].iloc[0]
print(f'Computer Programmers: exposure={programmer.observed_exposure}; '
      f'y={programmer.observed_exposure_percent}; '
      f'tooltip={namespace["percentage"](programmer.observed_exposure)}; '
      f'x={programmer.employment_change_percent_2025_35}; '
      f'employment={programmer.employment_2025}')
print('LIMIT: no browser or Plotly rendering check; bubble area and hover rendering need live review.')
