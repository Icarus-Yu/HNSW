# VSAG 原版小规模运行

本目录是完整 VSAG 源码构建与原版 API 小例子的入口；与上一层基于 hnswlib 的部分方法实验分开。

## 版本与范围

固定 VSAG v0.15.0，提交 `295acf3c5e1b202bd414ef42f11b9d741aefdd6a`。该版本尚未确认是 PVLDB 论文实验对应版本。本轮不修改搜索算法。

运行上游两个例子：

| 例子 | 数据量 | 维度 | 表示 | 查询 |
| --- | --- | --- | --- | --- |
| `101_index_hnsw` | 1,000 | 128 | FP32 | 独立生成的 1 条，top-10 |
| `103_index_hgraph` | 10,000 | 128 | SQ8 | 独立生成的 1 条，top-10 |

数据由例子在内存中生成，随机种子 47，不下载数据集。这里只检查构建、建图、查询和基本输出有效性，不验证精确真值，不报告 Recall/QPS，不将两种索引直接作为消融对照。

## 目录安排

| 路径（相对于项目根目录） | 内容 | Git |
| --- | --- | --- |
| `experiments/vendor/vsag/` | 固定版本上游源码 | 忽略；迁移时需重新下载 |
| `experiments/build/vsag/` | CMake、第三方依赖源码及库、程序、日志 | 忽略；可重建 |
| `experiments/build/vsag/install/` | 项目内安装前缀，避免安装到系统目录 | 忽略 |
| `experiments/vsag/build.sh` | 固定参数的构建入口 | 保留 |
| `experiments/vsag/run_examples.py` | 执行原例子并检查结果 | 保留 |
| `experiments/vsag/results/<时间>/` | 每次独立保存 stdout、stderr、metadata | 保留 |

旧 `experiments/results*` 继续属于 hnswlib 实验，互不覆盖。`PLAN.md` 记录本轮工作与验收。

## 依赖和构建

Ubuntu 24.04，GCC 13.3，CMake 3.28.3，Python 3.12（仅标准库）。系统依赖：

```bash
sudo apt-get install -y --no-install-recommends build-essential cmake python3 git gfortran libaio-dev libcurl4-openssl-dev
```

GCC 使用 libgomp OpenMP 运行库；本轮使用 OpenBLAS，不需要 Intel MKL、GPU、CUDA 或 pyvsag。OpenBLAS、Boost、antlr4、spdlog 等由上游 CMake 下载并构建，需要网络。关闭完整测试、工具和 Python 绑定，但上游配置仍会获取部分测试相关第三方库。

源码缺失时，从项目根目录运行：

```bash
git clone --depth 1 --branch v0.15.0 https://github.com/antgroup/vsag.git experiments/vendor/vsag
git -C experiments/vendor/vsag rev-parse HEAD
```

构建与运行（从项目根目录）：

```bash
bash experiments/vsag/build.sh
taskset -c 2 python3 experiments/vsag/run_examples.py
```

CPU 2 必须在当前允许集合中。运行脚本限制 OpenMP/OpenBLAS 环境线程数为 1，但没有声称整个 VSAG 内部线程池只有一个线程；本轮不作计时比较。主构建以及支持 `NUM_BUILDING_JOBS` 的第三方构建使用两路；上游 spdlog 子构建硬编码为四路（本轮保留原配置）；保留上游默认多指令集编译，运行时按 CPU 能力分发（本机支持 AVX2，不支持 AVX-512）。OpenBLAS 内部 make 会按检测到的核心数继续展开并行任务，不能将顶层两路视为全局进程上限。

构建失败时查看 `experiments/build/vsag/logs/` 及各第三方目录内的 `*-stamp/*-*.log`。下载超时应先核对具体 URL 和日志；不要直接更换上游版本。重复运行构建脚本可利用已完成产物。

结果校验：两个进程退出成功；索引数量正确；各返回 10 个不重复且范围正确的标签；L2 距离为有限非负数并按升序排列。`metadata.json` 中的 wall time 包括数据生成、建图和查询，不能当作查询延迟。查询准确性和论文机制消融属于后续阶段。

## 当前状态

2026-11-09：依赖安装、完整 `vsag` 共享库和两个目标例子编译成功；绑定 CPU 2 运行两个例子，全部基本结果检查通过。上游源码工作区干净，动态库无缺失。构建目录约 6.1 GiB（包含依赖、调试信息和缓存）。

[本次原始结果与环境](results/20261109_235756_065698/) 包含 stdout、stderr、metadata、系统包版本和构建选项。完整单元测试尚未运行，查询召回率与论文消融尚未测量。

## 已定位的构建兼容性问题

首次配置强制关闭 AVX-512，但保留 AVX2，在 `src/simd/avx512.cpp` 的 `FP32ComputeL2SqrBatch4` 中出现 `__m512` 未声明错误。该函数内 AVX-512 指令块被 `ENABLE_AVX2` 而不是 `ENABLE_AVX512` 保护；邻近函数使用的是后者。

本轮选择恢复上游默认多指令集编译，不修改算法或 vendor 文件。编译 AVX-512 内核不等于运行 AVX-512；`src/simd/simd.cpp` 使用 cpuinfo 检查 CPU，`src/simd/fp32_simd.cpp` 按支持情况选择函数。最终须用本机实际运行验证。首次失败日志保留为 `experiments/build/vsag/logs/build-avx512-disabled.log`。
