# 镜像体积分析与优化报告

## 实测状态

已完成实际构建、功能测试、动态库检查、Trivy 0.76.1 扫描及 SBOM 生成。证据：[验证运行](https://github.com/zkcloud/multi-runtime-base/actions/runs/40060736835)，源代码 head：f45c1e62067c5cb6d5943d9324c9ae546bbf5599，PR 测试 merge commit：069115e95925d50b37216ad86935d9c2f7dd1cc7。日期：2026-10-24。

| 变体 | 架构 | 对照字节 | 优化字节 | 优化 MiB | 减少字节 | 减少比例 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| base | amd64 | 661311289 | 603811358 | 575.84 | 57499931 | 8.695% |
| base | arm64 | 686658543 | 625678651 | 596.69 | 60979892 | 8.881% |
| build | amd64 | 1103935084 | 1046435153 | 997.96 | 57499931 | 5.209% |
| build | arm64 | 1112223332 | 1051243440 | 1002.54 | 60979892 | 5.483% |

以上为 Docker 未压缩内容大小，四组对照与优化的 dpkg 包版本一致性检查均通过；两者使用相同上游 index digest 和 npm 安全补丁。原始 sizes、镜像 ID、上游摘要和扫描汇总已提交至 [results/2026-10-24.json](results/2026-10-24.json)。完整测试与安全结果见 [验证报告](validation-2026-10-24.md)。GHCR 发布未执行，压缩传输大小没有实测值。

## 对照方法

同一 Dockerfile、相同上游镜像引用、同一 runner：
- 对照 TRIM=0：保留安装后的 apt lists、包文档及完整上游载荷。
- 优化 TRIM=1：同层清除 apt lists/cache，dpkg 安装时排除 man/info/doc（保留 copyright），载荷复制到最终镜像前移除 Node man/doc 和 JDK src.zip。
- 分别测 base/build × amd64/arm64 的 Docker image inspect .Size，输出字节和百分比。
- 同时记录 docker history、du 目录分布、dpkg 清单和 BuildKit metadata。
- 这是未压缩镜像内容大小，不能当成 GHCR 下载大小、磁盘增量或共享层去重后的总大小。

base/build 共享底层，不可把两者 Size 简单相加当成节点实际占用。基线缓存层和最终归档不发布到 GHCR。

## 能力边界

不删除 apt/dpkg 数据库、不对未知 ELF 执行 strip、不删除 JDK 模块或头文件、不移除 npm、不手工猜测动态库。全量 ldd 检查结合 Java headless 图像处理、Python 标准扩展、Java 编译及 build 原生编译验证。无图形桌面/X server/字体渲染布局保证。

完整 JDK 的 jmods、编译工具与模块库占据显著空间，这是完整开发功能的成本。继续缩小应优先拆出不同场景镜像；本项目保持用户要求的三语言完整开发基础能力。
