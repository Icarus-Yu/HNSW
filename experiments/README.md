# 本机部分方法复现

目的：以 hnswlib 为基础，独立简化复现 VSAG §3.2 的有效邻居筛选与步长预取。环境配置、依赖和原生 Ubuntu 运行命令见 [项目 README](../README.md)。接续助手先读 [CONTINUE_HERE.md](../CONTINUE_HERE.md)。

## 代码与目录

| 路径 | 内容 |
| --- | --- |
| `vendor/hnswlib/` | 未修改的 v0.8.0 上游仓库，实验基线 |
| `vendor/vsag/` | v0.15.0，已独立构建共享库与两个原例子；不是本 hnswlib 实验依赖 |
| [smoke.cpp](smoke.cpp) | 合成数据、精确真值、共享索引、查询与计时 |
| [prepare_variant.py](prepare_variant.py) | 校验上游源码，生成修改底层查询循环的实验头文件 |
| [test_prepare_variant.py](test_prepare_variant.py) | LF、CRLF 两种源码换行符与实际修改拒绝的迁移检查 |
| [run_smoke.py](run_smoke.py) | 编译三版本、运行、核对标签、记录结果与环境 |
| `build/valid/hnswlib/` | 自动生成的实验头文件，不手工修改 |
| `build/` | 三个本机程序：baseline、valid_s1_d1、valid_s4_d2 |
| `data/` | 合成向量、精确真值、共享索引与返回标签 |
| `results/` | 最近一次运行的 CSV 与 metadata.json，会被下次运行覆盖 |
| [results_wsl_2026-11-09](results_wsl_2026-11-09/) | 单独保留的 WSL 历史记录，后续不覆盖 |

Git 忽略 vendor、build、data、tmp；实验脚本和结果归档不在这些忽略规则中。是否已提交，以实际 git status 为准。

`tmp/vsag_source/` 中是另一份最新提交的阅读片段，与 vendor/vsag 不同，不参与编译，也不是迁移必需文件。

## 版本和生成方式

hnswlib v0.8.0，提交 `3f3429661187e4c24a490a0f148fc6bc89042b3d`。原版仓库保持原样，实验头文件由脚本生成。

校验 hnswalg.h 时先统一为 LF，再计算 SHA-256：`0fb2c1b1d3aae1ea959b536f96844f3f3ae6a2f32ce063f2c31f93d84a7e5c32`。只消除 Windows/Linux 换行差异，其他源码差异仍被拒绝。

## 三个版本

| 名称 | 内容 |
| --- | --- |
| baseline | 未修改的 hnswlib，包含其已有预取 |
| valid_s1_d1 | 先收集未访问邻居；提前 1 个目标，预取 1 条缓存行 |
| valid_s4_d2 | 同上；提前 4 个目标，预取 2 条缓存行 |

保留距离函数、有效邻居顺序、队列更新与结束条件。只验证静态、无过滤、无删除、标准停止条件的路径。生成头文件中的 assert 在 -DNDEBUG 下不生效，因此不能将其误当作运行时的通用输入保护。

这不是完整 VSAG，不包含 PRS、量化、自动调参或 KBest 图算法，也不是已经验证的新方法。

## 数据、计时和正确性

- 20,000 条 128 维 FP32 合成向量、300 条独立查询、k=10；全量距离扫描计算真值。
- 原版仅构建一次索引，三版本加载同一文件；M=16、efConstruction=200，固定随机种子。
- efSearch=32、64、128；每档预热 300 次，再计时 3 轮，单线程。
- QPS 按搜索调用耗时计算，不包含建图、读盘、真值核对和服务开销。
- 每个实验版每档第一轮的 top-10 标签集合与原版逐查询比较；六组、共 1,800 次集合比较。
- 本轮没有采集缓存事件、温度功耗或实际距离计算次数；不能仅凭同结果断言全部内部工作量相同。

## 已完成的 WSL 结果

原始记录：[smoke.csv](results_wsl_2026-11-09/smoke.csv)，环境与索引哈希：[metadata.json](results_wsl_2026-11-09/metadata.json)。

此前在 AMD Ryzen 7 7735H、Ubuntu 24.04 / WSL2、GCC 13.3.0 下完成；六组结果检查一致，没有观察到加速。小合成数据、固定运行顺序与 WSL 限制了性能解释，不是正式真实数据评测。

原生 Ubuntu 已于 2026-11-09 完成同规模小实验，27 行测量与六组结果集合检查通过，本次未观察到加速。结果保存于 [results_ubuntu_2026-11-09](results_ubuntu_2026-11-09/)，环境与限制见 [初始化记录](INITIALIZATION_2026-11-09.md)。后续再考虑 SIFT1M 和硬件事件。WSL 与原生测量单独保留，不混为同一组结果。

## 独立 VSAG 源码运行入口

[vsag/README.md](vsag/README.md) 记录完整 VSAG 库构建与原版小例子运行；上游源码、构建产物、结果分别放置，旧 hnswlib 输出不被覆盖。此入口尚未进行论文方法消融。
