# HNSW 访存与执行优化

更新：2026-11-09。

研究主线已确定：CPU 图检索的访存与执行优化，以 VSAG（PVLDB 2025）为核心论文；KBest 用于分析硬件优化及可迁移思想。具体改进方法与创新点仍待实验验证。

正式实验优先使用本人双系统中的原生 Ubuntu 24 环境。WSL 保留用于开发和快速检查；已有 WSL 结果属于流程验证，不能当作原生 Linux 的性能结果。原生系统的具体配置与运行结果尚待实际检查。

## 当前进展

- 已精读 VSAG 访存章节及 KBest 硬件优化相关章节，形成方法与源码对照。
- 已在 WSL2 中跑通基于 hnswlib 的 VSAG 部分方法复现：2 万条合成向量、3 档搜索参数、两个实验版本。
- 实验版与原版的逐查询 top-10 集合一致；当前小实验未观察到加速，尚未完成真实数据正式评测。
- 完整 VSAG 源码已下载供阅读与依赖检查，尚未编译完整系统。

## 阅读入口

| 内容 | 文件 |
| --- | --- |
| 主线、KBest 硬件优化、迁移判断与实验记录 | [当前研究记录](notes/VSAG主线_KBest迁移分析与本机复现_2026-11-09.md) |
| HNSW 流程、Cache 基础与实验设计 | [访存研究基础](notes/HNSW_Cache优化方向与实验条件_2026-11-08.md) |
| 原生 Ubuntu 与 WSL 的运行步骤、源码结构 | [实验说明](experiments/README.md) |
| 论文文件、版本和来源 | [论文目录](papers/README.md) |

已删除不再采用的 NUMA 专题和多方向选题讨论；目录中的旧文档链接已清理。原始论文保留为文献资料。

## 文件分类

| 目录 | 内容 |
| --- | --- |
| [experiments](experiments/README.md) | 本人实验代码、固定版本的上游源码、构建与数据、原始结果 |
| [notes](notes/) | 当前主线研究记录与基础材料，共 2 份 Markdown 文档 |
| [papers](papers/README.md) | 11 篇研究的本地 PDF 与来源记录，主线论文和辅助文献分开说明 |
| [thesis_documents](thesis_documents/) | 学校任务书、开题报告模板 |
| [notices](notices/) | 学院与学校毕业论文通知 |
| [templates](templates/) | 论文模板和书写规范 |
| [reference_materials](reference_materials/) | 系统操作指南、经验分享 |
