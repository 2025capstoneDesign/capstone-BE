import shutil
import os

from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.config.storage_s3 import upload_file_to_s3
from app.model.lecture import Lecture

def extract_audio_from_video(file: UploadFile):
    # TODO: 실제 오디오 추출 로직 연결 예정
    filename = f"{file.filename}"
    with open(filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "오디오 추출 로직은 아직 구현되지 않았지만 파일은 저장됨", "saved_file": filename}

def transcribe_audio_file(file: UploadFile):
    # TODO: Whisper 또는 SpeechRecognition으로 텍스트 추출
    return {"transcription": "여기에 음성 인식 결과가 나올 예정"}

def upload_lecture_file(file: UploadFile, db: Session):
    filename = file.filename
    filetype = filename.split(".")[-1]

    # AWS S3 업로드
    file_url = upload_file_to_s3(file.file, filename, file.content_type)

    # DB 저장
    lecture = Lecture(
        filename=filename,
        filetype=filetype,
        file_url=file_url  # ✅ 새 필드 추가 필요
    )
    db.add(lecture)
    db.commit()
    db.refresh(lecture)

    return {
        "message": "File uploaded to S3 and metadata saved to DB",
        "lecture_id": lecture.id,
        "filename": lecture.filename,
        "filetype": lecture.filetype,
        "file_url": lecture.file_url,
        "created_at": lecture.created_at
    }