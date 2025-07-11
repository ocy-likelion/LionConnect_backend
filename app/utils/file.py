import os
from fastapi import UploadFile, HTTPException
from uuid import uuid4

PROFILE_DIR = "app/media/profile"

def save_profile_image(file: UploadFile) -> str:
    try:
        # 디렉토리가 존재하지 않으면 생성
        os.makedirs(PROFILE_DIR, exist_ok=True)
        
        # 파일 확장자 검증
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        ext = file.filename.split(".")[-1].lower()
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식입니다. 허용된 형식: {', '.join(allowed_extensions)}")
        
        # 파일 크기 검증 (5MB)
        file.file.seek(0, 2)  # 파일 끝으로 이동
        file_size = file.file.tell()
        file.file.seek(0)  # 파일 시작으로 이동
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(status_code=400, detail="파일 크기가 5MB를 초과합니다.")
        
        filename = f"{uuid4().hex}.{ext}"
        file_path = os.path.join(PROFILE_DIR, filename)
        
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        
        return f"/media/profile/{filename}"
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}") 