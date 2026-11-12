#!/usr/bin/env bash
# Run from any directory. Generated files stay outside the vendor checkout.
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
source_dir="$project_root/experiments/vendor/vsag"
build_dir="$project_root/experiments/build/vsag"
expected=295acf3c5e1b202bd414ef42f11b9d741aefdd6a
if [[ $(git -C "$source_dir" rev-parse HEAD) != "$expected" ]]; then
    echo "VSAG commit differs from pinned v0.15.0" >&2
    exit 1
fi
for command in cmake g++ make gfortran; do
    command -v "$command" >/dev/null || { echo "Missing: $command" >&2; exit 1; }
done
# CMake build trees contain absolute paths and cannot be moved as a cache.
if [[ -f "$build_dir/CMakeCache.txt" ]]; then
    cached_source=$(sed -n 's/^CMAKE_HOME_DIRECTORY:INTERNAL=//p' "$build_dir/CMakeCache.txt")
    cached_build=$(sed -n 's/^CMAKE_CACHEFILE_DIR:INTERNAL=//p' "$build_dir/CMakeCache.txt")
    if [[ "$cached_source" != "$source_dir" || "$cached_build" != "$build_dir" ]]; then
        backup_dir="${build_dir}.before-relocation.$(date +%Y%m%d-%H%M%S).$$"
        echo "Moved CMake cache detected; preserving it in $backup_dir"
        mv -- "$build_dir" "$backup_dir"
    fi
fi
mkdir -p "$build_dir/logs"
cmake -S "$source_dir" -B "$build_dir" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$build_dir/install" \
    -DENABLE_INTEL_MKL=OFF \
    -DENABLE_TESTS=OFF -DENABLE_TOOLS=OFF -DENABLE_PYBINDS=OFF \
    -DENABLE_EXAMPLES=ON \
    -DDISABLE_AVX512_FORCE=OFF -DDISABLE_AVX512VPOPCNTDQ_FORCE=OFF \
    -DNUM_BUILDING_JOBS=2 2>&1 | tee "$build_dir/logs/configure.log"
cmake --build "$build_dir" --target 101_index_hnsw 103_index_hgraph \
    --parallel 2 2>&1 | tee "$build_dir/logs/build.log"
