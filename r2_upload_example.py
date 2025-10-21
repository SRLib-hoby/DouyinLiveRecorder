#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
Example script for uploading videos to Cloudflare R2

This script demonstrates how to use the R2Uploader to upload recorded videos
to Cloudflare R2 storage.

Usage:
    # Upload a single file
    python r2_upload_example.py /path/to/video.mp4

    # Upload with configuration from config.ini
    python r2_upload_example.py --config /path/to/video.mp4

    # Upload all files in a directory
    python r2_upload_example.py --dir /path/to/downloads/
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.r2_uploader import R2Uploader, create_r2_uploader_from_config, upload_video_to_r2
from loguru import logger


def read_config():
    """Read configuration from config.ini file."""
    import configparser

    config_path = Path(__file__).parent / 'config' / 'config.ini'
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return None

    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8-sig')

    # Build config dict
    r2_config = {}

    if 'Cloudflare R2 配置' in config:
        section = config['Cloudflare R2 配置']
        r2_config['r2_upload_enabled'] = section.get('是否启用R2上传(是/否)', '否')
        r2_config['r2_account_id'] = section.get('R2账户ID', '')
        r2_config['r2_access_key_id'] = section.get('R2访问密钥ID', '')
        r2_config['r2_secret_access_key'] = section.get('R2访问密钥密码', '')
        r2_config['r2_bucket_name'] = section.get('R2存储桶名称', '')
        r2_config['r2_endpoint_url'] = section.get('R2端点URL', '')
        r2_config['r2_public_url'] = section.get('R2公共URL', '')
        r2_config['delete_after_upload'] = section.get('上传后删除本地文件', '否')
        r2_config['upload_format_filter'] = section.get('上传文件格式过滤', '')

    return r2_config


async def upload_single_file(uploader, file_path, platform='unknown', anchor='unknown', delete_after=False):
    """Upload a single file to R2."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False

    logger.info(f"Uploading {file_path}...")

    result = await upload_video_to_r2(
        uploader=uploader,
        file_path=file_path,
        platform=platform,
        anchor_name=anchor,
        delete_after_upload=delete_after
    )

    if result.get('success'):
        logger.success(f"Upload successful!")
        logger.info(f"  Object: {result.get('object_name')}")
        logger.info(f"  Size: {result.get('size', 0) / 1024 / 1024:.2f} MB")
        if 'url' in result:
            logger.info(f"  URL: {result.get('url')}")
        return True
    else:
        logger.error(f"Upload failed: {result.get('error')}")
        return False


async def upload_directory(uploader, dir_path, delete_after=False, format_filter=None):
    """Upload all video files in a directory to R2."""
    if not os.path.isdir(dir_path):
        logger.error(f"Directory not found: {dir_path}")
        return

    # Define video extensions
    video_extensions = {'.mp4', '.mkv', '.flv', '.ts', '.m3u8', '.avi', '.mov', '.wmv'}

    # Apply format filter if specified
    if format_filter:
        formats = [f".{fmt.strip().lower()}" for fmt in format_filter.split(',')]
        video_extensions = set(formats)

    # Find all video files
    video_files = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if Path(file).suffix.lower() in video_extensions:
                video_files.append(os.path.join(root, file))

    logger.info(f"Found {len(video_files)} video files to upload")

    # Upload files
    success_count = 0
    fail_count = 0

    for file_path in video_files:
        # Try to extract platform and anchor from path
        # Expected structure: downloads/platform/anchor/video.mp4
        parts = Path(file_path).parts
        platform = 'unknown'
        anchor = 'unknown'

        if len(parts) >= 3:
            if 'downloads' in parts:
                idx = parts.index('downloads')
                if idx + 2 < len(parts):
                    platform = parts[idx + 1]
                    anchor = parts[idx + 2]

        success = await upload_single_file(uploader, file_path, platform, anchor, delete_after)
        if success:
            success_count += 1
        else:
            fail_count += 1

    logger.info(f"Upload complete: {success_count} successful, {fail_count} failed")


async def main():
    parser = argparse.ArgumentParser(description='Upload videos to Cloudflare R2')

    parser.add_argument('path', nargs='?', help='File or directory path to upload')
    parser.add_argument('--config', action='store_true', help='Use configuration from config.ini')
    parser.add_argument('--dir', action='store_true', help='Upload all videos in directory')
    parser.add_argument('--delete', action='store_true', help='Delete local files after upload')
    parser.add_argument('--platform', default='unknown', help='Platform name')
    parser.add_argument('--anchor', default='unknown', help='Anchor/streamer name')

    # Manual configuration options
    parser.add_argument('--account-id', help='R2 Account ID')
    parser.add_argument('--access-key', help='R2 Access Key ID')
    parser.add_argument('--secret-key', help='R2 Secret Access Key')
    parser.add_argument('--bucket', help='R2 Bucket name')
    parser.add_argument('--public-url', help='R2 Public URL')

    args = parser.parse_args()

    # Validate path
    if not args.path:
        parser.print_help()
        sys.exit(1)

    # Create uploader
    uploader = None

    if args.config:
        # Load from config.ini
        logger.info("Loading configuration from config.ini...")
        config = read_config()
        if config:
            uploader = create_r2_uploader_from_config(config)
            delete_after = config.get('delete_after_upload', '否') in ['是', 'yes', 'true', '1']
            if args.delete:
                delete_after = True
        else:
            logger.error("Failed to load configuration")
            sys.exit(1)
    else:
        # Use manual configuration
        if not all([args.account_id, args.access_key, args.secret_key, args.bucket]):
            logger.error("Manual configuration requires: --account-id, --access-key, --secret-key, --bucket")
            logger.info("Or use --config to load from config.ini")
            sys.exit(1)

        uploader = R2Uploader(
            account_id=args.account_id,
            access_key_id=args.access_key,
            secret_access_key=args.secret_key,
            bucket_name=args.bucket,
            public_url=args.public_url
        )
        delete_after = args.delete

    if not uploader:
        logger.error("Failed to create R2 uploader")
        sys.exit(1)

    # Upload
    if args.dir:
        # Upload directory
        await upload_directory(uploader, args.path, delete_after)
    else:
        # Upload single file
        await upload_single_file(uploader, args.path, args.platform, args.anchor, delete_after)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Upload interrupted by user")
    except Exception as e:
        logger.error(f"Upload error: {e}")
        import traceback
        traceback.print_exc()
