import uuid

from fastapi import HTTPException, UploadFile
from supabase import create_client, Client

from src.utils.settings import settings

# One shared Supabase client for the whole backend (uses the secret key)
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

RESUME_TYPES = {"application/pdf"}
TRADE_LICENSE_TYPES = {"application/pdf", "image/jpeg", "image/png"}

# The first bytes of a real file; a renamed fake file cannot match these
FILE_SIGNATURES = {
    "application/pdf": b"%PDF",
    "image/jpeg": b"\xff\xd8\xff",
    "image/png": b"\x89PNG\r\n\x1a\n",
}
EXTENSIONS = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png"}


def upload_file(file: UploadFile, bucket: str, allowed_types: set) -> str:
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Read at most 1 byte more than the limit, so huge files are not fully loaded
    content = file.file.read(MAX_FILE_SIZE + 1)

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File must be smaller than 5MB")
    if not content.startswith(FILE_SIGNATURES[file.content_type]):
        raise HTTPException(status_code=400, detail="File content does not match its type")

    # Unique name so two users never overwrite each other's file
    file_path = f"{uuid.uuid4().hex}.{EXTENSIONS[file.content_type]}"

    try:
        supabase.storage.from_(bucket).upload(
            file_path, content, {"content-type": file.content_type}
        )
    except Exception as error:
        print(f"Supabase upload error: {error}")  # shows the real reason in terminal
        raise HTTPException(status_code=500, detail="File upload failed")

    # Buckets are private, so we save only this path in the database
    return file_path


def upload_resume(file: UploadFile) -> str:
    return upload_file(file, settings.RESUME_BUCKET, RESUME_TYPES)


def upload_trade_license(file: UploadFile) -> str:
    return upload_file(file, settings.TRADE_LICENSE_BUCKET, TRADE_LICENSE_TYPES)


def get_signed_url(bucket: str, file_path: str, expires_in: int = 3600) -> str:
    # Temporary link (1 hour by default) to view a private file
    result = supabase.storage.from_(bucket).create_signed_url(file_path, expires_in)
    return result.get("signedURL") or result.get("signedUrl")


def delete_file(bucket: str, file_path: str):
    # Clean-up if something fails after the upload
    try:
        supabase.storage.from_(bucket).remove([file_path])
    except Exception:
        pass