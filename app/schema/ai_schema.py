from pydantic import BaseModel
from typing import Dict, Optional

# /youtube-audio 요청 형식 
class YouTubeURLRequest(BaseModel):
    youtube_url: str
    start_time: Optional[str] = None  # 예: "00:20:03"
    end_time: Optional[str] = None    # 예: "00:29:40"
# /extract-ppt-text 응답 형식 
class PptExtractResponse(BaseModel):
    message: str          
    data: Dict[str, str]  # "슬라이드 1": "슬라이드1에서 추출한 텍스트"

# /transcribe-audio 응답 형식
class AudioTranscibeResponse(BaseModel):
    message : str
    data : dict     # 강의 녹음본에서 추출한 텍스트 전체