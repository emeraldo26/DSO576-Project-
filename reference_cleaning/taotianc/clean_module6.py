"""Full-source Module 6 cleaning and audit; never writes to source files.

Scope: national occupation-screening prototype, with no priority score.
All reductions are derived views, separate from row-preserving clean tables.
Run instructions and snapshot requirements: code/README.md.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve()
EXPECTATIONS = SCRIPT.with_name('module6_record_expectations.json')
HASHES = {
    'bls_table_1_2_2025_35.csv': '460af8e1eaf961732bc29b56cc92b25c4d6ef85c587b8b566f834beaebededa2',
    'job_exposure.csv': '4f0a3adf5feeb2ec5f5d02ab18cc5e851a2a4b8470bde84c0c9335017be12d68',
    'onet_occupation_data.csv': 'a09eae1d6609686e44e05b7290993a1c8b523d8ca224bc0eedc194c855c3ee02',
    'onet_task_statements.csv': '4568e14d8db6f05551ad37e056e909b13ebae4a26bcb5ff915bb5f281d582c57',
    'task_penetration.csv': '85bee872db1d55d3e9a7f4e89da5ae4a5d59aa8ec875d728fbf4b7d820984616',
    'bls_occupation_tables_2025_35.xlsx': 'a7d060f0576f7d4f5b829b9a0bb4a6c11a12766d159ebb0e07aab5bd2e7583c5',
}
SIZES = {'jobs': 756, 'penetration': 17998, 'occupations': 1016, 'tasks': 18838, 'bls': 1112}
FILES = {'jobs': 'job_exposure.csv', 'penetration': 'task_penetration.csv',
         'occupations': 'onet_occupation_data.csv', 'tasks': 'onet_task_statements.csv',
         'bls': 'bls_table_1_2_2025_35.csv'}
BLS_HEADERS = ['2025 National Employment Matrix title', '2025 National Employment Matrix code',
    'Occupation type', 'Employment, 2025', 'Employment, 2035',
    'Employment distribution, percent, 2025', 'Employment distribution, percent, 2035',
    'Employment change, numeric, 2025–35', 'Employment change, percent, 2025–35',
    'Percent self-employed, 2025', 'Occupational openings, 2025–35 annual average',
    'Median annual wage, dollars, 2025', 'Typical education needed for entry',
    'Work experience in a related occupation',
    'Typical on-the-job training needed to attain competency in the occupation']
SCHEMAS = {'jobs': ['occ_code', 'title', 'observed_exposure'],
    'penetration': ['task', 'penetration'],
    'occupations': ['O*NET-SOC Code', 'Title', 'Description'],
    'tasks': ['O*NET-SOC Code', 'Title', 'Task ID', 'Task', 'Task Type',
              'Incumbents Responding', 'Date', 'Domain Source'], 'bls': BLS_HEADERS}
BLS_NUM = dict(zip(BLS_HEADERS[3:12], ['employment_2025_thousands',
    'employment_2035_thousands', 'employment_distribution_2025_percent',
    'employment_distribution_2035_percent', 'employment_change_thousands',
    'employment_change_percent', 'self_employed_percent', 'annual_openings_thousands',
    'median_annual_wage_dollars']))
LIMITATIONS = [
    'National occupation-screening prototype. California funding conclusions require California employment, projections, training costs/capacity and outcomes.',
    'No priority score, weights, or priority/coverage thresholds have been invented. Partial task coverage is reported as a factual boolean and ratio.',
    'Observed Claude use is not displacement, causal AI impact, or the prevalence of all workplace AI use.',
    'The exact Anthropic/O*NET release identifiers and original download dates were not supplied. SHA-256 fixes the inspected local snapshot; local filesystem dates are not provenance.',
    'BLS workbook labels its projection period 2025–35 and wage year 2025. Source file identity is pinned, but external download authenticity/release provenance has not been independently established.',
    'Conservative exact task matching leaves unmatched tasks. Missing penetration is unknown, not zero; matched-task averages may be biased.',
    'SOC base-code matches do not establish full classification-version equivalence. O*NET suffix detail is retained, but the description view uses the .00 base.',
    'BLS totals differ from sums of displayed line items because of rounding and excluded occupational data. Published percent changes are preserved.',
    'Wage medians cover a different population from total employment; medians cannot be added or averaged into a national median.',
    'Source task vintage spans 2006–2026. Structural task metadata blanks remain null with explicit reasons.',
    'No Gradescope PDF or notebook is produced by this pipeline. Branch publishing and the final submitted commit remain pending the user review.',
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(s: pd.Series) -> pd.Series:
    return s.str.lower().str.replace(r'\s+', ' ', regex=True).str.strip()


def scalar(v):
    if pd.isna(v):
        return ''
    if isinstance(v, float):
        return format(v, '.12f').rstrip('0').rstrip('.')
    return str(v)


def text_frame(path: Path) -> pd.DataFrame:
    # Read every identifier as text. Do not treat literal "None" as NA.
    return pd.read_csv(path, dtype='string', keep_default_na=False, na_filter=False)


class Audit:
    def __init__(self, out: Path):
        self.out = out
        self.checks = []
        self.flows = []
        self.exclusions = []
        self.conversions = []
        self.key_checks = []

    def table(self, name, rows, columns=None):
        frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows, columns=columns)
        frame.to_csv(self.out / name, index=False, encoding='utf-8', lineterminator='\n', float_format='%.12g')

    def check(self, name, condition, actual, expected):
        def compact(value):
            text = str(value)
            if len(text) > 500:
                return f'length={len(value)}; sha256={hashlib.sha256(text.encode()).hexdigest()}'
            return text
        self.checks.append({'check': name, 'actual': compact(actual), 'expected': compact(expected),
                            'status': 'PASS' if condition else 'FAIL'})
        if not condition:
            self.table('validation_checks.csv', self.checks)
            raise ValueError(f'{name}: actual={actual!r}; expected={expected!r}')

    def eq(self, name, actual, expected):
        self.check(name, actual == expected, actual, expected)

    def key(self, name, d, keys, expected_extra=0):
        sizes = d.groupby(keys, dropna=False).size()
        repeated = sizes[sizes > 1]
        extra = int((repeated - 1).sum())
        self.key_checks.append({'dataset': name, 'key': ' + '.join(keys),
            'rows': len(d), 'distinct_keys': len(sizes), 'repeated_groups': len(repeated),
            'rows_in_repeated_groups': int(repeated.sum()), 'extra_records': extra})
        self.eq(f'{name}: repeated-key extras {keys}', extra, expected_extra)
        self.eq(f'{name}: null/blank key cells {keys}',
                int(sum((d[k].isna() | d[k].eq('')).sum() for k in keys)), 0)

    def flow(self, name, before, after, expected_after, reason, removed=None):
        self.eq(name + ': final row count', after, expected_after)
        reduction = before - after
        self.flows.append({'view': name, 'input_rows': before, 'output_rows': after,
                           'reduction': reduction, 'reason': reason})
        if removed is not None:
            self.eq(name + ': exclusion ledger count', len(removed), reduction)
            for _, row in removed.iterrows():
                self.exclusions.append({'view': name, 'reason': reason,
                    'record': json.dumps({k: scalar(v) for k, v in row.items()}, ensure_ascii=False, sort_keys=True)})

    def number(self, dataset, frame, source, target, blank=0, dash=0):
        s = frame[source]
        self.eq(dataset + '.' + source + ': blanks', int(s.eq('').sum()), blank)
        self.eq(dataset + '.' + source + ': em dashes', int(s.eq('—').sum()), dash)
        missing = s.isin(['', '—'])
        x = pd.to_numeric(s.mask(missing), errors='coerce').astype('Float64')
        failed = ~missing & x.isna()
        self.conversions.append({'dataset': dataset, 'column': source, 'target': target,
            'kind': 'numeric', 'rows': len(s), 'parsed': int(x.notna().sum()),
            'source_missing': int(missing.sum()), 'failures': int(failed.sum())})
        self.eq(dataset + '.' + source + ': unexpected conversion failures', int(failed.sum()), 0)
        frame[target] = x
        return x


def load_sources(data: Path, a: Audit):
    manifest = []
    for name, expected in HASHES.items():
        p = data / name
        a.check('source exists: ' + name, p.is_file(), p.is_file(), True)
        actual = sha(p)
        manifest.append({'file': name, 'bytes': p.stat().st_size, 'sha256_before': actual,
                         'sha256_expected': expected})
        a.eq('source hash: ' + name, actual, expected)
    raw = {}
    for name, filename in FILES.items():
        with (data / filename).open(encoding='utf-8', newline='') as f:
            records = list(csv.reader(f))
        a.eq(name + ': exact headers', records[0], SCHEMAS[name])
        a.eq(name + ': malformed record widths', sum(len(r) != len(records[0]) for r in records[1:]), 0)
        raw[name] = text_frame(data / filename)
        a.eq(name + ': raw row count', len(raw[name]), SIZES[name])
    return raw, manifest


def source_profile(raw, a):
    schema, missing, exact, categories = [], [], [], []
    for name, d in raw.items():
        for c in d:
            s = d[c]
            schema.append({'dataset': name, 'column': c, 'input_dtype': str(s.dtype),
                           'rows': len(s), 'distinct': s.nunique(), 'load_rule': 'text; no automatic NA tokens'})
            missing.append({'dataset': name, 'stage': 'source', 'column': c,
                'null': int(s.isna().sum()), 'blank': int(s.eq('').sum()),
                'whitespace_only': int((s.ne('') & s.str.strip().eq('')).sum()),
                'em_dash': int(s.eq('—').sum()), 'literal_None': int(s.eq('None').sum())})
            if s.nunique() < 30:
                for val, count in s.value_counts(dropna=False, sort=False).sort_index().items():
                    categories.append({'dataset': name, 'column': c, 'value': val, 'count': int(count)})
        extra = int(d.duplicated().sum())
        involved = int(d.duplicated(keep=False).sum())
        groups = len(d[d.duplicated(keep=False)].drop_duplicates())
        exact.append({'dataset': name, 'groups': groups, 'rows_involved': involved, 'extra_rows': extra})
        a.eq(name + ': exact duplicate extras', extra, 6 if name == 'penetration' else 0)
    a.table('source_schema.csv', schema)
    a.table('source_missing.csv', missing)
    a.table('exact_duplicate_summary.csv', exact)
    a.table('source_categories.csv', categories)


def clean(raw, data, a):
    cleaned = {k: v.copy().assign(source_record=range(1, len(v) + 1)) for k, v in raw.items()}
    jobs, pen, occ, tasks, bls = [cleaned[k] for k in ['jobs', 'penetration', 'occupations', 'tasks', 'bls']]
    for name, d, code, pattern in [('jobs', jobs, 'occ_code', r'\d{2}-\d{4}'),
        ('occupations', occ, 'O*NET-SOC Code', r'\d{2}-\d{4}\.\d{2}'),
        ('tasks', tasks, 'O*NET-SOC Code', r'\d{2}-\d{4}\.\d{2}'),
        ('bls', bls, BLS_HEADERS[1], r'\d{2}-\d{4}')]:
        a.eq(name + ': invalid occupation IDs', int((~d[code].str.fullmatch(pattern)).sum()), 0)
        d['soc_code'] = d[code].str.slice(0, 7)
    a.key('jobs', jobs, ['occ_code'])
    a.key('occupations', occ, ['O*NET-SOC Code'])
    a.key('occupations_soc', occ, ['soc_code'], 149)
    a.key('tasks', tasks, ['Task ID'])
    a.key('bls', bls, ['soc_code'])
    a.eq('task ID digit validation', int((~tasks['Task ID'].str.fullmatch(r'\d+')).sum()), 0)
    for name, d, src, dst in [('jobs', jobs, 'observed_exposure', 'observed_exposure_value'),
                              ('penetration', pen, 'penetration', 'penetration_value')]:
        x = a.number(name, d, src, dst)
        a.eq(name + ': outside [0,1]', int((~x.between(0, 1)).sum()), 0)
    pen['task_normalized'] = norm(pen['task'])
    tasks['task_normalized'] = norm(tasks['Task'])
    a.key('penetration_raw_text', pen, ['task'], 6)
    a.key('penetration_normalized', pen, ['task_normalized'], 7)
    a.key('tasks_full_code_text', tasks, ['O*NET-SOC Code', 'task_normalized'])
    a.key('tasks_soc_text', tasks, ['soc_code', 'task_normalized'], 24)
    responses = a.number('tasks', tasks, 'Incumbents Responding', 'respondents', blank=587)
    a.eq('respondents integral', int((responses.dropna() % 1 != 0).sum()), 0)
    tasks['respondents'] = responses.astype('Int64')
    tasks['respondents_missing_reason'] = tasks['Domain Source'].map(
        {'Analyst': 'analyst_source_not_reported', 'Analyst - Transition': 'analyst_source_not_reported'}).fillna('')
    a.eq('respondent missingness equals analyst-source rows',
         tasks.respondents.isna().tolist(), tasks.respondents_missing_reason.ne('').tolist())
    tasks['task_type'] = tasks['Task Type'].replace('', pd.NA)
    tasks['task_type_missing_reason'] = tasks['Domain Source'].map({'Analyst': 'analyst_not_classified'}).fillna('')
    a.eq('task type missingness equals Analyst rows', tasks.task_type.isna().tolist(),
         tasks['Domain Source'].eq('Analyst').tolist())
    dates = pd.to_datetime(tasks['Date'], format='%m/%Y', errors='coerce')
    failures = int(dates.isna().sum())
    a.conversions.append({'dataset': 'tasks', 'column': 'Date', 'target': 'task_month',
                         'kind': 'date %m/%Y', 'rows': len(tasks), 'parsed': int(dates.notna().sum()),
                         'source_missing': 0, 'failures': failures})
    a.eq('strict monthly date failures', failures, 0)
    a.eq('monthly date exact round trip', dates.dt.strftime('%m/%Y').tolist(), tasks['Date'].tolist())
    tasks['task_month'] = dates.dt.strftime('%Y-%m-01')
    occ['is_base_record'] = occ['O*NET-SOC Code'].str.endswith('.00')
    a.eq('one .00 record per SOC', occ.groupby('soc_code').is_base_record.sum().eq(1).all(), True)

    wb = load_workbook(data / 'bls_occupation_tables_2025_35.xlsx', read_only=True, data_only=False)
    rows = list(wb['Table 1.2'].values)
    a.eq('workbook first fifteen headers', list(rows[1][:15]), BLS_HEADERS)
    coded = [list(r[:15]) for r in rows[2:] if isinstance(r[1], str) and r[1]]
    a.eq('workbook coded rows', len(coded), 1112)
    x = pd.DataFrame(coded, columns=BLS_HEADERS).astype('string')
    a.eq('workbook code order', x[BLS_HEADERS[1]].tolist(), bls[BLS_HEADERS[1]].tolist())
    cell_audit = []
    for c in BLS_HEADERS:
        if c in BLS_NUM:
            left = pd.to_numeric(x[c].replace('—', pd.NA), errors='coerce')
            right = pd.to_numeric(bls[c].replace('—', pd.NA), errors='coerce')
            equal = (left.isna() & right.isna()) | (left - right).abs().lt(1e-8).fillna(False)
            a.eq('workbook numeric equality: ' + c, int((~equal).sum()), 0)
        else:
            diff = x[c].ne(bls[c])
            expected = 716 if c == BLS_HEADERS[13] else 321 if c == BLS_HEADERS[14] else 0
            a.eq('workbook text differences: ' + c, int(diff.sum()), expected)
            for i in x.index[diff]:
                a.check('category recovery condition ' + bls.loc[i, 'soc_code'] + ':' + c,
                    x.loc[i, c] == 'None' and bls.loc[i, c] == '',
                    repr((x.loc[i, c], bls.loc[i, c])), "('None', '')")
                cell_audit.append({'soc_code': bls.loc[i, 'soc_code'], 'column': c,
                    'workbook_cell': f'{"NOP"[BLS_HEADERS.index(c)-13]}{i+3}' if c in BLS_HEADERS[13:15] else '',
                    'csv_original': bls.loc[i, c], 'workbook_original': x.loc[i, c],
                    'clean_value': x.loc[i, c], 'match_status': 'PASS'})
    a.table('bls_category_recovery.csv', cell_audit)
    for c, name in BLS_NUM.items():
        dash = 220 if name == 'self_employed_percent' else 9 if name == 'median_annual_wage_dollars' else 0
        a.number('bls', bls, c, name, dash=dash)
        bls[name + '_missing_reason'] = bls[c].map({'—': 'source_unavailable'}).fillna('')
    for index, canonical in [(12, 'education'), (13, 'work_experience'), (14, 'ojt')]:
        c = BLS_HEADERS[index]
        bls[canonical + '_csv_raw'] = bls[c]
        bls[canonical + '_workbook_raw'] = x[c]
        bls[canonical] = x[c].replace('—', pd.NA)
        bls[canonical + '_missing_reason'] = x[c].map({'—': 'summary_not_applicable'}).fillna('')
    a.eq('work experience None count', int(bls.work_experience.eq('None').sum()), 716)
    a.eq('OJT None count', int(bls.ojt.eq('None').sum()), 321)
    bls['bls_title'] = bls[BLS_HEADERS[0]].str.strip()
    bls['is_line_item'] = bls['Occupation type'].eq('Line item')
    a.eq('BLS row type categories', sorted(bls['Occupation type'].unique()), ['Line item', 'Summary'])
    a.eq('BLS line items', int(bls.is_line_item.sum()), 831)
    a.eq('legitimate line items ending 0', sorted(bls.loc[bls.is_line_item & bls.soc_code.str.endswith('0'), 'soc_code']),
         ['13-1020', '13-2020', '29-2010', '31-1120', '39-7010', '47-4090', '51-2090'])
    # Independent workbook table, not a second copy in the analytical data.
    other_rows = list(wb['Table 1.10'].values)
    other = pd.DataFrame([r for r in other_rows[2:] if isinstance(r[1], str) and r[1]], columns=other_rows[1])
    joined = x.merge(other.astype('string'), on=BLS_HEADERS[1], suffixes=('_12', '_10'), validate='one_to_one')
    a.eq('Table 1.10 shared key count', len(joined), 1112)
    for c in [BLS_HEADERS[i] for i in [3, 4, 7, 8, 10]]:
        diff = pd.to_numeric(joined[c + '_12']) - pd.to_numeric(joined[c + '_10'])
        a.eq('Table 1.10 shared measure: ' + c, int(diff.abs().gt(1e-8).sum()), 0)
    wb.close()
    for name, d in cleaned.items():
        a.eq(name + ': row-preserving clean count', len(d), SIZES[name])
        a.eq(name + ': all raw columns unchanged', d[SCHEMAS[name]].equals(raw[name]), True)
        a.table({'jobs': 'job_exposure_clean.csv', 'penetration': 'task_penetration_clean.csv',
            'occupations': 'onet_occupation_clean.csv', 'tasks': 'onet_task_statements_clean.csv',
            'bls': 'bls_table_1_2_clean.csv'}[name], d)
    a.table('repeated_key_summary.csv', a.key_checks)
    a.table('conversion_checks.csv', a.conversions)
    return cleaned


def joins_and_views(d, a):
    jobs, pen, occ, tasks, bls = [d[k] for k in ['jobs', 'penetration', 'occupations', 'tasks', 'bls']]
    a.eq('conflicting penetration normalized keys',
         int(pen.groupby('task_normalized').penetration_value.nunique().gt(1).sum()), 0)
    keep = ~pen.duplicated('task_normalized')
    lookup = pen[keep].copy()
    lookup['source_row_count'] = lookup.task_normalized.map(pen.groupby('task_normalized').size())
    lookup['source_records'] = lookup.task_normalized.map(pen.groupby('task_normalized').source_record.agg(lambda s: ','.join(map(str, s))))
    a.flow('penetration_lookup', len(pen), len(lookup), 17991,
           'Same normalized key and same value; retain all raw rows; consolidate lookup only', pen[~keep])
    a.table('task_penetration_lookup.csv', lookup)
    a.table('exact_duplicate_rows.csv', pen.loc[pen[SCHEMAS['penetration']].duplicated(keep=False)])
    base = occ[occ.is_base_record].copy()
    a.flow('occupation_soc_bridge', len(occ), len(base), 867,
           'Use the unique .00 description for six-digit display; suffix rows remain in clean source', occ[~occ.is_base_record])
    a.table('onet_occupation_soc_bridge.csv', base)
    keep = ~tasks.duplicated(['soc_code', 'task_normalized'])
    bridge = tasks[keep].copy()
    lineage = tasks.groupby(['soc_code', 'task_normalized']).agg(
        contributing_task_ids=('Task ID', lambda s: ','.join(s)),
        contributing_full_codes=('O*NET-SOC Code', lambda s: ','.join(s)),
        contributing_rows=('source_record', 'size')).reset_index()
    bridge = bridge.merge(lineage, on=['soc_code', 'task_normalized'], validate='one_to_one')
    a.flow('soc_task_bridge', len(tasks), len(bridge), 18814,
           'Consolidate identical task within one base SOC after suffix collapse; retain lineage', tasks[~keep])
    a.table('onet_soc_task_bridge.csv', bridge)
    full_join = tasks.merge(occ[['O*NET-SOC Code', 'Title']], on='O*NET-SOC Code',
                           how='left', validate='many_to_one', suffixes=('', '_occupation'), indicator=True)
    a.eq('task full-code occupation join rows', len(full_join), 18838)
    a.eq('task full-code unmatched rows', int(full_join['_merge'].ne('both').sum()), 0)
    a.eq('task full-code title disagreement', int(full_join['Title'].ne(full_join['Title_occupation']).sum()), 0)
    linked = bridge.merge(lookup[['task_normalized', 'penetration_value']], on='task_normalized',
                          how='left', validate='many_to_one', indicator=True)
    a.eq('task lookup join has no fanout', len(linked), len(bridge))
    linked['task_match_status'] = linked['_merge'].map({'both': 'matched', 'left_only': 'onet_only'}).astype('string')
    linked = linked.drop(columns='_merge')
    a.eq('task lookup unmatched links', int(linked.penetration_value.isna().sum()), 158)
    a.table('task_links_all.csv', linked)
    matched = linked[linked.penetration_value.notna()].copy()
    a.flow('matched_task_links', len(linked), len(matched), 18656,
           'Analytical penetration view requires a measured value; missing remains unknown', linked[linked.penetration_value.isna()])
    summary = linked.groupby('soc_code').agg(total_unique_onet_tasks=('task_normalized', 'size'),
        matched_unique_tasks=('penetration_value', 'count'),
        penetration_sum=('penetration_value', lambda s: s.sum(min_count=1)),
        average_matched_task_penetration=('penetration_value', 'mean')).reset_index()
    summary['unmatched_unique_tasks'] = summary.total_unique_onet_tasks - summary.matched_unique_tasks
    summary['task_match_rate'] = summary.matched_unique_tasks / summary.total_unique_onet_tasks
    summary['task_coverage_incomplete'] = summary.unmatched_unique_tasks.gt(0)
    a.eq('positive matched-task denominators', int(summary.matched_unique_tasks.eq(0).sum()), 0)
    a.table('task_denominators.csv', summary)
    line = bls[bls.is_line_item].copy()
    a.flow('bls_line_items', len(bls), len(line), 831, 'Exclude hierarchy summaries from detailed analysis', bls[~bls.is_line_item])
    cols = ['soc_code', 'bls_title', *BLS_NUM.values(), 'education', 'work_experience', 'ojt']
    master = jobs.merge(line[cols], on='soc_code', how='left', validate='one_to_one', indicator=True)
    master['bls_match_status'] = master['_merge'].map({'both': 'matched', 'left_only': 'job_only'}).astype('string')
    master = master.drop(columns='_merge').merge(base[['soc_code', 'Description']], on='soc_code', how='left', validate='one_to_one')
    master = master.merge(summary, on='soc_code', how='left', validate='one_to_one').sort_values('soc_code').reset_index(drop=True)
    a.flow('occupation_master', len(jobs), len(master), 756, 'Left join retains every job occupation')
    a.eq('only unmatched occupation', master.loc[master.bls_match_status.eq('job_only'), 'soc_code'].tolist(), ['11-1031'])
    a.eq('master descriptions complete', int(master.Description.isna().sum()), 0)
    a.eq('master task summaries complete', int(master.total_unique_onet_tasks.isna().sum()), 0)
    complete = master[master.bls_match_status.eq('matched')].copy()
    a.flow('bls_complete_analysis', len(master), len(complete), 755,
           'Optional analysis requires BLS data; Legislators remains in master', master[master.bls_match_status.ne('matched')])
    eligible = matched.soc_code.isin(complete.soc_code)
    occupation_tasks = matched[eligible].sort_values(['soc_code', 'penetration_value', 'task_normalized'],
                                                   ascending=[True, False, True]).copy()
    a.flow('occupation_tasks', len(matched), len(occupation_tasks), 17760,
           'Task view for the 755 BLS-complete job occupations', matched[~eligible])
    occupation_tasks['task_rank'] = occupation_tasks.groupby('soc_code').cumcount() + 1
    top = occupation_tasks[occupation_tasks.task_rank.le(5)].copy()
    a.flow('top_five_tasks', len(occupation_tasks), len(top), 3774,
           'Top five display selection, penetration descending then normalized text ascending', occupation_tasks[occupation_tasks.task_rank.gt(5)])
    for filename, frame in [('occupation_master.csv', master), ('occupation_analysis_bls_complete.csv', complete),
                            ('occupation_tasks.csv', occupation_tasks), ('top_tasks_by_occupation.csv', top)]:
        a.table(filename, frame)
    # A full outer key ledger exposes BOTH directions of every merge.
    audit_rows = []
    for relationship, left, right in [
        ('jobs_bls_line', set(jobs.soc_code), set(line.soc_code)),
        ('jobs_onet_base', set(jobs.soc_code), set(base.soc_code)),
        ('task_fullcode_occupation', set(tasks['O*NET-SOC Code']), set(occ['O*NET-SOC Code'])),
        ('penetration_onet_task', set(lookup.task_normalized), set(tasks.task_normalized))]:
        common = left & right
        for key in sorted(left | right):
            audit_rows.append({'relationship': relationship, 'key': key,
                               'status': 'both' if key in common else 'left_only' if key in left else 'right_only'})
    a.table('merge_key_audit.csv', audit_rows)
    a.table('merge_summary.csv', pd.DataFrame(audit_rows).groupby(['relationship', 'status']).size().rename('keys').reset_index())
    a.table('before_after_row_counts.csv', a.flows + [
        {'view': k + '_clean', 'input_rows': len(raw), 'output_rows': len(raw), 'reduction': 0,
         'reason': 'All original records and columns retained; parsed companions added'} for k, raw in d.items()])
    a.table('view_reductions.csv', a.exclusions)
    return master, complete, occupation_tasks, summary, lookup


def numeric_audit(raw, d, master, complete, lookup, a):
    bls = d['bls']; line = bls[bls.is_line_item]; total = bls[bls.soc_code.eq('00-0000')].iloc[0]
    controls = {
        'employment_2025_thousands': (170280.8, 170267.2, 154223.4),
        'employment_2035_thousands': (176198.5, 176184.5, 158949.6),
        'employment_change_thousands': (5917.6, 5917.9, 4726.9),
        'annual_openings_thousands': (17461.8, 17460.7, 15607.2)}
    rows = []
    for col, (expected_total, expected_line, expected_matched) in controls.items():
        published = float(total[col]); all_line = float(line[col].sum()); joined = float(complete[col].sum())
        for label, actual, expected in [('total', published, expected_total), ('line_sum', all_line, expected_line), ('matched_sum', joined, expected_matched)]:
            a.check(f'{col}: {label}', abs(actual - expected) < 1e-7, actual, expected)
        excluded = float(line.loc[~line.soc_code.isin(complete.soc_code), col].sum())
        a.check(col + ': matched + BLS-only reconciliation', abs(joined + excluded - all_line) < 1e-7,
                joined + excluded, all_line)
        rows.append({'metric': col, 'published_total': published, 'line_items_831': all_line,
            'matched_755': joined, 'bls_only_76': excluded, 'line_minus_published': all_line - published,
            'expected_line_minus_published': expected_line - expected_total,
            'explanation': 'Snapshot control; rounding/excluded occupational data. No invented correction.'})
    a.table('total_reconciliation.csv', rows)
    # Independent Decimal arithmetic on original strings, not on pandas group results.
    R = raw['bls']
    residual = [Decimal(e35) - Decimal(e25) - Decimal(ch) for e25, e35, ch in zip(R[BLS_HEADERS[3]], R[BLS_HEADERS[4]], R[BLS_HEADERS[7]])]
    a.eq('published numeric-change rounded residual count', sum(v != 0 for v in residual), 285)
    a.eq('published numeric-change max residual', max(abs(v) for v in residual), Decimal('0.1'))
    pctdiff = [Decimal(ch) / Decimal(e) * 100 - Decimal(pct) for ch, e, pct in zip(R[BLS_HEADERS[7]], R[BLS_HEADERS[3]], R[BLS_HEADERS[8]])]
    a.eq('recomputed percentage differs >0.10pp', sum(abs(v) > Decimal('.10') for v in pctdiff), 269)
    a.table('published_calculation_checks.csv', [
        {'soc_code': code, 'numeric_change_residual_thousands': str(res),
         'recomputed_percent_minus_published_pp': str(diff), 'action': 'preserve published values'}
        for code, res, diff in zip(R[BLS_HEADERS[1]], residual, pctdiff)])
    metrics = []
    for label, frame, col in [('job_exposure_all', master, 'observed_exposure_value'),
                             ('job_exposure_bls_complete', complete, 'observed_exposure_value'),
                             ('penetration_raw', d['penetration'], 'penetration_value'),
                             ('penetration_normalized_lookup', lookup, 'penetration_value')]:
        metrics.append({'metric': label, 'records': len(frame), 'nonmissing_denominator': int(frame[col].count()),
                        'numerator': frame[col].sum(min_count=1), 'mean': frame[col].mean(),
                        'missing_policy': 'exclude null from denominator; retain measured zero'})
    weighted = (complete.observed_exposure_value * complete.employment_2025_thousands).sum()
    metrics.append({'metric': 'employment_weighted_exposure', 'records': len(complete),
        'nonmissing_denominator': complete.employment_2025_thousands.sum(), 'numerator': weighted,
        'mean': weighted / complete.employment_2025_thousands.sum(),
        'missing_policy': 'matched occupations only; denominator in thousands, not occupation count'})
    a.table('metric_denominators.csv', metrics)
    # Verify all occupation averages independently, including null semantics.
    source_pen = {r.task_normalized: Decimal(r.penetration) for r in d['penetration'].itertuples()}
    task_keys = {}
    for row in d['tasks'].itertuples():
        task_keys.setdefault(row.soc_code, set()).add(row.task_normalized)
    for row in master.itertuples():
        keys = task_keys[row.soc_code]; values = [source_pen[k] for k in keys if k in source_pen]
        a.eq(row.soc_code + ': independent total task count', row.total_unique_onet_tasks, len(keys))
        a.eq(row.soc_code + ': independent matched count', row.matched_unique_tasks, len(values))
        expected = float(sum(values) / len(values))
        a.check(row.soc_code + ': independent task mean', abs(row.average_matched_task_penetration - expected) < 1e-12,
                row.average_matched_task_penetration, expected)
    a.eq('all job source exposure total Decimal', sum(map(Decimal, raw['jobs'].observed_exposure)), Decimal('58.1944'))
    a.eq('raw penetration total Decimal', sum(map(Decimal, raw['penetration'].penetration)), Decimal('1201.2546'))
    a.check('lookup penetration total', abs(float(lookup.penetration_value.sum()) - 1196.1705) < 1e-8, lookup.penetration_value.sum(), 1196.1705)


def profiles_after(raw, d, a):
    rows, schema, flags, text_changes = [], [], [], []
    mapping = {'jobs': {'observed_exposure': 'observed_exposure_value'},
        'penetration': {'penetration': 'penetration_value'}, 'occupations': {},
        'tasks': {'Task Type': 'task_type', 'Incumbents Responding': 'respondents', 'Date': 'task_month'},
        'bls': {**BLS_NUM, BLS_HEADERS[12]: 'education', BLS_HEADERS[13]: 'work_experience', BLS_HEADERS[14]: 'ojt'}}
    for name, frame in d.items():
        for col in frame:
            schema.append({'dataset': name, 'column': col, 'dtype': str(frame[col].dtype),
                           'rows': len(frame), 'nulls': int(frame[col].isna().sum())})
        for col in raw[name]:
            dst = mapping[name].get(col, col); before = raw[name][col]; after = frame[dst]
            rows.append({'dataset': name, 'source_column': col, 'clean_column': dst,
                'before_blank': int(before.eq('').sum()), 'before_em_dash': int(before.eq('—').sum()),
                'before_literal_None': int(before.eq('None').sum()), 'after_null': int(after.isna().sum()),
                'after_blank': int(after.eq('').sum()), 'after_em_dash': int(after.eq('—').sum()),
                'after_literal_None': int(after.eq('None').sum()),
                'rule': 'Preserve raw; typed companion; BLS categories from workbook; no statistical imputation'})
    for name, source, target in [('penetration', 'task', 'task_normalized'), ('tasks', 'Task', 'task_normalized'), ('bls', BLS_HEADERS[0], 'bls_title')]:
        frame = d[name]
        for _, row in frame.loc[frame[source].ne(frame[target])].iterrows():
            text_changes.append({'dataset': name, 'source_record': row.source_record, 'column': source,
                                 'original': row[source], 'derived': row[target], 'rule': 'conservative task key' if target == 'task_normalized' else 'display title only'})
    for name, col in [('jobs', 'observed_exposure_value'), ('penetration', 'penetration_value'),
        *[('bls', c) for c in BLS_NUM.values()]]:
        frame = d[name]; s = frame[col]
        if col in ['observed_exposure_value', 'penetration_value']:
            invalid = ~s.between(0, 1)
        elif 'percent' in col and col != 'employment_change_percent':
            invalid = s.notna() & ~s.between(0, 100)
        elif col.startswith('employment_change'):
            invalid = s.notna() & s.lt(-100) if col.endswith('percent') else s.isna()
        else:
            invalid = s.notna() & s.lt(0)
        a.eq(name + ':' + col + ': impossible values', int(invalid.sum()), 0)
        selected = s.isna() | s.eq(0) | s.lt(0) | s.eq(s.max())
        for _, row in frame[selected].iterrows():
            value = row[col]
            reason = 'source_unavailable' if pd.isna(value) else 'measured_zero' if value == 0 else 'negative_projected_change' if value < 0 else 'observed_maximum'
            flags.append({'dataset': name, 'source_record': row.source_record, 'column': col,
                          'value': scalar(value), 'reason': reason, 'disposition': 'Retain; flag only; no clipping or imputation'})
    a.table('before_after_missing.csv', rows)
    a.table('clean_schema.csv', schema)
    a.table('text_changes.csv', text_changes)
    a.table('suspicious_values.csv', flags)
    a.table('task_vintage_counts.csv', d['tasks'].groupby('task_month').size().rename('rows').reset_index())
    # Explicitly guard known punctuation pairs against over-normalization.
    pairs = [('Maintain customer records using automated systems.', 'Maintain customer records, using automated systems.', '0.7239', '1.0'),
        ('Advise students on academic and vocational curricula and on career issues.', 'Advise students on academic and vocational curricula, and on career issues.', '0.7735', '0.8157'),
        ('Compile, administer, and grade examinations or assign this work to others.', 'Compile, administer, and grade examinations, or assign this work to others.', '0.9669', '0.9134')]
    for left, right, lv, rv in pairs:
        pen = d['penetration'].set_index('task')
        a.eq('punctuation left preserved: ' + left, pen.loc[left, 'penetration'], lv)
        a.eq('punctuation right preserved: ' + right, pen.loc[right, 'penetration'], rv)
        a.check('punctuation keys remain distinct: ' + left,
                pen.loc[left, 'task_normalized'] != pen.loc[right, 'task_normalized'], 'distinct', 'distinct')


def five_records(raw, a):
    specs = json.loads(EXPECTATIONS.read_text(encoding='utf-8'))
    records = []
    for spec in specs:
        frame = text_frame(a.out / spec['dataset'])
        selected = frame[frame[spec['key_column']].eq(spec['key'])]
        a.eq('record case ' + spec['case'] + ': unique saved row', len(selected), 1)
        row = selected.iloc[0]
        actual = {k: row[k] for k in spec['expected']}
        # Numerics compare explicitly within serialization precision; text exact.
        matches = []
        for col, exp in spec['expected'].items():
            act = actual[col]
            if col in BLS_NUM.values() or col in ['observed_exposure_value', 'task_match_rate', 'average_matched_task_penetration']:
                matches.append(act == exp if '' in [act, exp] else abs(Decimal(act) - Decimal(exp)) <= Decimal('0.000000000001'))
            else:
                matches.append(act == exp)
        if spec['case'] in ['1', '2', '3']:
            origin = raw['bls'].loc[raw['bls'][BLS_HEADERS[1]].eq(spec['key'])].iloc[0].to_dict()
            if spec['case'] == '2':
                origin['workbook_ojt_original'] = row['ojt_workbook_raw']
        else:
            origin = raw['jobs'].loc[raw['jobs'].occ_code.eq(spec['key'])].iloc[0].to_dict()
            if spec['case'] == '5':
                origin['onet_task_IDs'] = raw['tasks'].loc[raw['tasks']['O*NET-SOC Code'].str.startswith(spec['key'] + '.'), 'Task ID'].tolist()
        records.append({'case': spec['case'], 'record_key': spec['key'], 'reason': spec['reason'],
            'original': json.dumps(origin, ensure_ascii=False, sort_keys=True),
            'expected': json.dumps(spec['expected'], ensure_ascii=False, sort_keys=True),
            'actual': json.dumps(actual, ensure_ascii=False, sort_keys=True),
            'match_status': 'PASS' if all(matches) else 'FAIL',
            'expectation_source': 'code/module6_record_expectations.json; authored before cleaning run'})
    a.table('five_record_checks.csv', records)
    a.eq('five saved-output record checks', sum(r['match_status'] == 'PASS' for r in records), 5)


def sample(master, bls, a):
    mandatory = ['11-1011', '11-1031', '23-2011', '27-2011', '51-2061']
    remaining = [c for c in sorted(master.soc_code) if c not in mandatory]
    codes = mandatory + remaining[:43]
    s = master[master.soc_code.isin(codes)].sort_values('soc_code').copy()
    s['sample_origin'] = 'occupation_master'
    s['selection_reason'] = s.soc_code.map({c: 'difficult_case' for c in mandatory}).fillna('first remaining SOCs in lexical order')
    control = bls.loc[bls.soc_code.isin(['00-0000', '31-1120'])].copy()
    control['title'] = control.bls_title
    control['sample_origin'] = 'bls_control'
    control['selection_reason'] = control.soc_code.map({
        '00-0000': 'leading-zero summary; not a detailed occupation',
        '31-1120': 'line item ending in 0; no matching job exposure code'})
    control['bls_match_status'] = control.soc_code.map({'00-0000': 'summary_control', '31-1120': 'bls_only'})
    cols = ['sample_origin', 'selection_reason', 'soc_code', 'title', 'bls_match_status',
        'observed_exposure_value', 'employment_2025_thousands', 'employment_2035_thousands',
        'employment_change_percent', 'annual_openings_thousands', 'median_annual_wage_dollars',
        'work_experience', 'ojt', 'total_unique_onet_tasks', 'matched_unique_tasks',
        'unmatched_unique_tasks', 'task_match_rate', 'average_matched_task_penetration', 'task_coverage_incomplete']
    s = pd.concat([control, s], ignore_index=True).reindex(columns=cols)
    a.eq('sample maximum 50 records', len(s), 50)
    a.table('cleaned_sample.csv', s)


def decision_log(a):
    rules = [
        ('SCOPE', 'all', 'National screening; compare exposure, task evidence and BLS context', 'California conclusions need California data; score not approved', 'No priority score, weights or thresholds emitted', 0),
        ('RAW', 'all', 'Immutable hash-pinned inputs; preserve raw fields and rows', 'Make every change attributable', 'Source hashes before/after and clean row counts', 0),
        ('ID', 'all identifiers', 'Text dtype; full IDs retained; derive SOC base separately', 'Avoid leading-zero loss and suffix erasure', 'Fullmatch, uniqueness, output text reload; case 1', 0),
        ('NONE', 'BLS work_experience / ojt', 'Copy code-aligned workbook categories to new canonical fields', 'CSV blanks erased meaningful no-experience/no-training categories', '1037 workbook cell recoveries; other cells equivalent; case 2', 1037),
        ('MARKER', 'BLS numeric and category fields', 'Em dash to nullable companion and explicit reason', 'Unavailable or summary not applicable differs from zero/None', 'Before/after markers; no unexpected conversion failures', 0),
        ('STRUCTURAL', 'O*NET Task Type/respondents', 'Preserve structural blanks as null; retain source reason', 'Analyst-source records do not supply these metadata', '418 type blanks; 587 respondent blanks; source cross-tab', 0),
        ('TEXT', 'task strings', 'Lowercase, collapse whitespace, trim derived keys only', 'Conservative cross-source task linkage', 'Three punctuation-conflict regression pairs remain distinct', 0),
        ('PEN_DUP', 'penetration lookup', 'Consolidate only identical values at normalized key; retain lineage', 'Prevent task lookup fanout and repeated weighting', '17998 to 17991; seven exclusions; zero conflicts', 7),
        ('ONET_BASE', 'occupation description bridge', 'Select the unique .00 record per base SOC', 'One description per occupation while preserving suffix detail', '1016 to 867; 149 suffix exclusions; all groups have .00', 149),
        ('TASK_DUP', 'SOC/task bridge', 'One normalized task per six-digit SOC; keep contributing IDs', 'Do not overweight repeated tasks after suffix collapse', '18838 to 18814; 24 exclusions', 24),
        ('SUMMARY', 'BLS detailed view', 'Filter Occupation type Line item, never infer from code ending', 'Avoid hierarchy double counting', '1112 to 831; seven legitimate line items ending 0 retained', 281),
        ('JOIN', 'occupation master', 'Left join jobs to BLS one-to-one', 'Keep measured exposure even when BLS is absent', '756 master rows; job_only Legislators; case 4', 0),
        ('COMPLETE', 'BLS-complete view', 'Optional filter; preserve unmatched master and audit', 'Explicit population for comparisons requiring BLS', '756 to 755; one exclusion', 1),
        ('TASK_AVG', 'task metrics', 'Average unique matched task values; report full/ matched denominators', 'Unmatched is unknown, not measured zero', 'Independent Decimal mean for every master SOC; case 5', 0),
        ('ROUNDED', 'BLS values', 'Preserve published units, zeros, negative projections and percent change', 'Displayed source precision cannot reproduce all source calculations', '285 subtraction residuals <=0.1 thousand; case 3', 0),
        ('TOP5', 'display view', 'Sort penetration descending then normalized text; retain first five', 'Stable descriptive task display specified by project', '17760 to 3774 with row-level exclusions', 13986),
    ]
    a.table('cleaning_decision_log.csv', [{'decision_id': k, 'status': 'implemented', 'dataset_or_column': col,
        'rule': rule, 'reason': reason, 'check': check, 'expected_reduction_or_recoveries': affected,
        'exceptions': 'Fail on unexpected input, conflicting value, invalid conversion, or count drift',
        'authorization': 'User reviewed rules and requested implementation; no commit/push',
        'code_sha256': sha(SCRIPT)} for k, col, rule, reason, check, affected in rules])


def run(data, out):
    a = Audit(out)
    raw, manifest = load_sources(data, a)
    source_profile(raw, a)
    d = clean(raw, data, a)
    master, complete, occupation_tasks, summary, lookup = joins_and_views(d, a)
    numeric_audit(raw, d, master, complete, lookup, a)
    profiles_after(raw, d, a)
    five_records(raw, a)
    sample(master, d['bls'], a)
    decision_log(a)
    # Round-trip every source ID from the actual saved clean files.
    for filename, clean_name, key in [('job_exposure.csv', 'job_exposure_clean.csv', 'occ_code'),
        ('onet_occupation_data.csv', 'onet_occupation_clean.csv', 'O*NET-SOC Code'),
        ('onet_task_statements.csv', 'onet_task_statements_clean.csv', 'Task ID'),
        ('bls_table_1_2_2025_35.csv', 'bls_table_1_2_clean.csv', BLS_HEADERS[1])]:
        a.eq('saved identifier round trip: ' + filename, text_frame(out / clean_name)[key].tolist(), text_frame(data / filename)[key].tolist())
    for record in manifest:
        record['sha256_after'] = sha(data / record['file'])
        a.eq('source unchanged: ' + record['file'], record['sha256_after'], record['sha256_before'])
    a.table('source_manifest.csv', manifest)
    a.table('validation_checks.csv', a.checks)
    metadata = {'scope': 'National occupation-screening prototype', 'python': platform.python_version(),
        'packages': {p: importlib.metadata.version(p) for p in ['pandas', 'numpy', 'openpyxl', 'et-xmlfile', 'python-dateutil', 'six', 'tzdata']},
        'code_sha256': sha(SCRIPT), 'expectations_sha256': sha(EXPECTATIONS),
        'dependencies_sha256': sha(ROOT / 'requirements-cleaning.txt'),
        'checks_passed': len(a.checks), 'checks_failed': 0, 'priority_score': 'not calculated'}
    (out / 'run_manifest.json').write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    report = ['# Module 6 cleaning report', '',
        'National occupation-screening prototype. Compare observed occupation exposure and matched task penetration with BLS employment/outlook/training context.', '',
        f'Validation: {len(a.checks)} PASS; 0 FAIL. All six source hashes unchanged.',
        'Five individual saved-output record checks: 5 PASS. Expected values were recorded before execution.',
        'Rows: 756 occupation master; 755 BLS-complete occupations; 17,760 occupation-task links; 3,774 top-task rows.',
        'All five clean source tables retain their original rows and raw columns. 1,037 BLS category companions recover literal None from the workbook.', '',
        '## How a Codex suggestion was checked', '',
        'The suggestion to restore BLS None was checked against every code-aligned workbook cell. bls_category_recovery.csv records 716 experience and 321 OJT recoveries. The script asserts no other text differences, numeric equivalence, and shared-measure agreement with Table 1.10. It does not fill other blanks by analogy.', '',
        '## Evidence', '',
        '- before_after_row_counts.csv and view_reductions.csv account for every derived reduction.',
        '- before_after_missing.csv compares every source column with its canonical companion.',
        '- merge_key_audit.csv, merge_summary.csv, total_reconciliation.csv and metric_denominators.csv expose populations and totals.',
        '- five_record_checks.csv includes original, expected, actual and match status.',
        '- cleaning_decision_log.csv records each rule, reason and check.',
        '- Reproducibility is verified in a separate fresh-process run using verify_module6.py.', '',
        '## Remaining limitations', '', *['- ' + text for text in LIMITATIONS], '']
    (out / 'cleaning_report.md').write_text('\n'.join(report), encoding='utf-8')
    print(json.dumps(metadata, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    p.add_argument('--output-dir', type=Path, default=ROOT / 'outputs' / 'module6')
    args = p.parse_args()
    data = args.data_dir.resolve(); out = args.output_dir.resolve()
    output_root = (ROOT / 'outputs').resolve()
    if not out.is_relative_to(output_root) or out == output_root or out.is_relative_to(data) or data.is_relative_to(out):
        p.error('Output must be a new child of repository outputs/, disjoint from data.')
    if out.exists():
        p.error('Output already exists. Choose a fresh --output-dir; previous evidence is never overwritten.')
    out.mkdir(parents=True)
    try:
        run(data, out)
    except Exception as exc:
        (out / 'FAILED.json').write_text(json.dumps({'status': 'FAIL', 'error': str(exc)}, indent=2) + '\n', encoding='utf-8')
        raise


if __name__ == '__main__':
    main()
