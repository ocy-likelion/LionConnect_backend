import os
import uuid
import mimetypes
from fastapi import UploadFile, HTTPException
from supabase import create_client, Client


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "media")


def _client() -> Client:
    if not (SUPABASE_URL and SUPABASE_KEY):
        raise HTTPException(status_code=500, detail="Supabase 설정이 누락되었습니다(SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_image(file: UploadFile, folder: str = "misc") -> str:
    try:
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="업로드할 파일이 없습니다")

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            raise HTTPException(status_code=400, detail="허용되지 않는 이미지 형식입니다")

        key = f"{folder}/{uuid.uuid4().hex}{ext}"
        content = file.file.read()
        file.file.seek(0)
        ctype = mimetypes.guess_type(key)[0] or "application/octet-stream"

        _client().storage.from_(SUPABASE_BUCKET).upload(
            path=key,
            file=content,
            file_options={"content-type": ctype, "upsert": True},
        )

        public_url = _client().storage.from_(SUPABASE_BUCKET).get_public_url(key)
        if isinstance(public_url, dict) and "publicUrl" in public_url:
            return public_url["publicUrl"]
        # SDK 버전에 따라 문자열이 올 수 있음
        return str(public_url)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase 업로드 실패: {str(e)}")


