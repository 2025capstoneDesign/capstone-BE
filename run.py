import uvicorn
from app.database.base import Base
from app.database.session import engine
from app.model import user  # ⚠️ 반드시 import 해야 테이블 생성됨

# 테이블 자동 생성
# def init_db():
#     print("📦 DB 테이블 생성 중...")
#     Base.metadata.create_all(bind=engine)
#     print("✅ DB 테이블 생성 완료")

if __name__ == "__main__":
    # init_db()
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=True)
