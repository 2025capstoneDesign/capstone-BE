from app.database.base import Base
from app.database.session import engine
# 반드시 여기서 해당 클래스를 import 해야 테이블 생성됨
from app.model import user, lecture, history

# 테이블 자동 생성
def init_db():
    print("📦 DB 테이블 생성 중...")
    Base.metadata.create_all(bind=engine)
    print("✅ DB 테이블 생성 완료")
