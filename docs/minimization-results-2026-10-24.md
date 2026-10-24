# 镜像最小化实测报告

日期：2026-10-24。范围：multi-runtime-base 基础镜像大小优化。

[PR #7](https://github.com/zkcloud/multi-runtime-base/pull/7) · [实际 Actions 运行](https://github.com/zkcloud/multi-runtime-base/actions/runs/40093061879) · [优化方案](minimization-plan.md) · [原始测量与镜像 ID](results/minimization-2026-10-24.json)

## 实测基线与结论

基线是已经合并的 main `07d82c08a3c740311897bb47d35e01c763a79e1a`，冻结为 Dockerfile.reference，使用 **TRIM=1**。没有拿更大的未裁剪镜像作为基线。

实测源码 head：`3d6cd4081a40b4622f59ae5a5877715609cfbd6c`；PR 合并测试 commit：`923494b6a081de2bc36ffc069ef4273e9a330adb`。后续文档提交不改变本次通过验证的生产代码和测试。

四组均使用相同上游 index digest，三档 dpkg 包版本一致。每组都在对应原生 amd64/arm64 runner 上实际构建并运行。

## 未压缩镜像内容大小

单位 MiB（1 MiB = 1,048,576 字节），来自 docker image inspect .Size。

| 镜像 | 当前 main 基线 | compact：保留 Node 符号 | 默认最小候选 | 减少 MiB | 减少比例 |
| --- | ---: | ---: | ---: | ---: | ---: |
| base/amd64 | 575.84 | 450.67 | 433.34 | 142.50 | 24.747% |
| base/arm64 | 596.69 | 471.10 | 451.99 | 144.70 | 24.25% |
| build/amd64 | 997.96 | 872.79 | 855.46 | 142.50 | 14.279% |
| build/arm64 | 1002.54 | 876.95 | 857.84 | 144.70 | 14.433% |

默认 Dockerfile 采用本轮三档对照中、通过全部功能验证且未压缩体积最小的候选。这里不宣称数学意义上的全局最小值；完整 JDK、三语言与既有 build 能力是本轮保留边界。

## 实际压缩导出层大小

单位 MiB。对三个 OCI layout 实际构建导出后，累计其 layer descriptor 的 size；排除很小的 config/manifest 元数据。不把本地导出称为已经下载或发布的 GHCR 镜像。

| 镜像 | 旧版 gzip6 | 新版 gzip9 | 新版 zstd19 | zstd19 相比旧版减少 |
| --- | ---: | ---: | ---: | ---: |
| base/amd64 | 253.35 | 244.63 | 223.21 | 11.90% |
| base/arm64 | 250.78 | 241.93 | 220.08 | 12.24% |
| build/amd64 | 404.95 | 396.23 | 348.71 | 13.89% |
| build/arm64 | 395.64 | 386.78 | 338.75 | 14.38% |

展开体积与传输体积收益不同。JDK 资源本身预压缩后，外层 gzip 的额外收益会变小。zstd19 是这次测量中更小的导出结果；正式 Registry push/pull 与所有消费者的解压兼容性没有执行验收，因此没有自动更改现有发布格式。当前发布流程仍从经过测试的归档导入并由 Docker push 发布。

## 优化措施与可复核证据

1. **JDK 全模块资源压缩**：用同一 Temurin JDK 的 jmods 运行 jlink，ALL-MODULE-PATH + zip-9，仅替换 lib/modules。保留原始 bin、原生库、include、jmods、legal 等开发资产。四组模块集合均与原镜像完全一致，各有 **69 个模块**。
2. **JMOD 无损重压缩**：使用标准 ZIP deflate level 9，只采用更小的结果；逐条解压校验 SHA256，逐个 jmod describe，再验证下游 jlink。amd64 校验 **28,819** 个条目，arm64 校验 **28,818** 个条目。
3. **可再生成缓存清理**：删除绑定旧模块镜像的预生成 CDS；清除有对应源码的 Python pyc，保留无源码的 bytecode。操作在产生文件的构建层完成，避免形成只隐藏文件的后续删除层。
4. **Node 原生符号裁剪**：仅对 Node 可执行文件执行 strip --strip-unneeded；裁剪前后全部动态导出文本一致。Node inspector、Intl、crypto、zlib 和 build N-API 实际测试通过。
5. **构建工具分离**：压缩脚本、Python/strip 构建辅助工具留在 payload 阶段，不额外安装到最终运行层。系统原有工具链和包集保持一致。

payload.json 中 amd64 JDK 常规文件总字节从 307,556,223 降到 197,369,028，Node 从 144,714,346 降到 126,539,210；arm64 JDK 从 308,151,757 降到 197,517,996，Node 从 141,211,621 降到 121,177,941。该口径是常规文件字节，不等于镜像层大小；总收益以 inspect 数据为准。

没有通过删除 JDK 模块、C/C++ 静态库、头文件、动态库、apt/dpkg 数据库或漏洞识别元数据来缩小镜像。

## 功能验证结果

共实际构建 **4 组 × 3 档 = 12 个镜像**：

- 原有功能测试 12 次通过：Ubuntu、Python 标准扩展、pip、venv、离线 wheel、Node/npm、Temurin JDK 21、Java 编译/文档/图像处理、apt 安装卸载；build 另有 C/C++、Python 扩展和 Node N-API。
- 增强能力测试 12 次通过：jimage verify、全部 JMOD describe、jlink 生成可运行且含 javac 的下游环境、JShell、jdb、CDS dump/强制加载、Node inspector/Intl/zlib；build 额外实际生成 JNI 头文件、编译共享库并运行。
- 两个优化档均通过 ELF 动态库检查，共 8 次。每个 profile 的检查路径数为 base/amd64 1703、base/arm64 1700、build/amd64 2689、build/arm64 2674，包含路径别名。
- 三档 Java 模块清单逐字比较一致；dpkg 包版本一致性检查 4 组均通过。
- 四组最小候选均生成 Trivy JSON 和 SPDX SBOM。

初次实验发现 CDS 仍指向原 lib/modules，导致警告污染模块清单比较。已修复顺序：替换资源前删除失效缓存，再验证模块和 jimage；没有放宽模块集合验收。

## 明确取舍

- 预生成 CDS 移除，默认 JVM 启动加速减少；CDS 功能保留，实测可重新生成并强制使用。
- 压缩类资源增加了解压工作；没有做 JVM 启动或业务吞吐性能压测，不能声称性能完全不变。
- Python 首次导入会重新编译可缓存源码，运行中可能重新写入 pyc。
- Node/V8 本体的部分原生排障符号减少；Java 原生库和调试符号没有 strip。Java 应用开发与已列出的 Node JS 调试能力通过验收。
- JDK 经过重新打包，不能把修改后的文件校验和说成 Temurin 官方原始发布物的校验和。
- 如需要 Node 原生符号，构建时使用 `--build-arg STRIP_NODE=0`，选择表中 compact 规格。

## 安全与发布

base 两架构 HIGH/CRITICAL 均为 0（另有 MEDIUM 33、LOW 6）。build 两架构各有 HIGH 372、CRITICAL 14，全部关联既有 linux-libc-dev 告警，原始门禁继续阻断；没有批量忽略、删除包数据库或降低阈值。

因此，**功能和体积优化验证通过，不等于全部安全门禁通过**。PR 待审核，尚未合并、未正式发布。Trivy 的识别范围与初版报告所述一致，不能替代对所有 JDK/Node 内嵌组件的完整安全评估。

## 使用

```bash
# 本轮默认最小候选
docker buildx build --target base --load -t multi-runtime-base:base .
docker buildx build --target build --load -t multi-runtime-base:build .

# 保留 Node 原生符号
docker buildx build --target base --build-arg STRIP_NODE=0 \
  --load -t multi-runtime-base:base-compact .
```

精确字节数、全部 image ID、上游摘要、OCI 层摘要、各档测试状态、JMOD 校验数和 SBOM 计数已写入 results/minimization-2026-10-24.json。完整日志与扫描细节保存在本次 Actions reports-* artifacts 中。
