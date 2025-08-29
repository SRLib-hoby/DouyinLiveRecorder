#!/usr/bin/env bash
set -euo pipefail

# 1) 启动录像主进程（按你的运行方式调整）
#    - 建议先把配置文件写好：config/*.yml 中填好要录制的直播间、保存格式（推荐 ts）等。:contentReference[oaicite:8]{index=8}
python main.py &

# 2) 配置 rclone 的 R2 远端（一次性）
rclone config create r2 s3 \
  provider Cloudflare \
  access_key_id "${R2_ACCESS_KEY_ID}" \
  secret_access_key "${R2_SECRET_ACCESS_KEY}" \
  endpoint "${R2_ENDPOINT}" \
  region "${R2_REGION:-auto}" \
  --non-interactive || true

# 3) 后台循环同步：把已落盘 ≥5 分钟的 ts/mp4 推送到 R2
while true; do
  rclone move "${RECORD_DIR}" "r2:${R2_BUCKET}" \
    --include "*.ts" --include "*.mp4" \
    --min-age 5m --transfers 4 --checkers 8 \
    --s3-chunk-size 64M --fast-list \
    --create-empty-src-dirs \
    --quiet
  sleep 60
done