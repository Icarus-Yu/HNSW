"""Generate an experimental header; leave the pinned upstream source untouched."""
from pathlib import Path
import hashlib
import shutil

root = Path(__file__).resolve().parent
src = root / 'vendor/hnswlib/hnswlib'
expected = '37dbdbf8f5836102f78ad022c1aac26e1818bc0704e21aff36c79e56c1720a37'
if hashlib.sha256((src / 'hnswalg.h').read_bytes()).hexdigest() != expected:
    raise RuntimeError('Expected unmodified hnswlib v0.8.0 hnswalg.h; refusing to patch another source')
dst = root / 'build/valid/hnswlib'
dst.mkdir(parents=True, exist_ok=True)
for p in src.glob('*.h'):
    shutil.copyfile(p, dst / p.name)
p = dst / 'hnswalg.h'
s = p.read_text()
start = s.index('    searchBaseLayerST(')
end = s.index('    void getNeighborsByHeuristic2(', start)
fn = s[start:end]
fn = fn.replace('        while (!candidate_set.empty()) {', '''        // This spike supports static, unfiltered search with the standard stop rule.
        assert(bare_bone_search && !isIdAllowed && !stop_condition);
        std::vector<tableint> valid_neighbors;
        valid_neighbors.reserve(maxM0_);
        while (!candidate_set.empty()) {''', 1)
a = fn.index('#ifdef USE_SSE', fn.index('metric_distance_computations+=size;'))
b = fn.index('                    char *currObj1', a)
fn = fn[:a] + '''            // VSAG section 3.2: gather valid IDs in original order first.
            valid_neighbors.clear();
            for (size_t j = 1; j <= size; ++j) {
                tableint id = static_cast<tableint>(*(data + j));
                if (visited_array[id] != visited_array_tag) {
                    visited_array[id] = visited_array_tag;
                    valid_neighbors.push_back(id);
                }
            }
            auto prefetch_vector = [&](tableint id) {
                const char* ptr = getDataByInternalId(id);
                const size_t lines = std::min<size_t>(HNSW_PREFETCH_DEPTH,
                                                      (data_size_ + 63) / 64);
                for (size_t line = 0; line < lines; ++line)
                    __builtin_prefetch(ptr + line * 64, 0, 3);
            };
            for (size_t j = 0; j < std::min<size_t>(HNSW_PREFETCH_STRIDE, valid_neighbors.size()); ++j)
                prefetch_vector(valid_neighbors[j]);
            for (size_t j = 0; j < valid_neighbors.size(); ++j) {
                const tableint candidate_id = valid_neighbors[j];
                if (j + HNSW_PREFETCH_STRIDE < valid_neighbors.size())
                    prefetch_vector(valid_neighbors[j + HNSW_PREFETCH_STRIDE]);
                { // Keep upstream distance computation and queue updates unchanged.
''' + fn[b:]
s = s[:start] + fn + s[end:]
p.write_text(s)
print('Generated valid-neighbor/stride-prefetch variant from hnswlib v0.8.0')
