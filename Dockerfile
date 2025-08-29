# 基于轻量 Python，并安装 ffmpeg、rclone、inotify-tools
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl ca-certificates unzip inotify-tools \
 && rm -rf /var/lib/apt/lists/*

# 安装 rclone（亦可改为 awscli / boto3）
RUN curl -fsSL https://rclone.org/install.sh | bash

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . ./

# 录像目录（容器内临时磁盘），Cloudflare Containers 有 2~4GB 本地盘，具体看实例类型
# 注意：磁盘是临时的，必须再同步到 R2。:contentReference[oaicite:7]{index=7}
ENV RECORD_DIR=/app/downloads
RUN mkdir -p ${RECORD_DIR}

# 环境变量（通过 Wrangler 注入实际值）
# R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT, R2_BUCKET, R2_REGION=auto 等

# 启动脚本：并行录制 + 后台周期同步到 R2
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8080
CMD ["docker-entrypoint.sh"]