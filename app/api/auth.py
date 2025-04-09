from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app.schema.user_schema import UserLoginResponse, UserRegisterRequest, UserRegisterResponse
from app.service.user_service import authenticate_user, create_user, get_user_by_email
from app.config.security import create_access_token
from app.config.settings import settings
from app.database.session import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 로그인 API
@router.post("/login", response_model=UserLoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # DB에 있는 내용과 비교해 인증 시도 
    user = authenticate_user(db, form_data.username, form_data.password)
    # 사용자 인증 실패
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    # JWT 토큰 생성 
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"message": "Log In Success", "access_token": token, "token_type": "bearer"}

# 로그아웃 API
@router.get("/logout")
def logout():
    return {"message": "Logged out. Discard your token on client side."}

# 회원가입 API
@router.post("/register", response_model=UserRegisterResponse)
def register(user_data: UserRegisterRequest, db: Session = Depends(get_db)):
    # 회원 중복 확인
    existing = get_user_by_email(db, user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    # 사용자 생성 
    user = create_user(db, user_data.email, user_data.password)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"message": "Register Success", "access_token": token, "token_type": "bearer"}
