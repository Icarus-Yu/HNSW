# 原生 Ubuntu 初始化记录

日期：2026-11-09（Asia/Shanghai）。

- 项目路径：`/home/hualuck7/桌面/Myproject/HNSW`。
- Ubuntu 24.04.2 LTS，内核 6.11.0-29-generic，x86_64；AMD Ryzen 7 7735H，8 核 16 线程，系统内存约 14 GiB，检查时可用约 5.4 GiB。
- GCC 13.3.0、Python 3.12.3、Git、taskset 已可用，无需安装系统包。
- hnswlib v0.8.0 已下载，提交为 `3f3429661187e4c24a490a0f148fc6bc89042b3d`，上游工作区干净。
- `python3 experiments/test_prepare_variant.py`：三个测试通过。
- `taskset -c 2 python3 experiments/run_smoke.py`：三版本编译成功，27 行测量，六组共 1,800 次 top-10 集合核对通过。CPU 2 与 CPU 3 共享物理核心；未控制后台负载、功耗或温度。

三轮平均查询耗时的中位数（微秒）：

| efSearch | baseline | valid_s1_d1 | valid_s4_d2 |
| --- | --- | --- | --- |
| 32 | 43.77 | 90.09 | 73.05 |
| 64 | 94.00 | 151.76 | 152.36 |
| 128 | 167.10 | 314.29 | 238.49 |

本次未观察到加速。这是小规模合成数据的流程验证，不能据此判断普遍性能或解释变慢原因。

原始结果：[原生归档](results_ubuntu_2026-11-09/)，其中 `environment.txt` 记录环境，`metadata.json` 记录编译选项、索引哈希和正确性检查。`results/` 为本次结果，可被下次运行覆盖。原生独立归档和 WSL 历史归档应保留；WSL 归档已与 Git HEAD 逐字节核对一致。

本记录对应最初的 hnswlib 初始化。后续同日已构建 VSAG 库并跑通两个原版例子，见 [VSAG 运行说明](vsag/README.md)。perf 已确认存在，版本 6.11.11，尚未检查硬件事件权限；未下载真实数据。
