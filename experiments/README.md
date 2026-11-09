# 本机小规模复现

目标：跑通 hnswlib C++ 源码，部分复现 VSAG §3.2 的有效邻居筛选与步长预取。已在 AMD Ryzen 7 7735H、Ubuntu 24.04 / WSL2、GCC 13.3.0 上执行成功。不是完整 VSAG 复现，未验证 Intel 实机性能。

## 原生 Ubuntu：后续主要测量平台

优先把项目放在原生 Linux 的文件系统中，例如 `~/hnsw`；避免把 Windows 的程序二进制直接搬过来运行。Windows 共享分区可用于传输源码和结果，编译、数据与正式测量尽量放在 Linux 本地文件系统。

当前会话运行在 Windows 中，尚未进入双系统的原生 Ubuntu，也没有验证那里的编译器、内存、CPU 绑定与硬件计数器。以下是切换后的操作步骤，不表示已经执行。

在 Ubuntu 中检查：

```bash
uname -a
lscpu
free -h
g++ --version
python3 --version
```

若缺少基础工具，可以安装：

```bash
sudo apt update
sudo apt install build-essential python3 git
```

将项目复制到 `~/hnsw` 后，若 vendor/hnswlib 没有随文件一起复制，按下一节的固定版本命令获取。已有 vendor 原版目录则无需重复下载。

首先保留已有 WSL 结果，在项目根目录执行一次：

```bash
cd ~/hnsw
cp -a experiments/results experiments/results_wsl_2026-11-09
```

然后编译并运行本机实验；脚本会重新构建 Linux 程序与索引：

```bash
cd ~/hnsw/experiments
taskset -c 2 python3 run_smoke.py
```

CPU 2 只沿用小实验设置。正式实验前，应检查其物理核心和同核逻辑线程关系，确认没有同核竞争。插电、功耗模式和后台负载尽量保持稳定。

原生环境更便于直接检查 `perf`、缓存/TLB 事件与大页；这些仍取决于内核、权限和 CPU 支持，需要逐项验证。原生环境也不保证每个实现一定提速，WSL 与原生 Linux 的绝对时间必须分别记录。

## WSL：开发与快速检查

在 Windows PowerShell、项目根目录执行：

```powershell
wsl -d Ubuntu-24.04 -- bash -lc 'cd /mnt/g/hnsw/experiments && taskset -c 2 python3 run_smoke.py'
```

现有电脑已具备 g++、Python 3。脚本仅使用 Python 标准库，无需 NumPy、hnswlib Python 包或 GPU。CPU 2 是当前机器的绑定选择，换机器需调整。

hnswlib 源码固定在 v0.8.0、提交 `3f3429661187e4c24a490a0f148fc6bc89042b3d`。vendor、生成头文件、程序和数据已忽略。若重新获取项目，在根目录先执行（Ubuntu 终端也使用同一条命令）：

```bash
git clone --depth 1 --branch v0.8.0 https://github.com/nmslib/hnswlib.git experiments/vendor/hnswlib
```

每次运行重新生成实验头文件、编译三个程序、生成数据与共享索引，并覆盖 results 中的输出。需要保留旧实验时，请先复制结果。

## 三个版本

| 名称 | 内容 |
| --- | --- |
| baseline | 未修改的 hnswlib，包含原本已有的预取 |
| valid_s1_d1 | 先收集未访问邻居；提前 1 个目标、预取 1 条缓存行 |
| valid_s4_d2 | 同上；提前 4 个目标、预取 2 条缓存行 |

原版建图一次，所有版本加载同一索引。实验保留距离函数、有效邻居次序、候选更新和结束条件。只覆盖静态、无过滤、无删除、无自定义停止条件的查询。

这是论文方法的独立简化实现：没有完整 VSAG 搜索器、PRS、量化、自动调参或 KBest 算法，也不能作为新方法。

## 数据与验证

- 20,000 条 128 维 FP32 合成向量，300 条独立查询，k=10。
- 全量距离扫描计算真值；查询不是数据库中抽出的原向量。
- M=16，efConstruction=200，efSearch=32、64、128。
- 每档预热 300 次，计时 3 轮；只计搜索调用时间。
- 每个实验版本每档第一轮的全部 top-10 标签集合，与原版逐查询核对；共 6 组、1,800 次集合比较。
- 单线程固定逻辑 CPU 2，使用 `-O3 -march=native`，不强制开启 AVX-512。

结果：[smoke.csv](results/smoke.csv)；编译信息与校验证据：[metadata.json](results/metadata.json)。

小数据、合成分布、WSL 和固定顺序运行限制了计时解释。未采集缓存计数器，也未记录每轮温度功耗。当前结果用于环境与正确性验证；低召回档位不能当作达到 90% 或 95% 召回的正式结果。

## 为什么先用 hnswlib

hnswlib 是头文件库，本轮不需补装系统依赖。VSAG v0.15.0 源码已下载到 vendor/vsag 用于检查，但未编译：它需要 OpenBLAS、Boost、antlr4 等依赖，默认开启 MKL，且论文对应提交尚未确认。它不是运行本实验的依赖。

后续切换完整 VSAG 时，先确定版本与必要模块，按本机 AVX2 能力配置。不能把 v0.15.0 或最新 main 直接称作论文原始实现。

## 当前源码与产物结构

| 路径（相对 experiments） | 用途 | 是否为本人实验代码 |
| --- | --- | --- |
| `vendor/hnswlib/` | 未修改的 hnswlib v0.8.0 上游仓库 | 否，基线依赖 |
| `vendor/vsag/` | VSAG v0.15.0，上游源码与依赖检查；未完整编译 | 否，阅读参考 |
| `smoke.cpp` | 生成合成数据、精确真值、共享索引；运行查询和计时 | 是 |
| `prepare_variant.py` | 校验原版头文件，再生成实验查询循环 | 是 |
| `run_smoke.py` | 编译、运行三版本，核对标签集合，保存结果与环境信息 | 是 |
| `build/valid/hnswlib/` | 自动生成的实验头文件；变动集中在底层查询循环 | 自动生成，不手改 |
| `build/baseline`、`build/valid_s1_d1`、`build/valid_s4_d2` | 本机编译程序 | 自动生成，换环境重编 |
| `data/` | 合成数据、真值、共享索引与返回标签 | 自动生成 |
| `results/` | CSV 测量记录与 metadata.json；当前为 WSL 结果 | 需保留的实验记录 |

上游源码保持原样，本人改动由生成脚本产生；没有直接把 hnswlib 替换成 VSAG，也没有把两个系统拼成一个库。

论文对照中使用的 VSAG 最新提交片段另存于项目的 `tmp/vsag_source/`，只用于阅读，不参与编译；它与 vendor/vsag 的 v0.15.0 是不同版本。正式扩展前必须统一目标版本。`tmp/pdf_tools/`、`tmp/paper_text/` 是论文阅读辅助文件，也不是实验依赖。

版本控制保留实验代码和结果；忽略 vendor、build、data 与 tmp。重新克隆本项目不会自动获得这些忽略的文件，需要按固定版本获取上游并重跑。
