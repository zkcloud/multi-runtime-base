# 构建、验证与使用

## 本地验证

要求 Docker Engine + Buildx，以及用于跨架构本地执行的 binfmt/QEMU（CI 使用原生 runner）。

```bash
for variant in base build; do
  docker buildx build --target "$variant" --build-arg TRIM=0 --load -t "local/$variant:baseline" .
  docker buildx build --target "$variant" --build-arg TRIM=1 --load -t "local/$variant:test" .
  docker run --rm -v "$PWD/tests:/tests:ro" "local/$variant:test" bash /tests/functional.sh "$variant"
  docker run --rm -v "$PWD/tests:/tests:ro" "local/$variant:test" python /tests/libraries.py
  python3 scripts/measure.py "$variant" "$(uname -m)"
done
```

## 发布

1. PR 的四个验证任务全部通过，检视 artifacts 中测试日志、Trivy JSON、SBOM 和 sizes.json。
2. 审核合并 main；管理员可配置 release environment 审批。
3. main 手动执行 Images，release_version 输入 vX.Y.Z。
4. 流水线重新验证当前 main，以归档中的相同 image ID 发布两种 multiarch tag。
5. 发布版本 tag 视为不可变，不要重复使用版本号。当前 GHCR 不强制不可变，应由企业治理补充。

Trivy 对 HIGH/CRITICAL 漏洞阻断发布，包含尚未修复项；没有通用忽略清单。漏洞出现时更新上游依赖或评审具体漏洞，不能为绿灯关闭扫描。扫描报告与 SPDX JSON 在独立 artifact。PR 的 token 只有 contents:read，不提供 registry 密钥。

## 企业网络

构建代理使用 Docker 标准 HTTP_PROXY/HTTPS_PROXY/NO_PROXY build args；私有凭据使用 BuildKit secret，不使用 ARG 持久化。系统/Python 证书通过派生层配置 update-ca-certificates；Node 配置 NODE_EXTRA_CA_CERTS，Java 通过 keytool 导入专用 truststore，并设置 javax.net.ssl.trustStore。离线部署应先镜像上游 OCI 输入、Ubuntu apt、npm、PyPI 及 Trivy DB，不能把网络失败当成测试通过。

base 不支持直接编译本地 C 扩展；选择 build。pip 安装到 venv。Node 原生模块可指定 npm_config_nodedir=/usr/local 使用保留的 headers，避免离线环境下载 headers。

## 扫描范围

Trivy 对最终镜像中的 Ubuntu OS 包和可识别的语言依赖进行扫描，SPDX 记录识别到的组件；不能将它等同于对 Node/JDK 内嵌 C/C++ 依赖、JDK 自身所有 CVE 的完整验证。运行时版本保留于功能测试日志；企业仍应跟踪 Temurin CPU 和 Node 安全发布。GHCR 发布动作需在审核后执行，目前不能宣称其推送已实测通过。
