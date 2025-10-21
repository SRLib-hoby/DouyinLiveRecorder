# -*- encoding: utf-8 -*-

"""
Author: Claude
Date: 2025-10-21
Function: Upload recorded videos to Cloudflare R2 storage.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not installed. R2 upload functionality will be disabled. Install with: pip install boto3")


class R2Uploader:
    """
    Cloudflare R2 storage uploader using S3-compatible API.

    Cloudflare R2 is an S3-compatible object storage service that provides
    cost-effective storage with zero egress fees.
    """

    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        endpoint_url: Optional[str] = None,
        public_url: Optional[str] = None
    ):
        """
        Initialize R2 uploader.

        Args:
            account_id: Cloudflare account ID
            access_key_id: R2 access key ID
            secret_access_key: R2 secret access key
            bucket_name: R2 bucket name
            endpoint_url: Custom endpoint URL (auto-generated if not provided)
            public_url: Public URL for accessing uploaded files (optional)
        """
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for R2 upload. Install with: pip install boto3")

        self.account_id = account_id
        self.bucket_name = bucket_name
        self.public_url = public_url

        # Construct endpoint URL if not provided
        if endpoint_url is None:
            endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

        self.endpoint_url = endpoint_url

        # Initialize S3 client for R2
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name='auto'  # R2 uses 'auto' region
            )
            logger.info(f"R2 uploader initialized for bucket: {bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize R2 client: {e}")
            raise

    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to R2 storage.

        Args:
            file_path: Local file path to upload
            object_name: S3 object name (defaults to file basename)
            metadata: Optional metadata to attach to the object
            content_type: Optional content type (auto-detected if not provided)

        Returns:
            Dict containing upload result with keys:
                - success: bool
                - object_name: str
                - size: int (bytes)
                - url: str (if public_url configured)
                - error: str (if failed)
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {"success": False, "error": "File not found"}

        # Use file basename if object_name not specified
        if object_name is None:
            object_name = os.path.basename(file_path)

        # Get file size
        file_size = os.path.getsize(file_path)

        # Auto-detect content type if not provided
        if content_type is None:
            content_type = self._get_content_type(file_path)

        # Prepare upload arguments
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        if metadata:
            extra_args['Metadata'] = metadata

        try:
            logger.info(f"Uploading {file_path} ({file_size / 1024 / 1024:.2f} MB) to R2: {object_name}")

            # Upload file
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                object_name,
                ExtraArgs=extra_args
            )

            logger.success(f"Successfully uploaded {object_name} to R2")

            result = {
                "success": True,
                "object_name": object_name,
                "size": file_size,
                "bucket": self.bucket_name
            }

            # Add public URL if configured
            if self.public_url:
                result["url"] = f"{self.public_url.rstrip('/')}/{object_name}"

            return result

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"R2 upload failed: {error_code} - {error_msg}")
            return {
                "success": False,
                "error": f"{error_code}: {error_msg}",
                "object_name": object_name
            }
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return {
                "success": False,
                "error": str(e),
                "object_name": object_name
            }

    async def upload_file_async(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Async wrapper for upload_file.

        Runs the synchronous upload in a thread pool to avoid blocking.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.upload_file,
            file_path,
            object_name,
            metadata,
            content_type
        )

    def delete_file(self, object_name: str) -> bool:
        """
        Delete a file from R2 storage.

        Args:
            object_name: S3 object name to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            logger.info(f"Deleted {object_name} from R2")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete {object_name}: {e}")
            return False

    def list_files(self, prefix: str = "", max_keys: int = 1000) -> list:
        """
        List files in R2 bucket.

        Args:
            prefix: Filter objects by prefix
            max_keys: Maximum number of keys to return

        Returns:
            List of object keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except ClientError as e:
            logger.error(f"Failed to list objects: {e}")
            return []

    def file_exists(self, object_name: str) -> bool:
        """
        Check if a file exists in R2 storage.

        Args:
            object_name: S3 object name to check

        Returns:
            bool: True if exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking if {object_name} exists: {e}")
            return False

    @staticmethod
    def _get_content_type(file_path: str) -> str:
        """
        Auto-detect content type based on file extension.

        Args:
            file_path: Path to file

        Returns:
            MIME type string
        """
        ext = Path(file_path).suffix.lower()

        content_types = {
            '.mp4': 'video/mp4',
            '.mkv': 'video/x-matroska',
            '.flv': 'video/x-flv',
            '.ts': 'video/mp2t',
            '.m3u8': 'application/vnd.apple.mpegurl',
            '.mp3': 'audio/mpeg',
            '.m4a': 'audio/mp4',
            '.aac': 'audio/aac',
            '.txt': 'text/plain',
            '.json': 'application/json',
        }

        return content_types.get(ext, 'application/octet-stream')


def create_r2_uploader_from_config(config: dict) -> Optional[R2Uploader]:
    """
    Create R2Uploader instance from configuration dictionary.

    Args:
        config: Configuration dict with R2 settings

    Returns:
        R2Uploader instance or None if not configured/disabled
    """
    if not BOTO3_AVAILABLE:
        logger.warning("boto3 not available, R2 upload disabled")
        return None

    # Check if R2 upload is enabled
    enabled = config.get('r2_upload_enabled', '否').strip() in ['是', 'yes', 'true', '1']
    if not enabled:
        logger.info("R2 upload is disabled in configuration")
        return None

    # Get required configuration
    account_id = config.get('r2_account_id', '').strip()
    access_key_id = config.get('r2_access_key_id', '').strip()
    secret_access_key = config.get('r2_secret_access_key', '').strip()
    bucket_name = config.get('r2_bucket_name', '').strip()

    if not all([account_id, access_key_id, secret_access_key, bucket_name]):
        logger.warning("R2 configuration incomplete, upload disabled")
        return None

    # Get optional configuration
    endpoint_url = config.get('r2_endpoint_url', '').strip() or None
    public_url = config.get('r2_public_url', '').strip() or None

    try:
        uploader = R2Uploader(
            account_id=account_id,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            bucket_name=bucket_name,
            endpoint_url=endpoint_url,
            public_url=public_url
        )
        logger.success("R2 uploader configured successfully")
        return uploader
    except Exception as e:
        logger.error(f"Failed to create R2 uploader: {e}")
        return None


async def upload_video_to_r2(
    uploader: R2Uploader,
    file_path: str,
    platform: str,
    anchor_name: str,
    delete_after_upload: bool = False
) -> Dict[str, Any]:
    """
    Upload a recorded video to R2 with metadata.

    Args:
        uploader: R2Uploader instance
        file_path: Path to video file
        platform: Platform name (e.g., 'douyin', 'tiktok')
        anchor_name: Streamer name
        delete_after_upload: Delete local file after successful upload

    Returns:
        Upload result dictionary
    """
    if not os.path.exists(file_path):
        logger.error(f"Video file not found: {file_path}")
        return {"success": False, "error": "File not found"}

    # Construct object name preserving directory structure
    # e.g., downloads/douyin/anchor/video.mp4 -> douyin/anchor/video.mp4
    relative_path = file_path
    if 'downloads' in file_path:
        parts = file_path.split('downloads')
        if len(parts) > 1:
            relative_path = parts[1].lstrip('/\\')

    object_name = relative_path.replace('\\', '/')

    # Prepare metadata
    metadata = {
        'platform': platform,
        'anchor': anchor_name,
        'upload_timestamp': str(int(asyncio.get_event_loop().time()))
    }

    # Upload file
    result = await uploader.upload_file_async(
        file_path=file_path,
        object_name=object_name,
        metadata=metadata
    )

    # Delete local file if successful and requested
    if result.get('success') and delete_after_upload:
        try:
            os.remove(file_path)
            logger.info(f"Deleted local file after upload: {file_path}")
            result['local_file_deleted'] = True
        except Exception as e:
            logger.warning(f"Failed to delete local file {file_path}: {e}")
            result['local_file_deleted'] = False

    return result
