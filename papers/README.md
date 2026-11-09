# Cache 与 NUMA 论文目录

收集日期：2026-11-08；2026-11-09 补充 C1 的正式版及 C5–C8 四篇近期材料，选定 C5（VSAG）为方向 A 的近期核心参考。用于配合当天的 [Cache 讨论记录](../notes/HNSW_Cache优化方向与实验条件_2026-11-08.md) 和 [NUMA 讨论记录](../notes/HNSW_NUMA优化方向与论文依据_2026-11-08.md)。

## 收录范围与版本原则

- 近期材料按 2024–2026 年筛选，共 10 篇，涵盖正式会议材料和作者预印本。
- 另收录图重排基础研究的 NeurIPS 2022 正式版，并保留 2021 年早期预印本；共 11 篇研究、12 份 PDF。两版本不可按相同版本引用。
- Cache 类放在 `cache/`，NUMA 与拓扑感知并发类放在 `numa/`。分类表示与本课题的关系，不表示所有论文都研究纯 Cache 优化或纯 NUMA 优化。
- 文件名中的主年份通常为发表或接收年份；带 arXiv 标识的文件另标明具体版本。C1 的正式版与早期预印本分别按 2022、2021 年命名。
- 原始 PDF 未做内容修改。文件完整性、页数和首页已核对；关联说明依据原文摘要及相关章节，不代表已完成逐篇精读或实验复现。
- [catalog.json](catalog.json) 记录作者、发表信息、实际下载 URL、版本、下载日期、页数、字节数和 SHA-256，便于后续追溯。

## Cache 与 CPU 图检索相关工作：8 篇研究、9 份 PDF

| 编号 | 论文与本地文件 | 发表信息与实际下载版本 | 相关性 |
| --- | --- | --- | --- |
| C1 | [Graph Reordering for Cache-Efficient Near Neighbor Search：2022 正式版](cache/2022_Graph_Reordering_for_Cache_Efficient_Near_Neighbor_Search.pdf)；[2021 早期预印本](cache/2021_Graph_Reordering_for_Cache_Efficient_Near_Neighbor_Search_arxiv2104.03221v1.pdf) | NeurIPS 2022 正式版，13 页，38488–38500 页；另保留 arXiv:2104.03221v1，11 页 | 图重排基础；明确属于近三年范围外的补充 |
| C2 | [KBest: Efficient Vector Search on Kunpeng CPU](cache/2026_KBest_Efficient_Vector_Search_on_Kunpeng_CPU_arxiv2508.03016v2.pdf) | arXiv 页面列 ACM KDD 2026；本地：arXiv:2508.03016v2，2025-08-07，10 页 | 硬件感知 CPU 检索、预取和 SIMD；鲲鹏 ARM 平台 |
| C3 | [SymphonyQG: Towards Symphonious Integration of Quantization and Graph for Approximate Nearest Neighbor Search](cache/2025_SymphonyQG_arxiv2411.12229v1.pdf) | arXiv 页面说明 SIGMOD 2025 接收；本地：arXiv:2411.12229v1，2024-11-19，17 页 | 量化、紧凑组织、批量计算协同的相邻路线，非简单 HNSW 缓存补丁 |
| C4 | [Distance Comparison Operation Optimization in ANNS: A Survey and Experimental Evaluation](cache/2026_Distance_Comparison_Operation_Optimization_in_ANNS_EDBT.pdf) | EDBT 2026，正式 PDF，14 页 | 距离比较优化综述与评测；用于区分计算、剪枝、量化与内存代价 |
| C5 | [VSAG: An Optimized Search Framework for Graph-based Approximate Nearest Neighbor Search](cache/2025_VSAG_Optimized_Search_Framework_for_Graph_Based_ANNS_PVLDB.pdf) | PVLDB 18(12)，2025，正式 PDF，14 页 | 近期核心：第 3 节访存优化；涉及量化的其他模块不作为新增独立方向 |
| C6 | [Graph-Based Vector Search: An Experimental Evaluation of the State-of-the-Art](cache/2025_Graph_Based_Vector_Search_Experimental_Evaluation_SIGMOD.pdf) | SIGMOD / PACMMOD 3(1)，Article 43，2025，作者公开正式排版 PDF，31 页 | 评测与基线选择参考；不是纯缓存方法 |
| C7 | [Probabilistic Routing for Graph-Based Approximate Nearest Neighbor Search](cache/2024_Probabilistic_Routing_for_Graph_Based_ANNS_ICML.pdf) | ICML 2024，PMLR 235，正式 PDF，19 页 | 概率路由与候选筛选；区分减少搜索工作量和改善同等工作量访存 |
| C8 | [The Impacts of Data, Ordering, and Intrinsic Dimensionality on Recall in Hierarchical Navigable Small Worlds](cache/2024_HNSW_Data_Ordering_Intrinsic_Dimensionality_Recall_arxiv2405.17813v1.pdf) | ICTIR 2024；本地 arXiv:2405.17813v1，15 页，作者预印本 | 插入顺序、数据与召回的实验控制参考；不是建图后物理重排 |

来源与版本核对入口：

1. C1：[2021 年预印本](https://arxiv.org/abs/2104.03221)、[2022 年正式页面](https://papers.neurips.cc/paper_files/paper/2022/hash/fb44a668c2d4bc984e9d6ca261262cbb-Abstract-Conference.html)、[正式 PDF 在线链接](https://papers.neurips.cc/paper_files/paper/2022/file/fb44a668c2d4bc984e9d6ca261262cbb-Paper-Conference.pdf)。NeurIPS 域名本机下载曾发生 TLS 传输错误；2026-11-09 已通过 [Proceedings.com 下载入口](https://www.proceedings.com/content/068/068431-2789open.pdf) 保存 13 页正式版并核对首页。后续精读和引用优先使用本地正式版；早期预印本仍保留供版本对照。
2. C2：[作者页面](https://arxiv.org/abs/2508.03016)、[实际下载 v2](https://arxiv.org/pdf/2508.03016v2)。不能把 ARM 平台收益直接套用到本机 AMD CPU。
3. C3：[作者页面](https://arxiv.org/abs/2411.12229)、[实际下载 v1](https://arxiv.org/pdf/2411.12229v1)。
4. C4：[OpenProceedings 原文](https://openproceedings.org/2026/conf/edbt/paper-270.pdf)。
5. C5：[正式原文](https://www.vldb.org/pvldb/vol18/p5017-cheng.pdf)、[作者代码](https://github.com/antgroup/vsag)。
6. C6：[作者原文](https://helios2.mi.parisdescartes.fr/~themisp/publications/sigmod25-gass.pdf)、[作者代码](https://github.com/iliasazizi/GVS)。
7. C7：[正式原文](https://raw.githubusercontent.com/mlresearch/v235/main/assets/lu24l/lu24l.pdf)、[作者代码](https://github.com/ICML2024-code/PEOs)。
8. C8：[作者原文](https://arxiv.org/pdf/2405.17813v1)。

当前阅读顺序：C5（VSAG）第 3 节作为近期核心；C1 保留为布局基础；C2 比较跨平台访存与执行组织；C6 用于实验设计；C8 控制建图与质量差异；C7 用于划清搜索策略与访存优化的边界。C3、C4 为相邻背景，删除量化候选方向不等于删除相关工作文献。N2 属于当前方向 B 的拓扑调度，可交叉阅读。

C5 的核心参考地位只表示当前优先精读和建立方法对照，不表示已选定改进方法或已复现。其总体结果包含量化和调参等模块，不能作为纯访存收益；论文对应代码版本、依赖与复现条件仍待核对。专题选择理由见 [Cache 笔记第 8.1 节](../notes/HNSW_Cache优化方向与实验条件_2026-11-08.md#81-方向-a-的近期核心参考vsag)。

论文编号 C1–C8、N1–N3 用于目录追溯，与研究方向 A/B/C 是不同编号体系。

## NUMA 与拓扑感知并发：3 份

| 编号 | 论文与本地文件 | 发表信息与实际下载版本 | 相关性与边界 |
| --- | --- | --- | --- |
| N1 | [Quake: Adaptive Indexing for Vector Search](numa/2025_Quake_Adaptive_Indexing_for_Vector_Search.pdf) | OSDI 2025，153–169 页；正式会议 PDF，含封面共 18 页 | 直接向量检索：NUMA 分区放置和查询内并行；采用分区式索引，不是 HNSW |
| N2 | [CCD-Level and Load-Aware Thread Orchestration for In-Memory Vector ANNS on Multi-Core CPUs](numa/2026_CCD_Level_and_Load_Aware_Thread_Orchestration_arxiv2605.10090v1.pdf) | arXiv 页面说明 ICDE 2026 接收；本地：arXiv:2605.10090v1，2026-05-11，14 页 | 直接涉及 HNSW 查询间并行与缓存域调度；CCD 不是 NUMA 内存节点的同义词 |
| N3 | [UDON: A case for offloading to general purpose compute on CXL memory](numa/2024_UDON_Offloading_to_General_Purpose_Compute_on_CXL_Memory_arxiv2404.02868v1.pdf) | arXiv 页面说明在 HCDS 2024 展示；本地：arXiv:2404.02868v1，2024-04-03，5 页 | 涉及 HNSW 的相邻研究：双路 ARM NUMA 模拟 CXL 近内存计算 |

来源与版本核对入口：

1. N1：[USENIX 正式页面](https://www.usenix.org/conference/osdi25/presentation/mohoney)、[实际下载正式 PDF](https://www.usenix.org/system/files/osdi25-mohoney.pdf)、[作者实验代码](https://github.com/marius-team/quake/tree/osdi2025/test/experiments/osdi2025)。
2. N2：[作者页面](https://arxiv.org/abs/2605.10090)、[实际下载 v1](https://arxiv.org/pdf/2605.10090v1)。它是本次整理新增的近期材料，相关工作对照应重点阅读。
3. N3：[作者页面](https://arxiv.org/abs/2404.02868)、[实际下载 v1](https://arxiv.org/pdf/2404.02868v1)。其模拟平台、卸载机制和收益不等于普通 NUMA 优化结论。

建议顺序：N1 理解数据放置与计算位置的配合；N2 看 HNSW 并发、缓存域与负载均衡已有方案；N3 扩展对远端内存与计算靠近数据的认识。当前不将选择性复制、队列或调度设想直接标成创新点。

## 早期背景资料

2014 年 Morsel-Driven Parallelism 和 ICDE 2020 NUMA 查询处理系统分析仅在 [NUMA 笔记](../notes/HNSW_NUMA优化方向与论文依据_2026-11-08.md#51-更早的方法论背景仅保留链接) 中保留来源链接，未纳入本次近期 PDF 集合。
