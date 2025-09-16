import hashlib
import logging
import mimetypes
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException, status

from app.config import settings
from app.models import AssetType

logger = logging.getLogger(__name__)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    endpoint_url=settings.S3_ENDPOINT_URL,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    config=Config(signature_version='s3v4'),
    region_name=settings.S3_REGION,
)

# Common file extensions mapping to asset types
EXTENSION_TO_TYPE = {
    # Images
    '.jpg': AssetType.IMAGE, '.jpeg': AssetType.IMAGE, '.png': AssetType.IMAGE,
    '.gif': AssetType.IMAGE, '.webp': AssetType.IMAGE, '.svg': AssetType.IMAGE,
    # Documents
    '.pdf': AssetType.DOCUMENT, '.doc': AssetType.DOCUMENT, '.docx': AssetType.DOCUMENT,
    # Audio
    '.mp3': AssetType.AUDIO, '.wav': AssetType.AUDIO, '.ogg': AssetType.AUDIO,
    # Video
    '.mp4': AssetType.VIDEO, '.webm': AssetType.VIDEO, '.mov': AssetType.VIDEO,
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def get_asset_type(filename: str) -> AssetType:
    """Determine asset type from file extension."""
    ext = Path(filename).suffix.lower()
    return EXTENSION_TO_TYPE.get(ext, AssetType.OTHER)

def generate_object_key(filename: str, user_id: int) -> str:
    """Generate unique S3 object key."""
    timestamp = datetime.utcnow().strftime('%Y/%m/%d')
    unique_id = os.urandom(4).hex()
    ext = Path(filename).suffix.lower()
    return f"users/{user_id}/{timestamp}/{unique_id}{ext}"

async def calculate_checksum(file: UploadFile) -> str:
    """Calculate SHA-256 checksum of file."""
    sha256 = hashlib.sha256()
    while chunk := await file.read(8192):
        sha256.update(chunk)
    await file.seek(0)
    return sha256.hexdigest()

async def upload_file(file: UploadFile, user_id: int, is_public: bool = False) -> Dict[str, Any]:
    """Upload file to S3 and return metadata."""
    try:
        # Validate file size
        file_size = (await file.read()).__sizeof__()
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds {MAX_FILE_SIZE/1024/1024}MB limit"
            )
        
        key = generate_object_key(file.filename, user_id)
        checksum = await calculate_checksum(file)
        content_type = mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
        
        extra_args = {
            'ContentType': content_type,
            'Metadata': {'uploaded-by': str(user_id), 'checksum': checksum}
        }
        if is_public:
            extra_args['ACL'] = 'public-read'
            
        s3_client.upload_fileobj(file.file, settings.S3_BUCKET_NAME, key, ExtraArgs=extra_args)
        
        return {
            'key': key,
            'url': get_presigned_url(key) if not is_public else get_public_url(key),
            'filename': file.filename,
            'content_type': content_type,
            'size': file_size,
            'checksum_sha256': checksum,
            'is_public': is_public,
        }
        
    except ClientError as e:
        logger.error(f"S3 upload error: {e}")
        raise HTTPException(500, "Failed to upload file")

def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    """Generate presigned URL for private file access."""
    try:
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.S3_BUCKET_NAME, 'Key': key},
            ExpiresIn=expires_in
        )
    except ClientError as e:
        logger.error(f"Presigned URL error: {e}")
        raise HTTPException(500, "Failed to generate access URL")

def get_public_url(key: str) -> str:
    """Get public URL for a file."""
    if settings.S3_PUBLIC_URL:
        return f"{settings.S3_PUBLIC_URL.rstrip('/')}/{key}"
    return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.S3_REGION}.amazonaws.com/{key}"

def delete_file(key: str) -> bool:
    """Delete file from S3."""
    try:
        s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
        return True
    except ClientError as e:
        logger.error(f"Delete error: {e}")
        return False
