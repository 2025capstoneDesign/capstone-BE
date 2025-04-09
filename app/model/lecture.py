from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database.base import Base

class Lecture(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    filetype = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
