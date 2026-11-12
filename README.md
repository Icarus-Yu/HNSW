# HNSW 访存与执行优化

更新：2026-11-11。

研究主线：CPU 图检索的访存与执行优化，以 VSAG（PVLDB 2025）为核心论文，KBest 用于提取硬件优化及可迁移思想。具体改进方法和创新点仍待验证。

换系统后，接续工作的助手先阅读 [CONTINUE_HERE.md](CONTINUE_HERE.md)，再检查本机环境。正式实验使用双系统中的原生 Ubuntu 24；WSL 保留为开发与流程检查环境。

当前项目路径：`/home/hualuck7/Desktop/HNSW`。目录迁移后的 VSAG 构建与运行入口已修复，见 [迁移记录](experiments/vsag/RELOCATION_2026-11-11.md)。

## 学习记录

当前从 HNSW 基础开始，依次学习 hnswlib、2022 年图重排论文与 VSAG；每次内容和理解反馈见 [学习进度](notes/学习进度.md)。

## 当前进展

- 已在 WSL2 跑通 hnswlib 与 VSAG §3.2 部分方法：2 万条合成向量、300 条查询、3 档搜索参数。
- 两个实验版的 top-10 集合与原版一致；当前小实验没有观察到加速。
- 原生 Ubuntu 24.04.2 已完成环境检查与同规模小实验：三个迁移测试通过、27 行测量、六组结果集合一致；本次未观察到加速。VSAG v0.15.0 已独立构建并跑通两个原版例子，见 [VSAG 小规模运行](experiments/vsag/README.md)。
- 原生结果与环境记录已归档至 [results_ubuntu_2026-11-09](experiments/results_ubuntu_2026-11-09/)，详见 [初始化记录](experiments/INITIALIZATION_2026-11-09.md)。
- WSL 原始结果已单独保存在 [results_wsl_2026-11-09](experiments/results_wsl_2026-11-09/)，切换后不要覆盖该目录。

## 环境与依赖

### 当前小实验必需

| 项目 | 要求或用途 |
| --- | --- |
| 操作系统 | 原生 Ubuntu 24，当前机器为 x86_64 / AMD；实际版本需现场确认 |
| C++ 编译器 | 支持 C++17 的 g++；此前 WSL 使用 GCC 13.3.0 |
| Python | Python 3，仅使用标准库 |
| Git | 下载并核对固定版本上游源码 |
| taskset | util-linux 提供，用于绑定 CPU |
| hnswlib | v0.8.0，固定提交见下方；头文件库，无需 pip 安装 |

本轮无需 NumPy、Matplotlib、CMake、GPU、CUDA、MKL 或 pyvsag。CMake 和科学计算包按后续任务需要安装即可。

在原生 Ubuntu 安装基础工具：

```bash
sudo apt update
sudo apt install build-essential python3 git util-linux
```

检查系统、可用内存和 CPU：

```bash
uname -a
lscpu
lscpu -e=CPU,CORE,SOCKET,ONLINE
free -h
python3 --version
g++ --version
taskset -pc $$
```

### 可选：性能分析

开始缓存/TLB 分析时再安装 perf，包版本需与正在运行的内核对应：

```bash
sudo apt install linux-tools-common linux-tools-$(uname -r)
perf --version
perf stat -e cycles,instructions -- true
```

如果内核对应软件包不存在，或事件权限不足，先记录具体报错并检查内核、权限和 CPU 支持，不要自动关闭系统保护。上述命令不代表已验证所有缓存事件。

### 可选：完整 VSAG

当前小实验不依赖完整 VSAG。已下载的 v0.15.0 供阅读和依赖检查，其 Ubuntu 安装脚本列有 CMake、gfortran、Python 开发头文件、OpenMP、libaio、curl 开发库，并在 x86 默认依赖 MKL；构建还拉取 Boost、OpenBLAS、antlr4 等组件。

本机现已使用 OpenBLAS 路径构建该版本共享库，并运行 HNSW（1,000 条）与 HGraph/SQ8（10,000 条）例子；命令、依赖与构建兼容性说明见 [VSAG 运行入口](experiments/vsag/README.md)。该入口与原有 hnswlib 实验分开。v0.15.0 尚未确认是论文对应提交，例子运行不代表论文性能复现。

## 换到原生 Ubuntu 后如何运行

1. 将本项目放在 Linux 本地文件系统，例如 `~/hnsw`。普通复制可以保留整个项目；通过 Git 迁移前先确认本次文档、源码和结果均已进入你要传输的版本。
2. 至少保留实验脚本、smoke.cpp、论文、研究笔记、CONTINUE_HERE.md 和已归档 WSL 结果。vendor、build、data、tmp 被 Git 忽略，单纯 git clone 不会带上它们。
3. 若 vendor/hnswlib 缺失，在项目根目录获取固定版本；已存在则不要重复 clone：

```bash
cd ~/hnsw
git clone --depth 1 --branch v0.8.0 https://github.com/nmslib/hnswlib.git experiments/vendor/hnswlib
git -C experiments/vendor/hnswlib rev-parse HEAD
```

预期提交：`3f3429661187e4c24a490a0f148fc6bc89042b3d`。

先做跨系统源码检查，再运行小实验：

```bash
cd ~/hnsw
python3 experiments/test_prepare_variant.py
cd experiments
taskset -c 2 python3 run_smoke.py
```

CPU 2 只是原小实验的选择；运行前确认它在本机允许使用的 CPU 集合中。正式计时应核对物理核心关系，减少同核逻辑线程竞争，保持插电、功耗模式和后台负载稳定。

运行脚本会重新编译三个程序并生成数据、真值和索引，无需复用 WSL 二进制；会覆盖 experiments/results 下的输出。Linux/Windows 换行符已经兼容，实际源码改动仍会被校验拒绝。原生结果保存到 results，WSL 历史结果保留在独立归档目录，两者分开解读。

预期完成：三个程序编译成功、输出 27 行测量数据、六组 top-10 集合检查通过。性能是否改善必须依据新结果，不能把之前 WSL 的时间当作原生结果。

## 资料与源码结构

| 目录或文件 | 内容 |
| --- | --- |
| [CONTINUE_HERE.md](CONTINUE_HERE.md) | 接续助手的上下文、已确认决定、版本和下一步 |
| [experiments/README.md](experiments/README.md) | 代码布局、运行产物、验证口径与限制 |
| [notes](notes/) | 主线研究记录与访存基础，共 2 份文档 |
| [papers/README.md](papers/README.md) | 按主线、相关工作、归档背景整理的 11 篇论文 |
| [thesis_documents](thesis_documents/) | 任务书与开题报告模板 |
| [notices](notices/)、[templates](templates/)、[reference_materials](reference_materials/) | 学校要求、格式与参考材料 |

研究细节见 [当前研究记录](notes/VSAG主线_KBest迁移分析与本机复现_2026-11-09.md) 和 [访存基础](notes/HNSW_Cache优化方向与实验条件_2026-11-08.md)。已放弃 NUMA、SSD 独立选题，不再维护多方向讨论稿。
