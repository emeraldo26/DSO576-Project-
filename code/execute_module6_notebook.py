"""Execute the submission notebook in a fresh, explicitly selected Python kernel."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import tempfile

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'code/module6_cleaning.ipynb'
notebook = nbformat.read(path, as_version=4)
with tempfile.TemporaryDirectory(prefix='module6-kernel-') as temp:
    spec = Path(temp) / 'module6'
    spec.mkdir()
    (spec / 'kernel.json').write_text(json.dumps({
        'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
        'display_name': 'Module 6 pinned Python', 'language': 'python'
    }), encoding='utf-8')
    manager = KernelManager(kernel_name='module6',
                            kernel_spec_manager=KernelSpecManager(kernel_dirs=[temp]))
    NotebookClient(notebook, km=manager, timeout=600,
                   resources={'metadata': {'path': str(ROOT)}}).execute()
code_cells = [c for c in notebook.cells if c.cell_type == 'code']
assert all(c.execution_count is not None for c in code_cells)
assert not any(o.output_type == 'error' for c in code_cells for o in c.outputs)
nbformat.write(notebook, path)
receipt = {
    'status': 'PASS', 'fresh_kernel': True, 'python': sys.version.split()[0],
    'executed_code_cells': len(code_cells), 'error_outputs': 0,
    'notebook_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'packages': {p: importlib.metadata.version(p) for p in
                 ('nbformat', 'nbclient', 'ipykernel', 'reportlab', 'pymupdf')},
    'method': 'nbclient; disposable kernelspec explicitly uses this process Python; errors abort'
}
(ROOT / 'docs/module6_evidence/notebook_execution.json').write_text(
    json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt, indent=2))
