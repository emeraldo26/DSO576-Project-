# Module 6 cleaned review sample

`module6_cleaned_sample.csv` contains exactly **50 real cleaned rows**:

- Two BLS controls: `00-0000` (leading-zero national summary) and `31-1120`
  (a legitimate line item ending in zero, absent from job exposure).
- Forty-eight occupation-master rows: required codes `11-1011`, `11-1031`,
  `23-2011`, `27-2011`, `51-2061`, plus the first 43 remaining SOCs in lexical order.

These cases exercise restored literal `None`, unmatched Legislators, partial
task coverage, unavailable wage, and a published change that cannot be computed
from displayed rounded employment. Together with `00-0000`, they cover all five
record-check cases. `sample_origin` and `selection_reason` explain every row.

The two BLS controls have no exposure/task values; those blanks do not mean zero.
Do not sum the national summary with detailed occupations. This deliberately
selected sample is not statistically representative.

Load with `pd.read_csv(path, dtype='string', keep_default_na=False)` to retain
literal `None`, leading zeros, and visible blanks. Consult `clean_schema.csv`
before numeric conversion. Units appear in the headers: employment/openings in
thousands, wage in dollars, BLS percent values, and 0–1 AI measurements.

The pipeline's `cleaned_sample.csv` reproduces this file byte for byte.
`code/verify_module6.py` checks the match in a new process. This is the only
submitted cleaned-data sample; `docs/module6_evidence/` holds audit records/counts.
