# syntax=docker/dockerfile:1.7
ARG NODE_IMAGE=node:24-bookworm-slim
ARG JAVA_IMAGE=eclipse-temurin:21-jdk-noble
ARG UBUNTU_IMAGE=ubuntu:24.04
FROM ${NODE_IMAGE} AS node
ARG NPM_VERSION=11.21.1
ARG UNDICI_VERSION=6.29.1
# npm's official patch release fixes brace-expansion/http-cache-semantics.
# Apply the newer compatible undici patch before copying the payload.
RUN npm install --global "npm@${NPM_VERSION}" --ignore-scripts --no-audit --no-fund \
    && npm install --prefix /tmp/npm-security "undici@${UNDICI_VERSION}" --ignore-scripts --no-audit --no-fund \
    && rm -rf /usr/local/lib/node_modules/npm/node_modules/undici \
    && cp -a /tmp/npm-security/node_modules/undici /usr/local/lib/node_modules/npm/node_modules/undici \
    && rm -rf /tmp/npm-security /root/.npm
FROM ${JAVA_IMAGE} AS java
FROM ${UBUNTU_IMAGE} AS payload
ARG TRIM=1
COPY --from=node /usr/local/ /payload/node/
COPY --from=java /opt/java/openjdk/ /payload/java/
# Keep every JDK binary, module, header, library and legal notice.
RUN rm -f /payload/node/bin/yarn /payload/node/bin/yarnpkg /payload/node/bin/docker-entrypoint.sh; \
    if [ "$TRIM" = 1 ]; then \
      rm -rf /payload/node/share/doc /payload/node/share/man \
             /payload/node/lib/node_modules/npm/docs /payload/node/lib/node_modules/npm/man \
             /payload/java/lib/src.zip; \
    fi

FROM ${UBUNTU_IMAGE} AS base
ARG TRIM=1
ENV JAVA_HOME=/opt/java/openjdk \
    PATH=/opt/java/openjdk/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin \
    LANG=C.UTF-8
SHELL ["/bin/bash", "-euo", "pipefail", "-c"]
# Do not remove dpkg metadata, apt, CA certificates or shared libraries.
RUN if [ "$TRIM" = 1 ]; then \
      printf 'path-exclude=/usr/share/doc/*\npath-include=/usr/share/doc/*/copyright\npath-exclude=/usr/share/man/*\npath-exclude=/usr/share/info/*\n' > /etc/dpkg/dpkg.cfg.d/01-nodoc; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      ca-certificates python3.12 python3-pip python3.12-venv \
      libstdc++6 libgcc-s1 zlib1g libfontconfig1 libfreetype6 \
      libasound2t64 libx11-6 libxext6 libxi6 libxrender1 libxtst6; \
    if [ "$TRIM" = 1 ]; then rm -rf /var/lib/apt/lists/* /var/cache/apt/*; fi; \
    ln -s /usr/bin/python3.12 /usr/local/bin/python; \
    ln -s /usr/bin/python3.12 /usr/local/bin/python3
COPY --from=payload /payload/node/ /usr/local/
COPY --from=payload /payload/java/ /opt/java/openjdk/
LABEL org.opencontainers.image.source="https://github.com/zkcloud/multi-runtime-base" \
      org.opencontainers.image.title="multi-runtime-base" \
      org.opencontainers.image.description="Ubuntu 24.04, Python 3.12, Node 24 and Eclipse Temurin JDK 21"
WORKDIR /workspace
CMD ["/bin/bash"]

FROM base AS build
RUN apt-get update; \
    apt-get install -y --no-install-recommends \
      build-essential pkg-config python3.12-dev git cmake ninja-build; \
    if [ "$TRIM" = 1 ]; then rm -rf /var/lib/apt/lists/* /var/cache/apt/*; fi; \
    printf '#!/bin/sh\nexec /usr/bin/python3.12-config "$@"\n' > /usr/local/bin/python3-config; \
    chmod 0755 /usr/local/bin/python3-config
