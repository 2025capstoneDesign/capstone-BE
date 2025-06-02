from pydantic import BaseModel

class KeywordSearchRequest(BaseModel):
    job_id: str
    keyword: str



class SegmentMatch(BaseModel):
    slide: str
    segment_id: str
    text: str