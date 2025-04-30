from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, lecture, ai, process_api

# FastAPI 
app = FastAPI(
    title="SmartLectureNote Project",
    description="Capstone Design 2025 Project",
    version="1.0.0"
)

# CORS 설정 (필요에 따라 도메인 추가)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 보안상 실제 운영 시엔 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(lecture.router, prefix="/api/lecture", tags=["Lecture"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(process_api.router, prefix="/api/process")

@app.get("/")
def read_root():
    return {"message": "FastAPI server is running", "status" : "Normal"}
