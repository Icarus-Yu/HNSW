# VSAG 原版小规模运行计划

目标：在原生 Ubuntu 上补齐依赖，构建固定版本 VSAG，运行原版 HNSW/HGraph 小例子，为论文阅读建立可运行入口。

结构：上游源码留在 `experiments/vendor/vsag`；生成内容留在 `experiments/build/vsag`；受版本管理的入口和说明放在 `experiments/vsag`；结果按运行时间放在 `experiments/vsag/results`。

技术：VSAG v0.15.0，提交 295acf3c5e1b202bd414ef42f11b9d741aefdd6a；GCC 13/C++17；CMake；OpenBLAS；主构建两路编译（上游 spdlog 子构建硬编码四路）；保留默认 SIMD 分发，关闭 Python 绑定和全量测试/工具。

- [x] 安装并核对 gfortran、libaio-dev 等系统依赖；用户在终端完成 sudo 身份验证。
- [x] 配置和构建原版 `101_index_hnsw`、`103_index_hgraph`，保留失败日志，修复仅限构建兼容性问题并记录。
- [x] 运行 1,000 条 HNSW、10,000 条 HGraph 原例子，检查建图数量、top-10 数量、标签范围和距离有效性，记录版本、配置、运行日志。
- [x] 更新根目录接续文档及本目录说明，核对上游工作区与 Git diff。

验证边界：原例子只有单查询，本轮是 API/构建流程检查，不是 Recall/QPS 评测，更不代表论文消融复现。v0.15.0 尚未确认是论文实验版本。旧 hnswlib 实验与 WSL 归档不改动。

构建决定：强制关闭 AVX-512 触发已定位的上游预处理条件错误；恢复默认多指令集编译，并在实际 CPU 上验证分发。保留 vendor 原样，不将兼容性配置调整称为算法改进。
