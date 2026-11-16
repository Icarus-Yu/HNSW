# VSAG 论文问题、源码对照与实验复现

整理于 2026-11-16。以 VSAG 原版 HGraph/SQ8 示例为实验主线，用 2022 年图重排和 KBest 对照它的取数、计算和搜索策略。

## 先回答 SQ8 属于哪类改进

**SQ8 属于 VSAG 第三类改进「加速距离计算」里的标量量化，对应 §5.2。** 它把每一维用 8 位编码近似表示，也会减少搜索时读取的向量字节。第三类改进还包括 SIMD、距离公式拆解和选择性复算。

**PRS 属于第一类访存改进，对应 §3.3，决定是否在节点旁额外存放邻居向量的压缩副本。** 一份副本可以用量化编码节省空间。是否启用副本仍是单独的设置与验证问题。

## 1. 阅读材料与版本

| 材料 | 这份笔记用它回答什么 |
| --- | --- |
| [2022 年 Graph Reordering 正式版](../papers/related/2022_Graph_Reordering_for_Cache_Efficient_Near_Neighbor_Search.pdf) | 同一张图，改变节点存放位置能否减少缓存未命中、缩短查询时间。重点为 §3–4.1 和 §5–7。 |
| [VSAG PVLDB 正式版](../papers/core/2025_VSAG_Optimized_Search_Framework_for_Graph_Based_ANNS_PVLDB.pdf) | 访存、自动调参、距离计算三类改进。重点为图 1、§3–5、§6 和 §7。 |
| [KBest arXiv v2](../papers/core/2026_KBest_Efficient_Vector_Search_on_Kunpeng_CPU_arxiv2508.03016v2.pdf) | 鲲鹏 920 的批量计算与取数安排、图精化、重排和早停。重点为 §3.1–3.2、图 4–5、§5。 |

页码按各 PDF 阅读器显示的页数，从 1 开始。源码定位针对本地 **hnswlib v0.8.0** 和 **VSAG v0.15.0** ，优先按函数名查找，行号用于快速跳转。VSAG v0.15.0 尚未确认是论文实验对应的提交。`experiments/vendor/` 和 `experiments/build/` 由项目忽略，只有项目文件的检出可能需要先准备上游源码，才能打开本文相应的源码链接。

## 2. 从向量到查询，原来的问题出在哪一步？

### 2.1 向量、节点、索引与查询候选

一批已编码的图片或文本进入检索库，每条向量通常对应图里的一个节点。节点有供程序定位的内部编号，以及返回给调用方的外部标签。 **索引** 是整套搜索结构，包含图、向量或其编码、入口及其他辅助信息。 **邻居表** 是其中一小部分，记录从某个节点能走到哪些节点。

以本地 hnswlib 为例，插入新向量 A 时，先分配内部编号并抽出 A 的最高层，再在已有图中搜索候选、筛边、填入 A 的邻居表，随后尝试反向连边。所有节点都在底层，部分节点被抽到上层。筛边会考虑路线是否重复。例如 B 已被选中，C 离 B 比离 A 更近，连接 `A → C` 可能重复已有的搜索方向。`efConstruction` 控制建图时的候选范围，`M` 影响连边预算。

在线查询从稀疏的高层导航到底层，在底层保留一批有希望的节点。展开 A 时，先读 A 的邻居编号，检查本次查询的访问标记，再读取需要比较的邻居向量。`efSearch` 控制搜索途中同时保留的候选范围，`k` 是最终返回条数。累计检查的节点数可以超过 `efSearch`。

**原文位置。** 2022 年论文 §2，第 3–4 页的 Near Neighbor Graphs 与 Graph Structure and Graph Search，以及 VSAG §1–2、算法 1。

**源码入口。** hnswlib 的 [`hnswalg.h`](../experiments/vendor/hnswlib/hnswlib/hnswalg.h) 中，`getNeighborsByHeuristic2` 约第 443 行负责筛边，`mutuallyConnectNewElement` 约第 506 行写入连接，`addPoint` 约第 1153 行负责插入，`searchKnn` 约第 1271 行进入查询，`searchBaseLayerST` 约第 311 行执行底层搜索。

### 2.2 邻居表在哪，为什么读向量还是会跳？

本地 hnswlib 的底层记录按固定长度排列。以 `M=16`、128 维 FP32、64 位平台为例，每个底层槽位有 652 字节。

| 槽位内的位置 | 字节数 | 用途 |
| --- | ---: | --- |
| 0–3 | 4 | 邻居表头，包含实际邻居数等信息 |
| 4–131 | 128 | 32 个邻居编号槽，每个编号 4 字节，底层容量为 `2 × M` |
| 132–643 | 512 | 当前节点自己的 128 维 FP32 向量 |
| 644–651 | 8 | 当前节点的外部标签 |

如果 A 当前有 3 个邻居，表头记 3，剩下 29 个编号槽仍然预留。这样加边时不用移动 A 的向量。上层邻居表单独分配，节点有几个上层才建立对应空间。各层查询同一个节点时仍读取底层保存的那份向量。

新节点通常按插入先后分配槽位，所以 **底层记录的摆放有顺序，查询访问的槽位却可能经常跳跃** 。例如 A 的表里连续存着 `12、900、37`，读三个编号是连续的，但跟着编号去读向量，就到了三个相距较远的槽位。硬件缓存以缓存行为单位保存数据，本机一行 64 字节。512 字节的向量按 64 字节对齐时跨 8 行，起点落在行内时跨 9 行。跨几行取决于地址，发生多少次未命中则取决于读取时各行是否已经在当前缓存里。

**原文位置。** 2022 年论文 §1 图 1、§2 Cache Locality of Graphs、补充材料 §4.3，以及 VSAG §3.1 图 2。

**源码入口。** [`hnswalg.h`](../experiments/vendor/hnswlib/hnswlib/hnswalg.h) 约第 112–141 行定容量和偏移，`getDataByInternalId` 约第 202 行按「首地址 + 内部编号 × 槽位大小 + 向量偏移」找向量。`get_linklist0`、`get_linklist` 约第 486–499 行分别定位底层和上层表。`addPoint` 约第 1181–1210 行分配编号并准备节点存储。

## 3. 2022 年论文怎样解决访存问题？

**遇到的问题。** 图按向量关系连边，内存位置通常来自原有记录顺序。被同一个节点经常一起读到的 B、D，可能分散在内存两端。

**解决方法。** 先用已有 HNSW 建图，再用图的连接关系生成全局排列 P。把节点记录搬到新位置并同步更新内部编号引用和入口引用，逻辑上仍是同一张图。保持邻居访问顺序和同距离时的处理规则，有利于把计时变化归到布局本身。

| 方法或问题 | 怎么做 | 原文位置 |
| --- | --- | --- |
| Gorder | 在位置窗口内给两类点对加分，包括两点之间直接连边以及两点共享一个指向它们的节点。比如 A 同时指向 B、D，展开 A 时可能一起读 B、D。 | §3，PDF 第 4 页，式（1） |
| RCM | 尝试缩小相连节点在排列中的最大位置差。 | §3 与补充材料 |
| Corder | 在点对得分基础上，对共享同一个来源且彼此接近的三元组扣分，减少把一次加载收益重复算到多对节点上。 | §4.1，第 6 页，式（2） |
| Porder | 先运行一批查询，给经常经过的边更高权重，再用图结构和这些权重决定排列。 | §4.1，第 6–7 页，式（3），以及 §6，第 9 页 |
| 位置接近如何联系到缓存命中 | 定理 1 用同块点对和三元组约束命中数，定理 2 加入缓存边界对齐，定理 3 给出模型内新布局命中数至少持平的充分条件。 | §4，第 4–6 页，定理 1–3 |
| 实际有没有变快 | 用相同图和查询比较布局，测相同召回率下的查询时间，另外用 `perf` 和 Cachegrind 看缓存行为。 | §5–6，图 4–5、表 1 和表 3 |

**源码入口。** 项目本地保存了正式 PDF 和[中文精读](2022_图重排论文中文精读.md)。作者[补充材料与源码压缩包](https://papers.neurips.cc/paper_files/paper/2022/file/fb44a668c2d4bc984e9d6ca261262cbb-Supplemental-Conference.zip)中，`GraphReorderingSupplementary/GraphReorderingCode/flatnav/Index.h` 的 `reorder` 与 `profile_reorder` 在约第 521、547 行，邻居编号重映射在约第 309 行。参考实现 `reference_implementation/hnsw/Index.h` 的 `gorder` 在约第 809 行，边引用改写在约第 1295 行。上面是作者附件里的实现，项目的 hnswlib 实验仍使用原始节点布局。

## 4. VSAG 怎样解决问题？论文和源码在哪里？

### 4.1 VSAG 负责建表，本地 HGraph 也有上层和底层

VSAG 是库名，`hgraph` 和 `hnsw` 是本地库可选择的索引类型。`103_index_hgraph` 把原始向量交给 `Build(base)`，由 HGraph 建索引和邻居表。默认路径逐个插入并随机抽层，上层路由图较稀疏，查询从高往低走，再在底层细搜。

本地 HGraph 默认把底层邻居表和向量编码分开放，通过同一个内部编号去取。底层表存实际邻居数和预留的编号槽。原版 hnswlib 则把底层邻居表和该节点自己的向量接在同一条定长记录里。在 HGraph 示例配置中，底层最多 26 个邻居，上层每张表的上限为 13。

论文另用 Gᵢ 保存节点 i 的邻居编号，用 Lᵢ 保存一一对应的 **边标签** 。标签记录在哪个剪枝设置下可以使用这条边。HNSW 的层号决定节点参加哪个导航图，论文的边标签决定在给定阈值下是否使用某条已有边。论文的补充建图算法用一个有向图表示流程，未要求采用本地 HGraph 的分层结构。

| 问题 | 原文位置 | 本地源码位置与范围 |
| --- | --- | --- |
| 谁来建表，怎么分层 | VSAG §4.4，正式版第 7–8 页。完整的带标签建图见作者[技术报告附录 B，算法 3](https://arxiv.org/html/2503.17911v3)，含找候选、筛边、打标签和处理反向边。 | [`103_index_hgraph.cpp`](../experiments/vendor/vsag/examples/cpp/103_index_hgraph.cpp) 约第 59–62 行创建索引并调用 `Build`。[`hgraph.cpp`](../experiments/vendor/vsag/src/algorithm/hgraph.cpp) 的 `Build` 约第 137 行，`graph_add_one` 约第 1033 行，后者按层搜索并连边。[`hgraph.h`](../experiments/vendor/vsag/src/algorithm/hgraph.h) 的 `get_random_level` 约第 177 行。 |
| 如何决定邻居和写表 | 正式版算法 2 说明边标签下的剪枝，算法 1 第 6–10 行说明搜索时怎样按未访问、标签阈值和邻居上限选边。 | [`pruning_strategy.cpp`](../experiments/vendor/vsag/src/impl/pruning_strategy.cpp) 约第 23、65 行是本地默认选边和反向连接。[`graph_datacell.h`](../experiments/vendor/vsag/src/data_cell/graph_datacell.h) 约第 144–209 行是定长底层表的布局和读写。[`sparse_graph_datacell.cpp`](../experiments/vendor/vsag/src/data_cell/sparse_graph_datacell.cpp) 约第 46、91 行是稀疏上层表的读写。已核对的默认邻居存储写入邻居 ID，论文的完整边标签调参路径尚未在此示例中确认。 |
| 查询到底怎样用上层、底层和向量数据 | 正式版 §2 图 1 和 §3.2 算法 1 描述搜索的主要环节。 | [`hgraph.cpp`](../experiments/vendor/vsag/src/algorithm/hgraph.cpp) 约第 320–357 行先从高往低查路由图，再查底层。[`basic_searcher.cpp`](../experiments/vendor/vsag/src/impl/basic_searcher.cpp) 的 `visit` 约第 30 行从图表读邻居，约第 183 行把 ID 交给向量查询入口。 |

### 4.2 第一类改进 · 减少等数据的时间

| 遇到的问题 | 论文的解决方法 | 论文位置与本地代码 |
| --- | --- | --- |
| 用到某个向量时才请求，CPU 可能停下来等 | 软件预取。算当前邻居时提示 CPU 提前取后续向量，让取数和计算有机会重叠。 | §3.1，PDF 第 4 页图 2。看 [`flatten_datacell.h`](../experiments/vendor/vsag/src/data_cell/flatten_datacell.h) 的 `Query`，约第 256、276 行发出首批和后续预取。 |
| 按原表预取，可能取到已经访问过的 C | 先扫 A 的编号和访问标记，形成实际上要算的 `B、D`，再对这批目标发提示。 **步长** 是向后看几个有效目标， **深度** 是为每个目标提示取几条缓存行。 | §3.2，图 3、算法 1 第 6–17 行。看 [`basic_searcher.cpp`](../experiments/vendor/vsag/src/impl/basic_searcher.cpp) 约第 38–66、159–195 行的筛选、向量查询及部分候选堆顶预取，以及 [`flatten_datacell.h`](../experiments/vendor/vsag/src/data_cell/flatten_datacell.h) 约第 256–292 行。 |
| 多个邻居的向量一开始放得很远 | **PRS** 把选中的邻居向量压缩副本放在使用它们的节点附近。A 和 X 都可以在自己的区域存一份 B。此布局在查询使用前准备好，副本比例 δ 越高通常需要更多存储。 | §2.1 图 1、§3.3，PDF 第 5–6 页。论文描述了副本布局和比例，未明确是每个节点建表后立即复制还是统一整理。已核对的本地 HGraph `Build`、`add_one_point` 与 `GraphDataCell` 说明了默认节点编码和邻接表怎么存。论文式的 PRS 副本路径尚未在本地运行中定位或验证。 |

**时间顺序。** 先知道 A 有哪些邻居，才能准备对应副本。在线查询拿的是已有的数据。预取则在查询已经运行时，提示 CPU 把将要用的数据提前取到缓存里。

### 4.3 第二类改进 · 自动挑参数

| 遇到的问题 | 论文的解决方法与位置 | 本地源码位置与验证范围 |
| --- | --- | --- |
| 换了 CPU 或向量编码，原来的预取安排可能不合适 | §4.1–4.2。环境级参数 **ELP** 用抽样搜索评估步长、深度的参数组合。相同图和搜索规则下主要看速度。 | [`HGraph::elp_optimize`](../experiments/vendor/vsag/src/algorithm/hgraph.cpp) 约第 1174 行。本地 v0.15.0 这里注册了向量编码和访问标记的预取步长，源码还有预取深度调节的待办。原版 HGraph 示例默认关闭此入口。 |
| 同一张图上，有的查询很容易，有的要多找一会儿 | §4.3，第 6–7 页。查询级参数 **QLP** 用当前候选距离等信号判断是否能缩小候选池 ef_s。论文在 §6.6 表 7 比较固定设置和按查询调整。 | 本地 [`HGraph::KnnSearch`](../experiments/vendor/vsag/src/algorithm/hgraph.cpp) 约第 332–354 行读取 `ef_search` 并用于底层搜索。原版示例固定为 100，尚未验证论文的 GBDT 难度判断路径。 |
| 每换一次连边设置就重建图，试错耗时 | §4.4、算法 2、图 5、技术报告附录 B。索引级参数 **ILP** 先把覆盖多套设置的边和标签存好，再用阈值和邻居上限选择有效边。§6.5 与表 6 测准备和调参时间。 | [`hgraph.cpp`](../experiments/vendor/vsag/src/algorithm/hgraph.cpp) 约第 71、137、1033 行与 [`pruning_strategy.cpp`](../experiments/vendor/vsag/src/impl/pruning_strategy.cpp) 是邻居上限、默认建图和选边路径的入口。本地原版示例使用固定建图设置，未验证带标签的 ILP 自动调参。 |

### 4.4 第三类改进 · 加速距离计算，纠正量化导致的排序误差

| 遇到的问题 | 论文的解决方法与位置 | 本地源码位置与验证范围 |
| --- | --- | --- |
| 每个候选都读完整 FP32 向量，算很多分量 | §5.1–5.2，第 8–9 页。先使用量化编码减少每次读取量和低精度计算成本，再利用 SIMD 对多组分量并行运算。SQ8 是其中一种编码。 | [`sq8_quantizer.h`](../experiments/vendor/vsag/src/quantization/scalar_quantization/sq8_quantizer.h) 的 `TrainImpl`、`EncodeOneImpl`、`ComputeDistImpl` 约在第 118、139、226 行。本地示例实际用 SQ8 编码库向量，输入查询仍是 FP32。 |
| 一个查询要和很多候选比较，同样的部分被反复计算 | §5.2，第 9 页。平方欧氏距离可拆成「库向量平方和 + 查询平方和 − 2 × 点积」。库向量的平方和可预存，查询的平方和每条查询算一次，每对候选现场算点积。 | 论文公式见 Distance Decomposition。本地 SQ8 的 L2 距离入口是 [`ComputeDistImpl`](../experiments/vendor/vsag/src/quantization/scalar_quantization/sq8_quantizer.h)，约第 226 行。当前示例没有单独验证论文所述的范数预计算路径及其收益。 |
| 压缩后的距离可能把第 10、11 名排反 | §5.3，第 9 页，算法 1 第 18 行。根据误差和距离的关系选择一部分候选，用原始高精度向量复算并重排名次。候选如果根本没有进入池，最后复算无从比较它。 | [`HGraph::reorder`](../experiments/vendor/vsag/src/algorithm/hgraph.cpp) 约第 1188 行。本地版这个函数对传入候选堆的成员计算高精度距离后筛出 top-k。它可以作为复算入口阅读，尚未确认与论文的 DDC 动态选择完全对应，本地示例默认关闭重排。 |

**SQ8 的字节口径。** 128 维 FP32 向量本体为 512 字节，SQ8 编码本体为 128 字节。每维以 0–255 的编号表示一个近似档位，量化器保留每维刻度。整份索引还包含图结构、标签等数据。 **编码字节减少的比例与整份索引减少的比例、实测查询加速是三个不同的量。**

**实验原文位置。** §6.1–6.3、图 6–7 是总体和规模对照。§6.4、表 5、图 8 是逐项叠加。§6.5–6.6、表 6–7 是调参耗时和效果。§7 第 12 页线上案例中的 1.1 毫秒是 **单段平均搜索延迟** 。表 5 从基线加到量化时两组召回都略有变化，随后各数据集的召回保持不变。用相邻行读收益，并保留此前已经开启的配置。

**原文里的几处不一致。** §4.2 把更早预取和更小步长联系起来，但算法 1 用当前下标 `k` 预取 `k + ω`。按这个定义，对同一个目标，较大步长更早发出提示。图 5 与同页的 Example 6 对 `x₂`、`x₃` 的边标签写法相反。表 5 的 GIST1M 全量 PRS 是 2,377 QPS，旁边正文写 2,337。分别按算法、图的标签、表格数据核对，记录时注明采用的出处。

## 5. KBest 应该怎样和 VSAG 对照？

KBest 的底层实现使用 ARM 的 NEON 与 `PRFM`，并按鲲鹏的执行资源安排计算和读取。将思想用于本机 AMD/x86，需要用目标机器的可用指令和实际缓存参数重新测。2022 年论文与 KBest 都做了节点重排，前者主要按窗口内的边和共享邻居打分，后者用图上的最小生成树及子树大小生成排列。

| 遇到的问题 | KBest 的做法与原文 | VSAG 中的对应位置或可验证方向 |
| --- | --- | --- |
| 一个查询和多个候选比较，反复读取同一段查询 | §3.1、图 4，第 3 页。把一个查询对 B 个候选的比较成批执行，复用查询片段，分别保存每个候选的累加结果。 | 本地 [`avx2.cpp`](../experiments/vendor/vsag/src/simd/avx2.cpp) 约第 202 行已经有 FP32 四路距离内核。[`quantizer.h`](../experiments/vendor/vsag/src/quantization/quantizer.h) 约第 180 行显示部分编码若无四路实现会回退为逐个计算。先查实际索引、编码走哪条路径。 |
| 向量分散，一次预取太多还可能占满缓存 | §3.1、图 5 和式（1），第 4 页。为 L1 数据缓存保留一部分预算，用预算除以向量字节数估算批次，同时预取可能即将展开的节点。 | [`basic_searcher.cpp`](../experiments/vendor/vsag/src/impl/basic_searcher.cpp) 已有堆顶预取，[`flatten_datacell.h`](../experiments/vendor/vsag/src/data_cell/flatten_datacell.h) 已有步长、深度和四路入口。可测按真实编码字节数、当前有效邻居数安排预取批次的效果。预取批次大小与计算内核一次处理的候选数可以分别设定。 |
| 稀疏读取要频繁做地址转换，记录还可能跨额外的缓存行 | §3.1 Memory Management，第 4 页。请求大页，尝试以更少的地址转换记录覆盖相同内存。对记录做 64 字节对齐和按需补齐。 | 这两种原则可以在 Linux x86 上验证。大页需核对实际分配，并测地址转换事件。补齐会增大存储，需一起报告。当前没有相应的本地对照。 |
| 原图的搜索路线不理想 | §3.2，第 4 页。先建初始近邻图，再把两跳邻居纳入候选反复筛边。 | 可对照本地 [`pruning_strategy.cpp`](../experiments/vendor/vsag/src/impl/pruning_strategy.cpp) 的默认选边，另做同召回下的建图时间、访问节点数和距离次数比较。图精化会改变连边。 |
| 图上常一起读的记录在内存里离得远 | §3.2，第 4–5 页，算法 2。以入口为根，按子树大小引导排列。 | 可在同一张图上比较原布局、Gorder 和 KBest 树引导布局。保持逻辑边、访问顺序和预取设置，对照结果标签及搜索工作量。 |
| 后续找到的候选一直排在后面 | §3.2，第 5 页，式（3）。根据连续低排名插入次数设置早停。 | VSAG §4.3 按查询难度判断是否缩小候选池。可在相同召回目标下比较固定搜索、缩小候选池和早停。注意测漏掉的近邻与少算的距离次数。 |
| 读完整向量、计算距离成本高 | §3.2 Vector quantization，第 5 页。提供 SQ、PQ 等可替换的向量编码。 | VSAG 已实现对应类型。与预取及布局做对照时，先固定向量编码及距离函数。 |

例如本机每核 L1 数据缓存 32 KiB，若用一半做预算，按 128 维 FP32 每条 512 字节粗算，整条向量的预算约为 32 条。若当前只有 6 个待算邻居，最多只有 6 个目标。实际选择还要考虑邻居 ID、访问表和候选队列也占缓存，以及每次预取只请求了几条缓存行。这个计算用于挑测试范围，最佳设置仍由计时决定。[本机缓存记录](学习进度.md)

**源码依据。** 当前工作区的 `experiments/vendor/` 只有 hnswlib 和 VSAG。KBest 的内部实现尚无可核验的本地文件及行号，上表给的是论文算法位置与 VSAG 对照入口。鲲鹏官方更新记录注明已发布 KBest 开源代码，安装指南提供 GitCode 软件包入口，API 文档可查 `Add` 的 `reorder` 参数及 `SetEarlyStoppingParams`。这些入口能定位公开接口，项目尚未核对到与论文 v2 对应的内部源码提交。[鲲鹏官方更新记录](https://www.hikunpeng.com/document/detail/en/SRA/wtsnew/index.html) · [安装指南](https://www.hikunpeng.com/document/detail/zh/boostsra/krecall/kbest/docs/zh/kbest/installation_guide.md) · [KBest API](https://www.hikunpeng.com/document/detail/en/boostsra/krecall/kbest/docs/en/kbest/api_reference.md)

**性能口径。** KBest §5.1–5.2 用鲲鹏上的 KBest 和 AMD 上的基线对比整机吞吐，§5.3 则是在 KBest 内部逐步叠加优化。VSAG 的论文主结果使用专用单核查询评测。两篇没有在相同条件下直接对测，本地也还没有测 KBest 思路迁入 VSAG 的收益。

## 6. 已完成的实验怎么复现？结果去哪里看？

### 6.1 主实验 · 跑通原版 VSAG 的 HGraph/SQ8

**已完成的程度。** 原生 Ubuntu 上构建 VSAG v0.15.0 的共享库，运行上游两个例子，并检查索引大小和输出。HGraph/SQ8 的输入为 10,000 条 128 维 FP32 合成向量，建图参数 `max_degree=26`、`ef_construction=100`。索引把库向量编码为 SQ8，执行 1 条 FP32 查询，以固定 `ef_search=100` 返回 top-10。另一个 HNSW/FP32 示例用 1,000 条向量，同样跑 1 条查询。两例完成的是功能验证。

**复现入口。** 在原生 Ubuntu 下，从项目根目录执行。VSAG 上游源码缺失时，先按[构建说明](../experiments/vsag/README.md)安装依赖、检出 v0.15.0 并核对提交 `295acf3c5e1b202bd414ef42f11b9d741aefdd6a`。下面的绑定命令沿用历史实验的 CPU 2。使用前先确认该逻辑 CPU 在允许集合内，其他机器可换成实际可用的编号。

```bash
taskset -pc $$
bash experiments/vsag/build.sh
taskset -c 2 python3 experiments/vsag/run_examples.py
```

[`build.sh`](../experiments/vsag/build.sh) 负责编译共享库及两个目标例子。[`run_examples.py`](../experiments/vsag/run_examples.py) 运行程序，检查索引条数、十个有效且不重复的 ID、有限非负且升序的距离，并保存每次的标准输出、错误输出和环境记录。这个脚本的总耗时覆盖数据生成、建图和查询。

| 要看什么 | 本地文件 |
| --- | --- |
| HGraph/SQ8 实际返回了什么 | [迁移后 HGraph 查询输出](../experiments/vsag/results/20261111_092401_187332/103_index_hgraph.stdout.txt)。首个返回项为 `6519: 13.865`，即标签 6519 和该示例报告的距离。 |
| HNSW/FP32 例子的对应输出 | [迁移后 HNSW 查询输出](../experiments/vsag/results/20261111_092401_187332/101_index_hnsw.stdout.txt) |
| 版本、机器、输入、校验口径 | [迁移后运行记录](../experiments/vsag/results/20261111_092401_187332/metadata.json) · [目录迁移与重建记录](../experiments/vsag/RELOCATION_2026-11-11.md) |

**和论文的差距。** 本地示例只有一条合成查询，尚无精确 top-10、Recall@10、单独查询 QPS 或论文消融。两例的图实现、数据规模和表示方式也不同，不能拿它们的总耗时估算 SQ8 的收益。论文第 6 节采用标准数据集和批量查询，报告相同召回水平的 QPS，并比较各项优化。HGraph 示例的高精度重排和环境调参默认关闭，PRS 是否实际使用尚待验证。

**平台口径。** 本地历史实验为原生 Ubuntu 24.04、AMD Ryzen 7 7735H。论文 §6.1 记载常规平台为 Intel Xeon Platinum 8163、512 GB 内存，VSAG 编译启用 AVX-512。§6.2 图 6 使用关闭超线程的 AWS r6i.16xlarge，§6.3 图 7 使用 AMD EPYC 服务器。引用耗时或 QPS 时，附上对应的实验平台、查询设置和召回率。

### 6.2 辅助实验 · 在 hnswlib 上独立复现 VSAG §3.2 的部分方法

**已完成的程度。** 用 20,000 条 128 维 FP32 合成向量建一次图，生成 300 条查询和全量扫描得到的精确 top-10。原版 hnswlib 和两个实验版加载同一份 `shared.hnsw`。实验版先筛未访问邻居，再分别用步长/深度 `(1,1)` 或 `(4,2)`，原版已有软件预取。三者各测 `efSearch=32、64、128`，每档预热后计时三轮。

```bash
python3 experiments/test_prepare_variant.py
taskset -c 2 python3 experiments/run_smoke.py
```

如缺上游版本，按[项目运行说明](../README.md)获取 hnswlib v0.8.0 并核对提交。上述命令从项目根目录运行。`run_smoke.py` 的普通结果写入 `experiments/results/`，下次会覆盖，两个历史归档目录各自保留。

| 入口 | 作用 |
| --- | --- |
| [`prepare_variant.py`](../experiments/prepare_variant.py) 约第 23–52 行 | 生成支持先筛邻居再预取的实验头文件。 |
| [`run_smoke.py`](../experiments/run_smoke.py) 约第 24–54 行 | 编译三版、统一准备数据、执行三档搜索并核对返回标签集合。 |
| [`smoke.cpp`](../experiments/smoke.cpp) 约第 41–94 行 | 合成数据、精确真值、共享索引和查询计时。 |
| [原生 Ubuntu 汇总](../experiments/INITIALIZATION_2026-11-09.md) · [原生 CSV](../experiments/results_ubuntu_2026-11-09/smoke.csv) · [核对记录](../experiments/results_ubuntu_2026-11-09/metadata.json) | 六组共 1,800 次首轮 top-10 集合核对一致。27 行计时表里两个实验版在当前设置下均未观察到加速。另有[独立 WSL 归档](../experiments/results_wsl_2026-11-09/smoke.csv)。 |

以下是原生 Ubuntu 归档的汇总。每组取三轮平均查询耗时的中位数，单位为微秒。

| `efSearch` | Recall@10 | 原版 | 步长 1 / 深度 1 | 步长 4 / 深度 2 |
| ---: | ---: | ---: | ---: | ---: |
| 32 | 44.60% | 43.77 | 90.09 | 73.05 |
| 64 | 61.40% | 94.00 | 151.76 | 152.36 |
| 128 | 78.17% | 167.10 | 314.29 | 238.49 |

这组对照同时改了筛选顺序和预取策略，测的是组合的净效果。缓存事件和实际距离计算次数未采集，因此暂时不能定位变慢原因。这个实验在 hnswlib 上做，与上面的 VSAG 官方 HGraph 示例各有自己的输入、目的和结果。

### 6.3 复现时已经遇到的工程问题

| 表现 | 原因和已采用的处理 | 源码或记录 |
| --- | --- | --- |
| 首次构建 VSAG 时报告 `__m512` 未声明 | 当时在保留 AVX2 的同时强制关闭 AVX-512，v0.15.0 的 AVX-512 四路 L2 实现里有一段以 `ENABLE_AVX2` 保护。恢复上游默认的多指令集编译，由运行时按本机支持的指令选择路径。 | [`avx512.cpp`](../experiments/vendor/vsag/src/simd/avx512.cpp) 约第 254–294 行。[构建兼容性记录](../experiments/vsag/README.md) |
| 项目移动目录后，原示例找不到 `libvsag.so` | 原构建缓存和程序的库搜索路径保留了旧目录。脚本识别旧缓存后重新配置与构建，运行脚本优先选项目当前的库目录。 | [`build.sh`](../experiments/vsag/build.sh) · [`run_examples.py`](../experiments/vsag/run_examples.py) · [迁移复验](../experiments/vsag/RELOCATION_2026-11-11.md) |
| hnswlib 头文件跨 Windows/Linux 后校验失败 | 生成脚本先把 CRLF 换行转换为 LF 再核对哈希。增加了 Linux 换行、Windows 换行和实际源码修改三种检查。 | [`prepare_variant.py`](../experiments/prepare_variant.py) · [`test_prepare_variant.py`](../experiments/test_prepare_variant.py) |

## 7. 从功能验证走到论文同类实验的大致步骤

可以先对照论文 §6.1–6.2 建立 **Recall@10–QPS 曲线** ，有了稳定基线，再做 §6.4 的分项对照。下面是后续实验路线，现有归档只覆盖第 1 步和独立的 hnswlib 小实验。

1. **确认可重复运行。** 用第 6.1 节脚本跑通原版示例，保留 VSAG 提交、构建选项和原始输出。用一套固定的本地设置作为后续起点。
2. **用同一套正式输入建一组基线。** 可从论文有、维度也与示例相同的 SIFT1M 开始。明确库向量、查询向量、距离定义和外部 ID，准备精确 top-10 作为真值。可用公开真值或全量距离扫描，核对距离定义、ID 和结果排序一致。
3. **将建图和查询分开计时。** 固定索引和查询，预热后单独计查询耗时。扫多个 `ef_search`，每档记录 Recall@10、QPS 及查询耗时分布，同时记录建图时间和索引内存。与 hnswlib 或论文基线比较时，在同一召回率附近比较曲线。
4. **每次明确改动一项。** 比较 SQ8 与 FP32 时，先说明是比较两个完整配置还是只隔离距离表示。默认建图过程也可能使用对应编码，若要隔离距离与访存，就需要固定或核对图结构。做预取对照时保留同一批数据、图和编码。要测 PRS、论文式调参或选择性复算，先确定当前版本实际走到对应路径，再记录开关、配置和指标。
5. **验证来自 KBest 的想法。** 第一组可以固定 VSAG 的图和计算内核，比较现有预取与按实际编码字节数和剩余邻居数设定的批次。第二组可以固定图、查询、编码和预取，对比原布局、Gorder 与树引导重排，保持逻辑边和邻居顺序。图精化和早停会改变搜索工作量，另做同召回对照。若记录缓存和地址转换事件，同时记录实际距离计算次数，才便于区分「等得更少」和「算得更少」。

正式归档至少保存原始计时数据、参数、提交、机器与线程配置、真值口径、图或索引标识，以及验证结果。 **先有可比较的召回率和耗时，才能说某项改动在这组条件下是否提速。**
