from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.service import lecture_service
from app.database.session import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/extract-audio")
def extract_audio_from_video(file: UploadFile = File(...)):
    """
    업로드된 영상 파일에서 오디오 파일 추출
    """
    # TODO: 비디오에서 오디오 추출하는 로직 추가
    # TODO : lecture_audio, lecture_note로 세분화 
    # lecture_audio : 강의 녹음본, 강의 영상
    # lecture_note : 강의 PPT, PDF

    return {"message": "오디오 추출 완료", "audio_path": "example.mp3"}


@router.post("/transcribe-audio")
def transcribe_audio(file: UploadFile = File(...)):
    """
    업로드된 오디오 파일에서 텍스트 추출
    """
    # TODO: 음성 인식 모델 연동
    return {"transcription": "이곳에 추출된 텍스트가 들어갑니다"}


@router.post("/upload-lecture-file")
def upload_lecture(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    강의 녹음본 및 강의안 업로드 
    """
    # TODO: 파일 저장 및 데이터베이스 등록
    return lecture_service.upload_lecture_file(file, db)