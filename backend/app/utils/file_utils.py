"""
Filesystem helper utilities: saving uploads, validating file types,
generating unique ids/filenames, and resolving stored file paths.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.config import get_settings
from app.core.exceptions import (
    FileNotFoundInStorageError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)

settings = get_settings()

# Extension -> mime types we consider valid for that extension.
ALLOWED_EXTENSIONS: dict[str, set[str]] = {
    ".pdf": {"application/pdf"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".tiff": {"image/tiff"},
    ".tif": {"image/tiff"},
    ".bmp": {"image/bmp", "image/x-ms-bmp"},
}


def validate_file(filename: str, content_type: str, size_bytes: int) -> str:
    """
    Validates extension, mime-type, and size.
    Returns the normalised (lowercase) file extension on success.
    Raises AppException subclasses on failure.
    """
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(filename)

    # Some browsers send generic mime types (e.g. application/octet-stream);
    # we only hard-fail if the content type is present AND clearly wrong.
    allowed_mimes = ALLOWED_EXTENSIONS[suffix]
    if content_type and content_type not in allowed_mimes and content_type != "application/octet-stream":
        raise UnsupportedFileTypeError(filename)

    if size_bytes > settings.max_upload_size_bytes:
        raise FileTooLargeError(settings.max_upload_size_mb)

    return suffix


async def save_upload_file(upload_file: UploadFile) -> tuple[str, str, Path, int]:
    """
    Streams an UploadFile to disk under a generated unique id.

    Returns:
        (file_id, stored_filename, absolute_path, size_bytes)
    """
    raw_bytes = await upload_file.read()
    size_bytes = len(raw_bytes)

    suffix = validate_file(upload_file.filename, upload_file.content_type, size_bytes)

    file_id = uuid.uuid4().hex
    stored_filename = f"{file_id}{suffix}"
    destination = settings.upload_path / stored_filename

    async with aiofiles.open(destination, "wb") as out_file:
        await out_file.write(raw_bytes)

    return file_id, stored_filename, destination, size_bytes


def resolve_uploaded_file(file_id: str) -> Path:
    """
    Locates the stored file on disk that matches the given file_id,
    regardless of its original extension.
    """
    matches = list(settings.upload_path.glob(f"{file_id}.*"))
    if not matches:
        raise FileNotFoundInStorageError(file_id)
    return matches[0]


def build_output_filename(result_id: str, output_format: str) -> str:
    extension_map = {"markdown": "md", "html": "html", "json": "json"}
    ext = extension_map.get(output_format, "txt")
    return f"{result_id}.{ext}"


def is_pdf(path: Path) -> bool:
    return path.suffix.lower() == ".pdf"
