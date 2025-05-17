from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.database.base import Base
from datetime import datetime
from zoneinfo import ZoneInfo  

KST = ZoneInfo("Asia/Seoul")

class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True) # 히스토리 아이디
    user_email = Column(String(255), nullable=False)   # 사용자 이메일 (이 히스토리가 어떤 사용자 것인지)
    filename = Column(String(255), nullable=False)     # 변환한 파일 이름
    notes_json = Column(JSON, nullable=False)          # 변환 결과 
    created_at = Column(                               # 히스토리 생성 일자
        DateTime,
        nullable=False,
        default=lambda: datetime.now(KST)  
    )