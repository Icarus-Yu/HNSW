"""Validate pinned upstream examples; this is not a recall/QPS benchmark."""
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'experiments/vendor/vsag'
BUILD = ROOT / 'experiments/build/vsag'
EXPECTED = '295acf3c5e1b202bd414ef42f11b9d741aefdd6a'
CASES = [('101_index_hnsw', 'HNSW', 1000), ('103_index_hgraph', 'HGraph', 10000)]


def main():
    commit = subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != EXPECTED:
        raise RuntimeError('VSAG checkout does not match pinned commit')
    for name, _, _ in CASES:
        if not (BUILD / 'examples/cpp' / name).is_file():
            raise RuntimeError(f'Missing {name}; first run bash experiments/vsag/build.sh')
    stamp = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%d_%H%M%S_%f')
    output = Path(__file__).resolve().parent / 'results' / stamp
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    report = {
        'purpose': 'Upstream examples API smoke; no recall or QPS claims',
        'vsag_commit': commit, 'platform': platform.platform(),
        'compiler': subprocess.check_output(['g++', '--version'], text=True).splitlines()[0],
        'cmake': subprocess.check_output(['cmake', '--version'], text=True).splitlines()[0],
        'affinity': sorted(os.sched_getaffinity(0)),
        'thread_environment': {key: env[key] for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS']},
        'cmake_cache_sha256': hashlib.sha256((BUILD / 'CMakeCache.txt').read_bytes()).hexdigest(),
        'cases': [],
    }
    for name, label, count in CASES:
        start = time.perf_counter()
        run = subprocess.run([str(BUILD / 'examples/cpp' / name)], cwd=output,
                             env=env, text=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, timeout=300)
        elapsed = time.perf_counter() - start
        (output / f'{name}.stdout.txt').write_text(run.stdout)
        (output / f'{name}.stderr.txt').write_text(run.stderr)
        if run.returncode:
            raise RuntimeError(f'{name} exited {run.returncode}; see {output}')
        if f'Index {label} contains: {count}' not in run.stdout:
            raise RuntimeError(f'{name}: unexpected index size; see {output}')
        matches = re.findall(r'^([0-9]+):\s*(\S+)\s*$', run.stdout, re.MULTILINE)
        ids = [int(key) for key, _ in matches]
        distances = [float(value) for _, value in matches]
        if (len(ids) != 10 or len(set(ids)) != 10
                or not all(0 <= key < count for key in ids)
                or not all(math.isfinite(value) and value >= 0 for value in distances)
                or distances != sorted(distances)):
            raise RuntimeError(f'{name}: invalid top-10 shape/IDs/distances; see {output}')
        report['cases'].append({'example': name, 'n': count, 'dim': 128,
                                'nq': 1, 'k': 10, 'seed': 47,
                                'quantization': 'sq8' if label == 'HGraph' else 'fp32',
                                'wall_seconds_including_build': elapsed,
                                'checks': 'size, 10 unique in-range IDs, finite nonnegative sorted distances',
                                'binary_sha256': hashlib.sha256((BUILD / 'examples/cpp' / name).read_bytes()).hexdigest(),
                                'example_source_sha256': hashlib.sha256(
                                    (SOURCE / 'examples/cpp' / f'{name}.cpp').read_bytes()).hexdigest()})
        print(f'{name}: n={count}, dim=128, top-10 checks passed', flush=True)
    (output / 'metadata.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Saved: {output}')


if __name__ == '__main__':
    main()
