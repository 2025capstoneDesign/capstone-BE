from pydantic import BaseModel

class KeywordSearchRequest(BaseModel):
    job_id: str
    keyword: str


class SegmentMatch(BaseModel):
    slide: str
    segment_id: str
    text: str


class TextMoveRequest(BaseModel):
    from_slide: str  # 예: "slide3"
    to_slide: str    # 예: "slide5"
    sentence: str