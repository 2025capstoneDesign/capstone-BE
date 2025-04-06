# Capstone Project - Smart Lecture Note Backend

이 프로젝트는 스마트 강의 노트 자동화 시스템의 백엔드입니다. FastAPI, MySQL, JWT 등을 사용하여 사용자 인증 및 데이터 처리를 수행합니다.

---

## 🚀 프로젝트 실행 방법

### 1. 루트 디렉토리로 이동

```bash
cd capstone-BE
```

### 2. 가상환경 생성 및 활성화

```
# 가상환경 생성
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. 의존성 패키지 설치

```
pip install -r requirements.txt
```

### 4. 환경 변수 파일 .env 생성

```
DATABASE_URL=mysql+pymysql://<username>:<password>@localhost:3306/<database_name>
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> 실제 값으로 **username**, **password**, **database_name**을 바꿔주세요.

### 5. 서버 실행 (루트 디렉토리에서)

```
python run.py
```
