# VSAG 主线论文目录

更新：2026-11-09。当前本地共有 11 篇研究、11 份 PDF。按实际阅读用途整理，论文编号保持不变，原始 PDF 内容未修改。

| 目录 | 数量 | 定位 |
| --- | --- | --- |
| [core](core/) | 2 | VSAG 主线与 KBest 硬件方法参考 |
| [related](related/) | 6 | 布局、评测、实验控制与相邻方法 |
| [archive/numa](archive/numa/) | 3 | 已放弃方向的背景原文，不进入近期阅读队列 |

## 近期优先阅读


| 编号 | 本地论文 | 本地版本 | 阅读任务 |
| --- | --- | --- | --- |
| C5 | [VSAG: An Optimized Search Framework for Graph-based Approximate Nearest Neighbor Search](core/2025_VSAG_Optimized_Search_Framework_for_Graph_Based_ANNS_PVLDB.pdf) | PVLDB 18(12), 2025 正式版，14 页 | 主线：§3、算法 1、§4.2、§6.4；对应实际搜索和存储代码 |
| C2 | [KBest: Efficient Vector Search on Kunpeng CPU](core/2026_KBest_Efficient_Vector_Search_on_Kunpeng_CPU_arxiv2508.03016v2.pdf) | arXiv:2508.03016v2，2025-08-07，10 页；目录发表信息为 KDD 2026 | 方法来源：§3.1 硬件适配、§3.2 通用方法；判断向 VSAG 迁移的条件 |

## 相关工作

建议先读 C1、C6、C8；C3、C4、C7 按具体研究问题补读。

| 编号 | 本地论文 | 本地版本 | 用途 |
| --- | --- | --- | --- |
| C1 | [Graph Reordering for Cache-Efficient Near Neighbor Search](related/2022_Graph_Reordering_for_Cache_Efficient_Near_Neighbor_Search.pdf) | NeurIPS 2022 正式版，13 页；基础文献 | 布局基础：已有图重排方法与代价 |
| C6 | [Graph-Based Vector Search: An Experimental Evaluation of the State-of-the-Art](related/2025_Graph_Based_Vector_Search_Experimental_Evaluation_SIGMOD.pdf) | SIGMOD/PACMMOD 2025 正式排版，31 页 | 实验设计：基线、参数、规模和公平比较 |
| C8 | [The Impacts of Data, Ordering, and Intrinsic Dimensionality on Recall in Hierarchical Navigable Small Worlds](related/2024_HNSW_Data_Ordering_Intrinsic_Dimensionality_Recall_arxiv2405.17813v1.pdf) | arXiv:2405.17813v1，15 页；ICTIR 2024 相关版本 | 质量控制：插入顺序、数据与召回 |
| C3 | [SymphonyQG: Towards Symphonious Integration of Quantization and Graph for Approximate Nearest Neighbor Search](related/2025_SymphonyQG_arxiv2411.12229v1.pdf) | arXiv:2411.12229v1，17 页；SIGMOD 2025 接收信息 | 相邻背景：量化、紧凑布局和批量计算协同 |
| C4 | [Distance Comparison Operation Optimization in ANNS: A Survey and Experimental Evaluation](related/2026_Distance_Comparison_Operation_Optimization_in_ANNS_EDBT.pdf) | EDBT 2026 正式版，14 页 | 综述参考：区分计算、剪枝、量化与访存 |
| C7 | [Probabilistic Routing for Graph-Based Approximate Nearest Neighbor Search](related/2024_Probabilistic_Routing_for_Graph_Based_ANNS_ICML.pdf) | ICML/PMLR 2024 正式版，19 页 | 边界参考：减少搜索工作量与改变访存安排的区别 |

## 归档背景

NUMA、CCD 调度和 CXL 不再作为独立选题。原论文放在 archive/numa，供必要时查阅；不保留对应方向讨论稿。

| 编号 | 原文 | 版本 |
| --- | --- | --- |
| N1 | [Quake: Adaptive Indexing for Vector Search](archive/numa/2025_Quake_Adaptive_Indexing_for_Vector_Search.pdf) | OSDI 2025 official proceedings PDF |
| N2 | [CCD-Level and Load-Aware Thread Orchestration for In-Memory Vector ANNS on Multi-Core CPUs](archive/numa/2026_CCD_Level_and_Load_Aware_Thread_Orchestration_arxiv2605.10090v1.pdf) | arXiv:2605.10090v1, 2026-05-11 |
| N3 | [UDON: A case for offloading to general purpose compute on CXL memory](archive/numa/2024_UDON_Offloading_to_General_Purpose_Compute_on_CXL_Memory_arxiv2404.02868v1.pdf) | arXiv:2404.02868v1, 2024-04-03 |

## 来源与完整性

[catalog.json](catalog.json) 是版本、下载来源、作者、页数、字节数和 SHA-256 的记录。此次整理前后核对全部 11 份 PDF 的哈希与字节数一致。项目 .gitattributes 将 PDF 设为 binary，防止跨系统 Git 换行转换改变原始字节。

| 编号 | 原始来源 | 代码 |
| --- | --- | --- |
| C5 | [发表或作者页面](https://www.vldb.org/pvldb/vol18/p5017-cheng.pdf) · [本地所用下载来源](https://www.vldb.org/pvldb/vol18/p5017-cheng.pdf) | [作者仓库](https://github.com/antgroup/vsag) |
| C2 | [发表或作者页面](https://arxiv.org/abs/2508.03016) · [本地所用下载来源](https://arxiv.org/pdf/2508.03016v2) | 未在目录中记录 |
| C1 | [发表或作者页面](https://papers.neurips.cc/paper_files/paper/2022/hash/fb44a668c2d4bc984e9d6ca261262cbb-Abstract-Conference.html) · [本地所用下载来源](https://www.proceedings.com/content/068/068431-2789open.pdf) | 未在目录中记录 |
| C6 | [发表或作者页面](https://arxiv.org/abs/2502.05575) · [本地所用下载来源](https://helios2.mi.parisdescartes.fr/~themisp/publications/sigmod25-gass.pdf) | [作者仓库](https://github.com/iliasazizi/GVS) |
| C8 | [发表或作者页面](https://arxiv.org/abs/2405.17813) · [本地所用下载来源](https://arxiv.org/pdf/2405.17813v1) | 未在目录中记录 |
| C3 | [发表或作者页面](https://arxiv.org/abs/2411.12229) · [本地所用下载来源](https://arxiv.org/pdf/2411.12229v1) | 未在目录中记录 |
| C4 | [发表或作者页面](https://openproceedings.org/2026/conf/edbt/paper-270.pdf) · [本地所用下载来源](https://openproceedings.org/2026/conf/edbt/paper-270.pdf) | 未在目录中记录 |
| C7 | [发表或作者页面](https://proceedings.mlr.press/v235/lu24l.html) · [本地所用下载来源](https://raw.githubusercontent.com/mlresearch/v235/main/assets/lu24l/lu24l.pdf) | [作者仓库](https://github.com/ICML2024-code/PEOs) |
| N1 | [发表或作者页面](https://www.usenix.org/conference/osdi25/presentation/mohoney) · [本地所用下载来源](https://www.usenix.org/system/files/osdi25-mohoney.pdf) | 未在目录中记录 |
| N2 | [发表或作者页面](https://arxiv.org/abs/2605.10090) · [本地所用下载来源](https://arxiv.org/pdf/2605.10090v1) | 未在目录中记录 |
| N3 | [发表或作者页面](https://arxiv.org/abs/2404.02868) · [本地所用下载来源](https://arxiv.org/pdf/2404.02868v1) | 未在目录中记录 |

C1 的 2021 年早期预印本当前不在本地；仅在 catalog.json 的 historical_versions 中保留历史来源，local_available=false，不计入本地数量。优先引用已保存的 2022 正式版。

文件名年份可能为发表年份，本地 arXiv 文件仍以具体版本号和日期为准。此前记载的发表状态并非此次重新逐项联网核验；详细引用应以出版页面和实际版本为准。

## 与实验的关系

主线已选定，具体创新点未确定。现有实验是 hnswlib 上的部分方法复现，不是完整 VSAG。VSAG 整体收益还包含量化与调参；KBest 的鲲鹏收益不能直接迁移为本机 x86 的加速结论。

研究分析见 [当前研究记录](../notes/VSAG主线_KBest迁移分析与本机复现_2026-11-09.md)，实验与迁移见 [项目 README](../README.md)。
