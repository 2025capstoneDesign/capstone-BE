import shutil
import os

from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.model.lecture import Lecture

AUDIO_SAVE_PATH = "media/audio"  # 저장 경로 지정 (media 폴더는 미리 만들어둬도 좋아)
VIDEO_SAVE_PATH = "media/video"

os.makedirs(AUDIO_SAVE_PATH, exist_ok=True)
os.makedirs(VIDEO_SAVE_PATH, exist_ok=True)

def extract_audio_from_video(file: UploadFile):
    # TODO: 실제 오디오 추출 로직 연결 예정
    filename = f"{VIDEO_SAVE_PATH}/{file.filename}"
    with open(filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "오디오 추출 로직은 아직 구현되지 않았지만 파일은 저장됨", "saved_file": filename}

def transcribe_audio_file(file: UploadFile):
    # TODO: Whisper 또는 SpeechRecognition으로 텍스트 추출
    return {"transcription": "여기에 음성 인식 결과가 나올 예정"}

def upload_lecture_file(file: UploadFile, db: Session):
    filename = file.filename
    filetype = filename.split(".")[-1]
    filepath = f"{AUDIO_SAVE_PATH}/{filename}"

    # 파일 저장 
    # TODO : 지금은 로컬에 저장 but 나중에는 클라우드에 저장되고 url만 db에 저장되는 식으로 

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # DB 저장
    lecture = Lecture(
        filename=filename,
        filetype=filetype
    )
    db.add(lecture)
    db.commit()
    db.refresh(lecture)

    return {
        "message": "강의 파일 업로드 및 DB 저장 완료",
        "lecture_id": lecture.id,
        "filename": lecture.filename,
        "filetype": lecture.filetype,
        "created_at": lecture.created_at
    }
