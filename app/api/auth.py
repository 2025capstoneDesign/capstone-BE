from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app.schema.user import Token, UserCreate
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

# 로그인
@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"message": "Log In Success", "access_token": token, "token_type": "bearer"}

# 로그아웃
@router.get("/logout")
def logout():
    return {"message": "Logged out. Discard your token on client side."}

# 회원가입
@router.post("/register", response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_email(db, user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = create_user(db, user_data.email, user_data.password)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"message": "Register Success", "access_token": token, "token_type": "bearer"}
