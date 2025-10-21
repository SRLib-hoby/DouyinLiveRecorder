# Cloudflare R2 Integration Setup Guide

This guide will help you configure DouyinLiveRecorder to automatically upload recorded videos to Cloudflare R2 storage.

## What is Cloudflare R2?

Cloudflare R2 is an S3-compatible object storage service with:
- **Zero egress fees**: No charges for data downloaded from R2
- **S3 API compatibility**: Works with existing S3-compatible tools
- **Global distribution**: Automatic caching through Cloudflare's CDN
- **Cost-effective**: Competitive pricing for storage

## Prerequisites

1. **Cloudflare Account** with R2 enabled
2. **R2 Bucket** created in your Cloudflare dashboard
3. **API Tokens** for R2 access

## Step 1: Create R2 Bucket

1. Log in to your [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **R2** in the sidebar
3. Click **Create bucket**
4. Enter a bucket name (e.g., `live-recordings`)
5. Click **Create bucket**

## Step 2: Generate R2 API Tokens

1. In R2 dashboard, click **Manage R2 API Tokens**
2. Click **Create API token**
3. Configure the token:
   - **Token name**: `DouyinLiveRecorder`
   - **Permissions**: `Object Read & Write` or `Admin Read & Write`
   - **TTL**: Choose appropriate expiration
4. Click **Create API Token**
5. **Save the credentials** (you won't see them again):
   - Access Key ID
   - Secret Access Key
   - Account ID

## Step 3: Configure DouyinLiveRecorder

Edit `config/config.ini` and update the `[Cloudflare R2 配置]` section:

```ini
[Cloudflare R2 配置]
# Enable R2 upload
是否启用R2上传(是/否) = 是

# Your Cloudflare Account ID (found in R2 dashboard)
R2账户ID = abc123def456789

# R2 API credentials
R2访问密钥ID = 4a1b2c3d4e5f6g7h8i9j0k
R2访问密钥密码 = abcdefghijklmnopqrstuvwxyz0123456789ABCD

# Bucket name you created
R2存储桶名称 = live-recordings

# Optional: Custom endpoint URL (leave empty for auto-generation)
R2端点URL =

# Optional: Public URL for accessing files
# If you've set up a custom domain for R2
R2公共URL = https://recordings.yourdomain.com

# Delete local files after successful upload
上传后删除本地文件 = 否

# Only upload specific formats (comma-separated, empty = all)
# Example: mp4,mkv
上传文件格式过滤 = mp4,mkv
```

## Step 4: Install boto3 Library

The R2 integration requires the `boto3` library. Install it with:

```bash
pip install boto3>=1.34.0
```

Or if you're installing all dependencies:

```bash
pip install -r requirements.txt
```

## Step 5: Using R2 Upload

### Automatic Upload

Once configured, DouyinLiveRecorder will automatically upload completed recordings to R2.

### Manual Upload (Python Script)

You can also manually upload files using the provided module:

```python
import asyncio
from src.r2_uploader import R2Uploader, upload_video_to_r2

# Initialize uploader
uploader = R2Uploader(
    account_id="your-account-id",
    access_key_id="your-access-key-id",
    secret_access_key="your-secret-access-key",
    bucket_name="your-bucket-name"
)

# Upload a video
async def upload():
    result = await upload_video_to_r2(
        uploader=uploader,
        file_path="/path/to/video.mp4",
        platform="douyin",
        anchor_name="streamer_name",
        delete_after_upload=False
    )
    print(result)

asyncio.run(upload())
```

### Integration in Custom Scripts

If you're using the custom script execution feature, you can integrate R2 upload:

```python
#!/usr/bin/env python3
import sys
import asyncio
from src.r2_uploader import create_r2_uploader_from_config, upload_video_to_r2
from src.utils import read_config

# Get video path from command line argument
video_path = sys.argv[1]
platform = sys.argv[2]
anchor = sys.argv[3]

# Load configuration
config = read_config()

# Create uploader from config
uploader = create_r2_uploader_from_config(config)

if uploader:
    # Upload video
    result = asyncio.run(upload_video_to_r2(
        uploader=uploader,
        file_path=video_path,
        platform=platform,
        anchor_name=anchor,
        delete_after_upload=False
    ))

    if result.get('success'):
        print(f"Upload successful: {result.get('url', 'N/A')}")
    else:
        print(f"Upload failed: {result.get('error')}")
```

## Configuration Options Explained

### 是否启用R2上传
Enable or disable R2 upload functionality.
- `是` / `yes` / `true` / `1`: Enable
- `否` / `no` / `false` / `0`: Disable

### R2账户ID
Your Cloudflare Account ID, found in:
- R2 dashboard URL: `https://dash.cloudflare.com/{account_id}/r2`
- Or in **R2 > Overview** section

### R2访问密钥ID / R2访问密钥密码
API credentials generated in Step 2. Keep these secret!

### R2存储桶名称
The name of your R2 bucket (e.g., `live-recordings`)

### R2端点URL
Optional custom endpoint. If empty, auto-generates as:
```
https://{account_id}.r2.cloudflarestorage.com
```

### R2公共URL
If you've configured a custom domain for public R2 access:
1. In R2 dashboard, click your bucket
2. Go to **Settings** > **Public Access**
3. Click **Connect Domain**
4. Follow instructions to connect your domain
5. Use that domain here: `https://recordings.yourdomain.com`

This enables the uploader to return public URLs for uploaded videos.

### 上传后删除本地文件
Automatically delete local files after successful upload to save disk space.
- `是`: Delete local file after upload
- `否`: Keep both local and R2 copies

### 上传文件格式过滤
Only upload specific file formats. Useful if you want to:
- Only upload final MP4 files: `mp4`
- Upload multiple formats: `mp4,mkv`
- Upload all formats: Leave empty

## File Organization in R2

Uploaded files maintain the local directory structure:

```
downloads/
├── douyin/
│   ├── streamer1/
│   │   └── 2025-10-21_20-30-00_stream_title.mp4
│   └── streamer2/
│       └── 2025-10-21_21-15-30_another_stream.mp4
└── tiktok/
    └── streamer3/
        └── 2025-10-21_22-00-00_live_show.mp4
```

In R2 bucket:
```
douyin/streamer1/2025-10-21_20-30-00_stream_title.mp4
douyin/streamer2/2025-10-21_21-15-30_another_stream.mp4
tiktok/streamer3/2025-10-21_22-00-00_live_show.mp4
```

Each file includes metadata:
- `platform`: Platform name (douyin, tiktok, etc.)
- `anchor`: Streamer name
- `upload_timestamp`: Unix timestamp of upload

## Troubleshooting

### "boto3 not installed" Error

Install boto3:
```bash
pip install boto3
```

### "R2 configuration incomplete" Warning

Ensure all required fields are filled in `config.ini`:
- R2账户ID
- R2访问密钥ID
- R2访问密钥密码
- R2存储桶名称

### Upload Fails with "403 Forbidden"

1. Verify your API token has correct permissions
2. Check that the bucket name is correct
3. Ensure the token hasn't expired

### Upload Fails with "NoSuchBucket"

The bucket name doesn't exist. Verify:
1. Bucket name is spelled correctly
2. Bucket exists in your Cloudflare account
3. Using the correct Account ID

### Slow Upload Speeds

1. Check your internet upload bandwidth
2. Consider enabling segmented uploads for large files
3. Verify no firewall/proxy issues

### Files Not Deleted After Upload

Check configuration:
```ini
上传后删除本地文件 = 是
```

Also verify the upload was actually successful by checking R2 dashboard.

## Cost Estimation

Cloudflare R2 pricing (as of 2025):

- **Storage**: $0.015 per GB per month
- **Class A Operations** (writes): $4.50 per million
- **Class B Operations** (reads): $0.36 per million
- **Egress**: FREE (no charges)

**Example cost for 1TB monthly recordings:**
- Storage: 1000 GB × $0.015 = $15/month
- Uploads: ~30,000 files × ($4.50 / 1M) = ~$0.14
- **Total**: ~$15.14/month

Compare to traditional S3 egress which could cost $90+ per TB downloaded!

## Security Best Practices

1. **Limit Token Permissions**: Only grant necessary permissions
2. **Use Token TTL**: Set expiration dates for API tokens
3. **Rotate Keys Regularly**: Generate new tokens periodically
4. **Secure config.ini**: Protect your configuration file
   ```bash
   chmod 600 config/config.ini
   ```
5. **Enable Bucket Versioning**: Protect against accidental deletions
6. **Monitor Usage**: Check R2 dashboard regularly for unexpected activity

## Advanced Features

### Lifecycle Policies

Configure automatic deletion of old recordings:

1. In R2 dashboard, select your bucket
2. Go to **Settings** > **Lifecycle rules**
3. Create rule to delete objects after X days
4. Example: Delete files older than 90 days

### Custom Domain with Cloudflare Pages

Serve your recordings via a custom domain:

1. Create a Cloudflare Pages project
2. Configure R2 bucket as data source
3. Add custom domain
4. Update `R2公共URL` in config

### Presigned URLs

Generate temporary download links in Python:

```python
from src.r2_uploader import R2Uploader

uploader = R2Uploader(...)

# Generate URL valid for 1 hour
url = uploader.s3_client.generate_presigned_url(
    'get_object',
    Params={
        'Bucket': 'your-bucket',
        'Key': 'path/to/video.mp4'
    },
    ExpiresIn=3600
)
```

## Integration with Web Applications

Access your recordings from a web app:

```javascript
// Fetch video list from R2
fetch('https://recordings.yourdomain.com/douyin/streamer1/')
  .then(response => response.json())
  .then(files => {
    files.forEach(file => {
      const videoUrl = `https://recordings.yourdomain.com/${file.key}`;
      // Display video player
    });
  });
```

## Support

For issues related to:
- **R2 service**: Contact Cloudflare support
- **DouyinLiveRecorder**: Open issue on GitHub
- **Integration**: See examples in `src/r2_uploader.py`

## References

- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)
- [R2 Pricing](https://developers.cloudflare.com/r2/pricing/)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [S3 API Compatibility](https://developers.cloudflare.com/r2/api/s3/api/)
