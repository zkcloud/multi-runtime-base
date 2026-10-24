# 镜像体积分析与优化报告

## 实测状态

首次 CI 尚未执行。本文件不提供估算 MB 数值，不把设计推断作为实测结果。实际值来自每次 Actions artifact 中 sizes.json，报告记录 commit、架构、时间和两份 image ID。

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
