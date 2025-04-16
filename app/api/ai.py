from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from app.schema.ai_schema import PptExtractResponse, YouTubeURLRequest, AudioTranscibeResponse
from app.service.ai_service import download_youtube_audio, transcribe_audio_file, extract_ppt_text  # 서비스 모듈 임포트

router = APIRouter()

@router.post("/youtube-audio")
async def youtube_audio(request: YouTubeURLRequest):
    """
    YouTube 영상으로부터 오디오를 추출 
    """
    try:
        file_path = download_youtube_audio(request.youtube_url)
        return {"message": "YouTube 오디오 다운로드 완료", "data": file_path}
    except Exception as e:
        # 예외 발생 시 오류 메시지를 반환
        return JSONResponse(status_code=500, content={"message": f"오디오 추출 실패: {e}", "data": None})

@router.post("/transcribe-audio", response_model=AudioTranscibeResponse)
async def transcribe_audio(audio_file: UploadFile = File(...)):
    """
    업로드된 오디오 파일을 Whisper 모델로 음성을 텍스트로 변환
    """
    try:
        transcribed_text = transcribe_audio_file(audio_file)
        return {"message": "오디오 텍스트 변환 성공", "data": transcribed_text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"음성 인식 실패: {e}", "data": None})

@router.post("/extract-ppt-text", response_model=PptExtractResponse)
def extract_ppt_text_endpoint(ppt_file: UploadFile = File(...)):
    """
    업로드된 PPTX 파일에서 슬라이드별 텍스트 추출 
    """
    try:
        text_list = extract_ppt_text(ppt_file)
        return {"message": "PPT 텍스트 추출 성공", "data": text_list}
    except ValueError as e:
        # 잘못된 입력 등으로 인한 사용자 오류
        return JSONResponse(status_code=400, content={"message": str(e), "data": None})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"PPT 처리 실패: {e}", "data": None})
