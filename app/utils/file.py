import os
from fastapi import UploadFile
from uuid import uuid4

PROFILE_DIR = "app/media/profile"

def save_profile_image(file: UploadFile) -> str:
    ext = file.filename.split(".")[-1]
    filename = f"{uuid4().hex}.{ext}"
    file_path = os.path.join(PROFILE_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return f"/media/profile/{filename}" 