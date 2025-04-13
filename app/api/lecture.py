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


@router.post("/extract-text-from-doc")
def extract_text_from_lecture_doc(file: UploadFile = File(...)):
    """
    강의안(PPTX, PDF) 파일에서 텍스트 추출
    """
    # TODO: 확장자 확인
    # TODO: PPTX → python-pptx로 텍스트 추출
    # TODO: PDF → pdfplumber로 텍스트 추출

    extension = file.filename.split('.')[-1].lower()
    if extension not in ["pdf", "pptx"]:
        return {"error": "지원하지 않는 파일 형식입니다. PDF 또는 PPTX만 허용됩니다."}

    # TODO: 실제 텍스트 추출 로직 구현 예정
    return {"message": f"{extension.upper()} 파일에서 텍스트 추출 완료", "text": "여기에 추출된 텍스트가 들어갑니다"}


@router.post("/lecture-slide-mapping")
def extract_text_from_lecture_doc(file: UploadFile = File(...)):
    """
    강의 녹음본에서 추출한 텍스트를 강의 슬라이드에 맞게 매칭
    """
    
    extension = file.filename.split('.')[-1].lower()
    if extension not in ["pdf", "pptx"]:
        return {"error": "지원하지 않는 파일 형식입니다. PDF 또는 PPTX만 허용됩니다."}

    # TODO: 실제 텍스트 슬라이드 맵핑 로직 구현 예정
    return {"message": "강의 녹음본 강의 슬라이드 맵핑 완료"}