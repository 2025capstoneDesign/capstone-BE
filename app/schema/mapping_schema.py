from pydantic import BaseModel
from typing import List

class LectureTextRequest(BaseModel):
    lecture_text: str
    slide_texts: List[str]  

class MappingResult(BaseModel):
    segment_index: int
    matched_slide_index: int   
    similarity_score: float

class MappingResultResponse(BaseModel):
    results: List[MappingResult]
