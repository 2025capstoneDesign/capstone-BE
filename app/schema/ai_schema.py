from pydantic import BaseModel
from typing import Dict

# /youtube-audio 요청 형식 
class YouTubeURLRequest(BaseModel):
    youtube_url: str

# /extract-ppt-text 응답 형식 
class PptExtractResponse(BaseModel):
    message: str          
    data: Dict[str, str]  # "슬라이드 1": "슬라이드1에서 추출한 텍스트"