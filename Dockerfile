# syntax=docker/dockerfile:1
FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive
# 代理（可选）
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ENV http_proxy=$HTTP_PROXY https_proxy=$HTTPS_PROXY no_proxy=$NO_PROXY \
    HTTP_PROXY=$HTTP_PROXY HTTPS_PROXY=$HTTPS_PROXY NO_PROXY=$NO_PROXY \
    PIP_DEFAULT_TIMEOUT=120 PIP_NO_CACHE_DIR=1

# 若设置了代理，让 apt 也跟随
RUN bash -lc ' \
  set -eux; \
  if [ -n "${HTTP_PROXY}" ]; then echo "Acquire::http::Proxy \"${HTTP_PROXY}\";"  > /etc/apt/apt.conf.d/99proxy; fi; \
  if [ -n "${HTTPS_PROXY}" ]; then echo "Acquire::https::Proxy \"${HTTPS_PROXY}\";" >> /etc/apt/apt.conf.d/99proxy; fi; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
    ffmpeg rclone curl ca-certificates unzip inotify-tools git; \
  rm -rf /var/lib/apt/lists/* \
'

WORKDIR /app
# 如果你的项目里已经有 requirements.txt
COPY requirements.txt ./ 2>/dev/null || true
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# 复制全部源码到镜像
COPY . .

# 运行目录
ENV RECORD_DIR=/app/downloads \
    LOG_DIR=/app/logs
RUN mkdir -p ${RECORD_DIR} ${LOG_DIR}

# 暴露端口 & 入口
EXPOSE 8080
CMD ["bash", "-lc", "if [ -x /usr/local/bin/docker-entrypoint.sh ]; then exec /usr/local/bin/docker-entrypoint.sh; else exec python -m http.server 8080; fi"]