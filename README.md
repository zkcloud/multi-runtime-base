# multi-runtime-base

Ubuntu 24.04 企业多语言开发基础镜像：Python 3.12 + pip + venv、Node.js 24 + npm、Eclipse Temurin 完整 JDK 21。支持 linux/amd64、linux/arm64，保留 apt 动态安装。

| 变体 | 内容 | 用途 |
| --- | --- | --- |
| base | 三语言、完整 JDK、apt、CA、JDK 动态库 | Java 编译、脚本、业务开发 |
| build | base + GCC/G++/make/pkg-config/Python headers/Git/CMake/Ninja | C/C++、Python 原生扩展、Node 原生模块编译 |

**状态：基础实现已合并；本轮最小化优化通过 PR #7 待审核。四组的三档功能对照和 ELF 检查已通过，build 的既有安全告警仍阻断发布。** 详见[本轮实测报告](docs/minimization-results-2026-10-24.md)。

本轮默认最小候选的实测未压缩体积：base 为 amd64 433.34 MiB / arm64 451.99 MiB；build 为 amd64 855.46 MiB / arm64 857.84 MiB。相比此前已裁剪 main 分别减少 14.28%～24.75%。[方案与取舍](docs/minimization-plan.md) · [实测数据](docs/minimization-results-2026-10-24.md)。

## 构建和使用

```bash
docker buildx build --target base --load -t multi-runtime-base:base .
docker buildx build --target build --load -t multi-runtime-base:build .
docker run --rm -it -v "$PWD:/workspace" multi-runtime-base:build
```

Python 系统环境遵循 Ubuntu PEP 668。请在 venv 中安装依赖：

```bash
python -m venv .venv
.venv/bin/python -m pip install requests
npm install
javac Example.java
apt-get update && apt-get install -y --no-install-recommends curl
rm -rf /var/lib/apt/lists/*
```

默认 root 用于派生镜像与 apt 安装；业务沙箱应自行设置非 root 用户、只读根文件系统及资源限制。未设置全局 PIP_BREAK_SYSTEM_PACKAGES。默认不包含 Maven/Gradle，按需添加。

通过 `--build-arg STRIP_NODE=0` 可保留 Node 原生符号；默认配置清除可再生成的 CDS/pyc 缓存，保留完整 JDK 工具与全部模块。启动与原生诊断取舍见实测报告。

## 验证与发布

PR/push 执行两架构 × 两变体原生构建、功能测试、ELF 动态库检查、Trivy 漏洞扫描、SPDX SBOM、冻结旧版基线/保留符号版/最小版三档构建、gzip/zstd 实际导出及体积报告。所有日志与报告保存在 Actions artifacts，PR 不发布镜像。

审核合并后，在 main 手动运行 **Images**，输入版本（例如 `v1.0.0`）才发布 GHCR：
`ghcr.io/zkcloud/multi-runtime-base:base-v1.0.0` 和 `:build-v1.0.0`。
发布导入已测试的镜像归档，不重新构建；发布前全部测试及扫描必须通过。

详见 [架构](docs/architecture.md)、[构建和使用](docs/build-and-use.md)、[优化报告](docs/optimization.md)。
