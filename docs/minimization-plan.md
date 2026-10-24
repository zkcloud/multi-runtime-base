# 镜像最小化实验方案

基线为当前 main 07d82c08a3c740311897bb47d35e01c763a79e1a 已裁剪镜像（Dockerfile.reference / TRIM=1），不是更大的 TRIM=0 对照。

三组使用相同 OCI 上游 digest、相同 dpkg 包版本：
- baseline：冻结当前 main 实现。
- compact：压缩全模块 JDK lib/modules（ALL-MODULE-PATH、zip-9），无损重压缩 JMOD，删除可再生成的 CDS 和有对应源码的 Python bytecode。保留 Node 原生符号。
- test：compact 加 Node strip --strip-unneeded，动态导出必须完全一致。

保留全部 JDK 工具、模块、jmods、头文件、原生库及原生调试信息。没有缩为部分模块 JRE。每个 JMOD 条目解压后 SHA256 必须一致。工具链、静态库、apt/dpkg、CA 都保留。

取舍：默认 CDS 缓存移除后 JVM 启动加速减少，可用 java -Xshare:dump 重建；Python 首次导入重新生成 pyc；Node strip 会减少 Node/V8 本体的原生排障符号，JS inspector 和 N-API 需要实际验证。需要原生符号时设 STRIP_NODE=0。JDK 原生库不 strip。

除了原有功能/ELF 测试，增加全 JMOD describe、模块集合比较、下游 jlink、JShell、jdb、CDS 重建与加载、JNI、Node inspector。

sizes.json 记录未压缩 docker image inspect .Size。compression.json 比较实际 OCI 导出的旧版 gzip6、新版 gzip9、新版 zstd19 层字节数；这是本地导出实测，不冒充 GHCR 下载量。最小候选必须先通过功能验证。首次实验结果待 CI 完成补充。

保留 Trivy、SBOM 和安全门禁，不移除包元数据或忽略告警。本次通过 PR 提交，待审核后合并和发布。
