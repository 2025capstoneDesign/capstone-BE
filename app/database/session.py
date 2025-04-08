from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

# DB와 연결할 수 있는 엔진 객체를 생성
engine = create_engine(settings.DATABASE_URL)
# SQLAlchemy ORM에서 사용하는 세션 생성 팩토리
# 이걸로 DB와의 세션을 만들고, db.query(...) 같은 ORM 작업 수행 가능
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
