#include "hnswlib/hnswlib.h"
#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using Clock = std::chrono::steady_clock;
constexpr size_t K = 10;
struct Data {
    size_t n, nq, dim;
    std::vector<float> base, queries;
    std::vector<uint32_t> truth;
};
template<class T> void transfer(std::fstream& f, T* p, size_t n, bool write) {
    if (write) f.write(reinterpret_cast<char*>(p), n * sizeof(T));
    else f.read(reinterpret_cast<char*>(p), n * sizeof(T));
    if (!f) throw std::runtime_error("dataset read/write failed");
}
void dataset(Data& d, const std::string& path, bool write) {
    std::fstream f(path, std::ios::binary | (write ? std::ios::out : std::ios::in));
    transfer(f, &d.n, 1, write); transfer(f, &d.nq, 1, write); transfer(f, &d.dim, 1, write);
    if (!write && (d.n < K || d.n > 1000000 || !d.nq || d.nq > 100000 || !d.dim || d.dim > 4096))
        throw std::runtime_error("invalid dataset dimensions");
    d.base.resize(d.n * d.dim); d.queries.resize(d.nq * d.dim); d.truth.resize(d.nq * K);
    transfer(f, d.base.data(), d.base.size(), write);
    transfer(f, d.queries.data(), d.queries.size(), write);
    transfer(f, d.truth.data(), d.truth.size(), write);
}
int main(int argc, char** argv) try {
    if (argc < 3) throw std::runtime_error("usage: smoke prepare|run directory [label]");
    const std::string mode = argv[1], dir = argv[2];
    std::filesystem::create_directories(dir);
    Data d{};
    if (mode == "prepare") {
        d.n = 20000; d.nq = 300; d.dim = 128;
        d.base.resize(d.n * d.dim); d.queries.resize(d.nq * d.dim); d.truth.resize(d.nq * K);
        std::mt19937 rng(20261109);
        std::uniform_real_distribution<float> uniform(0.0f, 1.0f);
        for (auto& v : d.base) v = uniform(rng);
        for (auto& v : d.queries) v = uniform(rng);
        hnswlib::L2Space space(d.dim);
        auto distance = space.get_dist_func();
        for (size_t q = 0; q < d.nq; ++q) {
            std::vector<std::pair<float, uint32_t>> all;
            all.reserve(d.n);
            for (size_t i = 0; i < d.n; ++i)
                all.emplace_back(distance(d.queries.data()+q*d.dim, d.base.data()+i*d.dim,
                                          space.get_dist_func_param()), i);
            std::partial_sort(all.begin(), all.begin()+K, all.end());
            for (size_t j = 0; j < K; ++j) d.truth[q*K+j] = all[j].second;
        }
        dataset(d, dir + "/synthetic.bin", true);
        hnswlib::HierarchicalNSW<float> index(&space, d.n, 16, 200, 100);
        for (size_t i = 0; i < d.n; ++i) index.addPoint(d.base.data()+i*d.dim, i);
        index.saveIndex(dir + "/shared.hnsw");
        std::cout << "Prepared independent synthetic queries, exact top-10, shared index: "
                  << d.n << " x " << d.dim << ", queries=" << d.nq << '\n';
        return 0;
    }
    if (mode != "run" || argc != 4) throw std::runtime_error("run requires a label");
    const std::string label = argv[3];
    dataset(d, dir + "/synthetic.bin", false);
    hnswlib::L2Space space(d.dim);
    hnswlib::HierarchicalNSW<float> index(&space, dir + "/shared.hnsw");
    std::cout << "variant,ef,repeat,n,nq,dim,recall_at_10,qps,mean_us,p50_us,p95_us\n";
    for (size_t ef : {32, 64, 128}) {
        index.setEf(ef);
        for (size_t q = 0; q < d.nq; ++q) index.searchKnn(d.queries.data()+q*d.dim, K);
        std::vector<uint32_t> first_ids;
        for (int rep = 0; rep < 3; ++rep) {
            std::vector<double> us;
            size_t hits = 0;
            for (size_t q = 0; q < d.nq; ++q) {
                const auto begin = Clock::now();
                auto result = index.searchKnn(d.queries.data()+q*d.dim, K);
                const auto end = Clock::now();
                us.push_back(std::chrono::duration<double, std::micro>(end-begin).count());
                if (result.size() != K) throw std::runtime_error("incorrect result count");
                std::vector<uint32_t> ids;
                while (!result.empty()) { ids.push_back(result.top().second); result.pop(); }
                std::sort(ids.begin(), ids.end());
                if (rep == 0) first_ids.insert(first_ids.end(), ids.begin(), ids.end());
                for (auto id : ids)
                    hits += std::find(d.truth.begin()+q*K, d.truth.begin()+(q+1)*K, id)
                            != d.truth.begin()+(q+1)*K;
            }
            double total = 0; for (double t : us) total += t;
            std::sort(us.begin(), us.end());
            std::cout << label << ',' << ef << ',' << rep << ',' << d.n << ',' << d.nq << ','
                      << d.dim << ',' << std::setprecision(9) << double(hits)/(d.nq*K) << ','
                      << d.nq*1e6/total << ',' << total/d.nq << ',' << us[d.nq/2] << ','
                      << us[std::min(d.nq-1, size_t(d.nq*0.95))] << '\n';
        }
        std::ofstream ids(dir + "/" + label + "_ef" + std::to_string(ef) + ".ids", std::ios::binary);
        ids.write(reinterpret_cast<const char*>(first_ids.data()), first_ids.size()*sizeof(uint32_t));
        if (!ids) throw std::runtime_error("result IDs write failed");
    }
    return 0;
} catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
