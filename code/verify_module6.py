"""Rebuild in a fresh Python process and compare every emitted byte.

Also checks the submitted 50-row sample and runs a source-drift negative test.
Temporary inputs and outputs are scoped to a new directory under outputs/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def inventory(folder):
    return {str(p.relative_to(folder)).replace('\\', '/'): digest(p)
            for p in sorted(folder.rglob('*')) if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, default=ROOT / 'outputs/module6')
    parser.add_argument('--sample', type=Path, default=ROOT / 'examples/module6_cleaned_sample.csv')
    parser.add_argument('--report', type=Path, default=ROOT / 'outputs/module6_reproducibility.json')
    args = parser.parse_args()
    baseline, report = args.baseline.resolve(), args.report.resolve()
    root = (ROOT / 'outputs').resolve()
    if not report.is_relative_to(root) or report.is_relative_to(baseline):
        parser.error('Report must be under outputs/ and outside the baseline directory.')
    if report.exists():
        parser.error('Choose a fresh report filename; previous reports are not overwritten.')
    if (baseline / 'FAILED.json').exists() or not (baseline / 'run_manifest.json').exists():
        parser.error('Baseline must be a completed successful pipeline run.')
    result = {'status': 'FAIL', 'method': 'Fresh subprocess from original sources; byte-for-byte comparison of every output',
              'sample': str(args.sample.relative_to(ROOT)) if args.sample.is_relative_to(ROOT) else str(args.sample)}
    try:
        with tempfile.TemporaryDirectory(prefix='module6-verify-', dir=root) as tmp:
            work = Path(tmp)
            fresh = work / 'rebuild'
            cmd = [sys.executable, str(ROOT / 'code/clean_module6.py'), '--output-dir', str(fresh)]
            process = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
            if process.returncode:
                raise RuntimeError('Fresh-process rebuild failed: ' + process.stderr)
            before, after = inventory(baseline), inventory(fresh)
            mismatches = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
            result['files_compared'] = len(before)
            result['mismatches'] = mismatches
            result['baseline_output_sha256'] = before
            if mismatches:
                raise ValueError('Rebuilt files differ: ' + ', '.join(mismatches))
            result['submitted_sample_matches'] = digest(args.sample) == digest(fresh / 'cleaned_sample.csv')
            if not result['submitted_sample_matches']:
                raise ValueError('Submitted sample differs from regenerated sample.')
            # Deliberate corruption in disposable input copies must be rejected.
            altered = work / 'altered_sources'
            altered.mkdir()
            for source in (ROOT / 'data').iterdir():
                if source.suffix in ('.csv', '.xlsx'):
                    shutil.copyfile(source, altered / source.name)
            target = altered / 'job_exposure.csv'
            target.write_bytes(target.read_bytes().replace(b'0.0333', b'0.9333', 1))
            negative = work / 'negative_test'
            rejected = subprocess.run([sys.executable, str(ROOT / 'code/clean_module6.py'),
                '--data-dir', str(altered), '--output-dir', str(negative)], cwd=ROOT,
                capture_output=True, text=True, encoding='utf-8')
            failure = json.loads((negative / 'FAILED.json').read_text(encoding='utf-8'))
            result['source_drift_rejected'] = rejected.returncode != 0 and 'source hash: job_exposure.csv' in failure['error']
            if not result['source_drift_rejected']:
                raise ValueError('Corrupted-input negative test failed to reject source drift.')
            result['negative_test_expected_error'] = 'source hash: job_exposure.csv mismatch (disposable copied input only)'
            result['status'] = 'PASS'
    except Exception as exc:
        result['error'] = str(exc)
        raise
    finally:
        report.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(f"PASS: {result['files_compared']} files identical; submitted sample identical; unexpected source drift rejected.")


if __name__ == '__main__':
    main()
