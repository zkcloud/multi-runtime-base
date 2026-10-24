# multi-runtime-base

Ubuntu 24.04 企业多语言开发基础镜像：Python 3.12 + pip + venv、Node.js 24 + npm、Eclipse Temurin 完整 JDK 21。支持 linux/amd64、linux/arm64，保留 apt 动态安装。

| 变体 | 内容 | 用途 |
| --- | --- | --- |
| base | 三语言、完整 JDK、apt、CA、JDK 动态库 | Java 编译、脚本、业务开发 |
| build | base + GCC/G++/make/pkg-config/Python headers/Git/CMake/Ninja | C/C++、Python 原生扩展、Node 原生模块编译 |

**状态：四组实际构建、功能测试和 ELF 检查已通过；base 安全门禁通过，build 存在 linux-libc-dev 相关安全告警，发布仍被阻断。尚未合并或正式发布。** 详见[实际验证报告](docs/validation-2026-10-24.md)。

实测未压缩体积：base 为 amd64 575.84 MiB / arm64 596.69 MiB；build 为 amd64 997.96 MiB / arm64 1002.54 MiB。完整对照见[优化报告](docs/optimization.md)。

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

## 验证与发布

PR/push 执行两架构 × 两变体原生构建、功能测试、ELF 动态库检查、Trivy 漏洞扫描、SPDX SBOM、未裁剪对照构建及体积报告。所有日志与报告保存在 Actions artifacts，PR 不发布镜像。

审核合并后，在 main 手动运行 **Images**，输入版本（例如 `v1.0.0`）才发布 GHCR：
`ghcr.io/zkcloud/multi-runtime-base:base-v1.0.0` 和 `:build-v1.0.0`。
发布导入已测试的镜像归档，不重新构建；发布前全部测试及扫描必须通过。

详见 [架构](docs/architecture.md)、[构建和使用](docs/build-and-use.md)、[优化报告](docs/optimization.md)。
