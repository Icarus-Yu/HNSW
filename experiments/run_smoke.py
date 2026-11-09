"""Linux/WSL smoke experiment, no Python dependencies required."""
from pathlib import Path
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys

root = Path(__file__).resolve().parent
os.chdir(root)
build = root / 'build'
data = root / 'data'
results = root / 'results'
for p in [build, data, results]: p.mkdir(exist_ok=True)

def run(args, **kwargs):
    print('+', ' '.join(map(str, args)), flush=True)
    return subprocess.run(list(map(str, args)), check=True, **kwargs)

run([sys.executable, root / 'prepare_variant.py'])
flags = ['g++', '-std=c++17', '-O3', '-march=native', '-DNDEBUG', '-pthread']
variants = [('baseline', None, None), ('valid_s1_d1', 1, 1), ('valid_s4_d2', 4, 2)]
metadata = {
    'purpose': 'VSAG section 3.2 partial method reproduction; synthetic smoke only',
    'platform': platform.platform(),
    'compiler': subprocess.check_output(['g++', '--version'], text=True).splitlines()[0],
    'hnswlib_commit': subprocess.check_output(['git', '-c', f'safe.directory={root / "vendor/hnswlib"}', '-C', str(root / 'vendor/hnswlib'), 'rev-parse', 'HEAD'], text=True).strip(),
    'flags': flags[1:], 'seed': 20261109, 'M': 16, 'ef_construction': 200,
    'timing': 'single-thread search call only, 300 warmup queries per ef, 3 repetitions',
    'affinity': sorted(os.sched_getaffinity(0)),
}
for label, stride, depth in variants:
    includes = root / ('vendor/hnswlib' if stride is None else 'build/valid')
    args = flags + ['-I', str(includes)]
    if stride is not None:
        args += [f'-DHNSW_PREFETCH_STRIDE={stride}', f'-DHNSW_PREFETCH_DEPTH={depth}']
    run(args + [root / 'smoke.cpp', '-o', build / label])
run([build / 'baseline', 'prepare', data])
rows = []
for label, _, _ in variants:
    output = subprocess.check_output([str(build / label), 'run', str(data), label], text=True)
    (results / (label + '.csv')).write_text(output)
    rows.extend(csv.DictReader(output.splitlines()))
checks = []
for ef in [32, 64, 128]:
    reference = (data / f'baseline_ef{ef}.ids').read_bytes()
    for label, _, _ in variants[1:]:
        if (data / f'{label}_ef{ef}.ids').read_bytes() != reference:
            raise RuntimeError(f'result IDs differ: {label}, ef={ef}')
        checks.append(f'{label} ef={ef}: all 300 top-10 sets equal baseline')
metadata['correctness_checks'] = checks
metadata['index_sha256'] = hashlib.sha256((data / 'shared.hnsw').read_bytes()).hexdigest()
(results / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
with (results / 'smoke.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
print('\n'.join(checks))
print('Saved results to', results)
