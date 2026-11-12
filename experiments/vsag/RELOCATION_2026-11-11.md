# 2026-11-11 项目目录迁移修复

当前项目：`/home/hualuck7/Desktop/HNSW`。
历史项目：`/home/hualuck7/桌面/Myproject/HNSW`。

问题：CMake 缓存、生成的构建规则和示例程序 RUNPATH 保留了旧绝对路径。迁移后原例子默认启动提示找不到 libvsag.so；临时指定当前库目录可以运行，说明原二进制与库未损坏。

处理：

- build.sh 核对 CMake 缓存中的源码与构建路径；不匹配时将旧构建目录完整重命名备份，再在当前位置重新配置与构建，不批量替换生成文件内容。
- 本次曾将旧目录备份至 `experiments/build/vsag.before-relocation.20261111-090825.10097/`；新构建验证通过后，已于 2026-11-11 按用户要求删除。
- run_examples.py 根据脚本位置推导项目根目录，优先使用当前构建目录的 libvsag.so，保留已有 LD_LIBRARY_PATH 条目，记录当前项目与库位置。
- vendor 源码、既有结果和历史环境记录不改写。删除的是约 6.1 GiB 的旧构建备份，当前构建保留。

## 验证结果

- 新位置完整配置和编译成功；随后从 `/tmp` 再次运行 build.sh，增量构建成功，未重复备份。
- 活动构建中的 9 份 CMakeCache.txt 均不含旧项目根目录。
- 新程序 RUNPATH 指向当前 Desktop/HNSW 下的构建目录；ldd 没有缺失依赖。
- 清除调用者 LD_LIBRARY_PATH 后，直接启动新 HNSW 二进制成功。
- 从 `/tmp` 调用 run_examples.py，HNSW（1,000 条）和 HGraph/SQ8（10,000 条）全部基本结果检查通过；[新构建验证结果](results/20261111_092401_187332/) 保存两例输出和 metadata。
- [旧二进制兼容性验证](results/20261111_091025_456916/) 使用备份中的旧 RUNPATH 二进制，验证运行脚本能主动定位对应库；其 metadata 的 library_directory 因此指向已删除的备份目录，仅作为当时的验证记录，不能与新构建验证混淆。
- hnswlib 源码准备的 3 个测试通过。
- 修复前登记的 18 个历史结果/环境文件哈希全部未变；两份 vendor 上游仓库工作区干净。
- 完整重建日志：`experiments/build/vsag/logs/build-relocation-full.log`；最近增量构建日志仍为 `logs/build.log`。

## 后续使用

从项目根目录运行原命令：

```bash
bash experiments/vsag/build.sh
taskset -c 2 python3 experiments/vsag/run_examples.py
```

也可以从其他目录用脚本绝对路径调用。以后再次移动目录，build.sh 会保存不匹配的旧构建树并重新构建，所需时间与磁盘空间接近一次新构建。旧备份为生成产物；本次已按用户要求在验证新构建后清理。

本轮只修复构建与动态库定位，不新增召回率或性能结论。

