# 实际构建与验证报告（2026-10-24）

代码 head：`f45c1e62067c5cb6d5943d9324c9ae546bbf5599`；PR 合并测试 commit：`069115e95925d50b37216ad86935d9c2f7dd1cc7`。报告后的文档提交不改变 Dockerfile、测试脚本和 CI 实现。

[完整验证运行](https://github.com/zkcloud/multi-runtime-base/actions/runs/40060736835)。实际运行 Ubuntu amd64/arm64 原生 runner，没有把 QEMU 测试当作原生测试。四种优化镜像及四种未裁剪对照均成功构建、导入并运行。

## 验证结果

| 镜像 | 功能测试 | ELF 路径检查 | CRITICAL / HIGH / MEDIUM / LOW | SPDX 2.3 SBOM | 安全门禁 |
| --- | --- | --- | --- | --- | --- |
| base/amd64 | 通过 | 1703，通过 | 0 / 0 / 33 / 6 | 282 个组件 | 通过 |
| base/arm64 | 通过 | 1700，通过 | 0 / 0 / 33 / 6 | 282 个组件 | 通过 |
| build/amd64 | 通过 | 2689，通过 | 14 / 372 / 1969 / 714 | 372 个组件 | 阻断 |
| build/arm64 | 通过 | 2674，通过 | 14 / 372 / 1969 / 714 | 371 个组件 | 阻断 |

ELF 数值是检查路径数，包含目录别名；不代表不同二进制的唯一数量。SBOM 组件数量来自实际 SPDX JSON 的 packages 数组，不等于全部软件文件数量。四组 sizes 比较均确认 dpkg 包版本一致。

功能覆盖 Ubuntu 版本、Python 3.12 标准扩展/CA、pip、venv、离线 wheel 安装与导入、Node 24/crypto、npm 离线安装与脚本、Temurin 厂商/JDK 21、javac、jar、javadoc、Java headless PNG、apt 实际安装与卸载。build 额外验证 GCC/G++ 执行、make/CMake/Ninja/Git 命令、Python C 扩展编译/导入、Node N-API 扩展编译/调用。

## 已定位并修复

1. 初次 build 功能测试失败：版本化 Python 开发包没有通用 python3-config 入口。
2. 直接把配置脚本链接到 /usr/local/bin 后，实测错误返回 /usr/local/include/python3.12，导致 Python.h 缺失。改为 exec 原始 /usr/bin/python3.12-config 的包装器，两个架构均成功编译和导入扩展。
3. 初次 base Trivy 检出 npm 的 5 项 HIGH/CRITICAL：brace-expansion 5.0.9、http-cache-semantics 4.2.0、undici 6.28.0。升级 npm 11.21.1，替换其内嵌 undici 为兼容的 6.29.1；复测 base 两架构 HIGH/CRITICAL 均为 0，仍有 33 MEDIUM 和 6 LOW。
4. 上游 Node /usr/local 中的 Yarn 链接指向未复制的 /opt 载荷，移除这两个未承诺提供的入口。
5. 镜像比较在同一 CI 任务先锁定上游 index digest，再校验两份镜像的 dpkg 包版本，避免依赖不同导致错误归因。
6. Trivy 从首轮 0.69.3 升级并固定为 0.76.1，复核剩余告警。

首轮失败运行：[40059715308](https://github.com/zkcloud/multi-runtime-base/actions/runs/40059715308)，相关体积原始 JSON 保存在 results/initial-*.json。初始版本和修复版本的依赖有变化，不将跨版本体积变化当作纯裁剪收益。

## 剩余安全阻断

build 两架构各有 386 项 HIGH/CRITICAL，全部关联 `linux-libc-dev 6.8.0-147.147`，其中 CRITICAL 14、HIGH 372，扫描 Status 均为 affected，没有 FixedVersion。完整 ID 列表：[security-build-2026-10-24.json](results/security-build-2026-10-24.json)。没有设置忽略、没有使用 ignore-unfixed、没有移除 dpkg 元数据。

linux-libc-dev 由编译工具链的 libc 开发依赖引入，删除它会破坏开发镜像能力。头文件包与 Linux 源包的 CVE 关联需要安全适用性判断。Canonical 的[内核团队说明](https://lists.ubuntu.com/archives/kernel-team/2024-February/148886.html)解释了该包作为用户空间接口头文件的性质；Trivy 的[官方讨论](https://github.com/aquasecurity/trivy/discussions/6562)解释了源包公告映射到二进制包的局限，并提醒不能默认忽略所有头文件告警。

这些材料为适用性复核提供依据，本 PR 没有把全部告警直接归零或发布未经审核的 VEX。后续需要逐项确认、提交受包版本/CVE ID 范围限制且带证据的 VEX，或采用上游修复包后重扫。宿主机实际运行的内核需要独立管理。

## 发布状态与限制

- PR 保持草稿，等待代码和安全审查；未合并。
- GHCR publish job 因 PR 条件/安全门禁被跳过，没有正式发布。
- 发布实现包含两架构索引和已测试镜像归档复用；GHCR 推送、发布归档转移、环境审批和发布后拉取尚未实际执行，不能宣称这些已通过测试。
- 本次逐架构镜像都实际运行；正式 GHCR 多架构 manifest 尚未发布验证。
- 严格历史复现仍需 Ubuntu apt 快照；当前记录了上游 OCI 摘要与安装清单。
- 完整体积数据见[优化报告](optimization.md)，不提供未实测的压缩大小。

Artifacts 中的 functional.log、libraries.log、trivy.json、sbom.spdx.json、sizes.json、inspect.json、history.txt、inventory.txt、upstream-*.txt、build-metadata.json 为本次证据，默认保留 30 天。关键尺寸、扫描计数、镜像 ID、上游摘要和高危 ID 列表已写入仓库，避免只依赖临时 artifact。
