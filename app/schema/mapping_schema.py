from pydantic import BaseModel
from typing import List

class LectureTextRequest(BaseModel):
    lecture_text: str
    slide_texts: List[str]  # 슬라이드 리스트를 추가!

class MappingResult(BaseModel):
    segment_index: int
    matched_slide_index: int   # 주의: 슬라이드 "번호"가 아니라 "인덱스" (0부터)
    similarity_score: float

class MappingResultResponse(BaseModel):
    results: List[MappingResult]
