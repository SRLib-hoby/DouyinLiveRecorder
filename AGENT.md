# DouyinLiveRecorder Agent Documentation

## Project Overview

DouyinLiveRecorder is a multi-platform live stream recording tool that monitors and automatically records live broadcasts from 60+ streaming platforms worldwide. Built with Python and FFmpeg, it provides a robust,循环值守 (continuous monitoring) solution for capturing live content.

## Key Features

- **Multi-Platform Support**: Records from 60+ platforms including Douyin, TikTok, Kuaishou, Huya, Douyu, Bilibili, YouTube, and many more
- **Automatic Monitoring**: Continuously monitors configured channels and automatically starts recording when they go live
- **Quality Selection**: Supports multiple quality levels (Original, Ultra HD, HD, SD, LD)
- **Format Options**: Save recordings in various formats (TS, MKV, FLV, MP4, MP3, M4A)
- **Segmented Recording**: Automatic video segmentation to prevent file corruption
- **Live Status Notifications**: Push notifications via WeChat, DingTalk, Telegram, Email, Bark, ntfy, PushPlus
- **Proxy Support**: Built-in proxy support for international platforms
- **Docker Support**: Fully containerized deployment with Docker and Docker Compose
- **Automatic Conversion**: Post-recording conversion to MP4 with H.264 encoding

## Architecture

### Core Components

```
DouyinLiveRecorder/
├── config/                    # Configuration files
│   ├── config.ini            # Main configuration
│   └── URL_config.ini        # Live room URLs
├── src/                      # Main package
│   ├── initializer.py        # Initialize Node.js environment
│   ├── spider.py             # Fetch live stream metadata
│   ├── stream.py             # Extract live stream URLs
│   ├── utils.py              # Utility functions
│   ├── logger.py             # Logging handler
│   ├── room.py               # Room information parser
│   ├── proxy.py              # Proxy configuration
│   └── http_clients/         # HTTP client implementations
│       ├── async_http.py     # Async HTTP client
│       └── sync_http.py      # Sync HTTP client
├── main.py                   # Main entry point
├── msg_push.py               # Push notification handler
├── ffmpeg_install.py         # FFmpeg installation script
└── downloads/                # Recorded videos storage
```

### Supported Platforms

**Chinese Platforms:**
- Douyin (抖音)
- Kuaishou (快手)
- Huya (虎牙)
- Douyu (斗鱼)
- Bilibili (B站)
- Xiaohongshu (小红书)
- YY, NetEase CC, Kugou, Weibo, Zhihu, and more

**International Platforms:**
- TikTok
- YouTube
- Twitch
- SOOP (AfreecaTV)
- Shopee
- Bigo
- ShowRoom
- TwitCasting
- And 40+ more platforms

## Configuration

### Main Configuration (`config/config.ini`)

**Recording Settings:**
- `视频保存格式`: Video format (ts|mkv|flv|mp4|mp3|m4a)
- `原画|超清|高清|标清|流畅`: Quality selection
- `分段录制是否开启`: Enable segmented recording
- `视频分段时间(秒)`: Segment duration in seconds
- `循环时间(秒)`: Monitoring interval in seconds
- `录制完成后自动转为mp4格式`: Auto-convert to MP4
- `mp4格式重新编码为h264`: Re-encode to H.264

**Notification Settings:**
- `直播状态推送渠道`: Push channels (微信|钉钉|tg|邮箱|bark|ntfy|pushplus)
- `开播推送开启`: Enable live start notifications
- `关播推送开启`: Enable live end notifications
- Custom notification templates supported

**Proxy Settings:**
- `是否使用代理ip`: Enable proxy
- `代理地址`: Proxy address (e.g., 127.0.0.1:7890)
- `使用代理录制的平台`: Platforms requiring proxy

**Platform Cookies:**
- Each platform has dedicated cookie configuration
- Required for platforms with authentication

### URL Configuration (`config/URL_config.ini`)

Add one live room URL per line:
```
https://live.douyin.com/745964462470
超清,https://live.douyin.com/745964462470
#https://live.kuaishou.com/u/disabled_room
```

- Prefix with quality (e.g., `超清,`) to set specific quality
- Prefix with `#` to temporarily disable monitoring

## Workflow

### Recording Process

1. **Initialization**
   - Load configuration from `config.ini` and `URL_config.ini`
   - Initialize FFmpeg and Node.js environment
   - Set up logging and proxy if configured

2. **Monitoring Loop**
   - For each configured URL:
     - Check if stream is live
     - Extract stream metadata (title, anchor name, quality options)
     - Parse live stream URLs

3. **Recording**
   - Start FFmpeg process to record stream
   - Monitor recording status
   - Handle segmented recording if enabled
   - Send live start notification

4. **Post-Processing**
   - Auto-convert to MP4 if configured
   - Re-encode to H.264 if needed
   - Delete original files if configured
   - Execute custom scripts if enabled
   - Send live end notification

5. **Error Handling**
   - Retry on network failures
   - Handle stream interruptions
   - Prevent file corruption with TS format

## Key Modules

### `src/spider.py`
- Fetches live room metadata from platform APIs
- Handles platform-specific authentication
- Parses room status and stream information

### `src/stream.py`
- Extracts actual stream URLs from metadata
- Handles quality selection logic
- Supports multiple URL formats (M3U8, FLV)
- Validates stream availability

### `src/room.py`
- Parses room URLs into platform identifiers
- Handles URL shortening and redirects
- Extracts room IDs and user IDs

### `src/utils.py`
- File path sanitization
- Video format conversion
- Configuration parsing
- FFmpeg command construction

### `msg_push.py`
- Multi-channel notification dispatcher
- Template-based message formatting
- Platform-specific API integrations

## Docker Deployment

### Quick Start
```bash
# Using docker-compose
docker-compose up -d

# Or build custom image
docker build -t douyin-live-recorder:latest .
docker run -v ./config:/app/config -v ./downloads:/app/downloads douyin-live-recorder
```

### Environment Variables
- `PROXY`: HTTP proxy address
- `RCLONE_ENABLED`: Enable rclone sync (true/false)
- `RCLONE_CONFIG`: Rclone configuration

### Volume Mounts
- `/app/config`: Configuration files
- `/app/downloads`: Recorded videos
- `/app/logs`: Application logs

## Development

### Requirements
- Python >= 3.10
- FFmpeg
- Node.js (auto-installed by initializer)

### Installation
```bash
git clone https://github.com/ihmily/DouyinLiveRecorder.git
cd DouyinLiveRecorder
pip install -r requirements.txt
python main.py
```

### Dependencies
- `requests`: HTTP requests
- `httpx`: Async HTTP client with HTTP/2 support
- `loguru`: Advanced logging
- `pycryptodome`: Encryption/decryption
- `PyExecJS`: JavaScript execution
- `tqdm`: Progress bars

## Best Practices

1. **Use TS Format**: Prevents file corruption on interruptions
2. **Enable Segmentation**: Splits long streams into manageable files
3. **Set Reasonable Intervals**: Avoid IP bans from frequent requests (recommended: 300s)
4. **Monitor Disk Space**: Configure `录制空间剩余阈值(gb)` threshold
5. **Use Proxy for International Platforms**: Required for TikTok, YouTube, Twitch, etc.
6. **Configure Cookies**: Essential for Douyin and authenticated platforms
7. **Enable Notifications**: Stay informed of recording status

## Troubleshooting

### Common Issues

**Recording doesn't start:**
- Verify URL is correct and live
- Check cookie configuration for the platform
- Ensure FFmpeg is installed
- Review logs in `/logs` directory

**Video corruption:**
- Use TS format instead of MP4/FLV
- Enable segmented recording
- Check disk space availability

**Proxy errors:**
- Verify proxy address format (host:port)
- Check proxy server connectivity
- Add platform to `使用代理录制的平台`

**Platform-specific failures:**
- Update platform cookies
- Check for platform API changes
- Review recent commits for fixes

## Agent Capabilities

This project is suitable for autonomous agent operations including:

1. **Automated Recording Management**
   - Add/remove channels dynamically
   - Adjust quality settings per channel
   - Schedule recording windows

2. **Intelligent Monitoring**
   - Detect unusual stream behavior
   - Optimize recording parameters
   - Handle platform-specific quirks

3. **Post-Processing Automation**
   - Video transcoding and optimization
   - Metadata tagging
   - Cloud storage upload
   - Content analysis and categorization

4. **Notification Intelligence**
   - Smart notification filtering
   - Context-aware alerts
   - Multi-channel routing

5. **Error Recovery**
   - Automatic retry with backoff
   - Fallback quality selection
   - Stream URL rotation

## Cloud Integration

The project supports cloud storage integration through:

1. **Rclone Integration** (existing)
   - Built-in Docker support
   - Automatic sync to cloud providers

2. **Cloudflare R2** (recommended for new deployments)
   - S3-compatible API
   - Cost-effective storage
   - Global CDN distribution

## License

Copyright (c) 2023-2025 by Hmily
GitHub: https://github.com/ihmily/DouyinLiveRecorder

## Contributing

Contributions welcome! Areas for enhancement:
- New platform support
- Performance optimizations
- Bug fixes
- Documentation improvements
- Cloud storage integrations

See the project's GitHub repository for contribution guidelines.
