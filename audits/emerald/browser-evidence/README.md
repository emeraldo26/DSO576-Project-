# Emerald's bubble-chart audit evidence

Audited app commit: `7485591666afe70acf5c0c7f9eeed6d6e5e16e74`.

Codex performed the automated source, numerical, and local browser checks and drafted the findings with Emerald. This folder contains shared evidence, not the individual Gradescope submission.

- `results.json`: completed chart checks; axis and hover values, 755 SVG bubble radii, exposure filtering, sort-color invariance, and an empty-result state.
- `reset-results.json`: fresh-session reproduction of B2-01. Chart counts are 11 before reset, 755 immediately afterward with the old bound still checked, and 11 again after sorting.
- PNG files: screenshots captured during those runs.

## Reproduce

Install the project's `requirements.txt` and Playwright in an isolated Python environment. The recorded run used Python 3.12.2, Streamlit 1.66.1, Plotly 6.9.0, pandas 2.3.3, and Playwright 1.64.1. Browser scripts launch the installed macOS Google Chrome executable; adjust its path for your system.

From the project root, run the numeric check:

```sh
python audits/emerald/check_bubble_chart.py .
```

Start the unchanged app in another terminal:

```sh
python -m streamlit run app.py --server.headless true --server.port 8519 --browser.gatherUsageStats false
```

Then run:

```sh
python audits/emerald/check_browser.py
python audits/emerald/check_reset_browser.py
```

Scripts replace their corresponding evidence files on rerun. `check_browser.py` checks passing chart behavior; `check_reset_browser.py` records reset state without treating the documented defect as a passing fix verification.

These checks do not establish raw-source accuracy, every filter combination, mobile behavior, accessibility, or behavior on other dependency versions. No app implementation changes are included.
