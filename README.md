# 🧠 필기요정 백엔드 실행 가이드

> Flask 기반 백엔드 서버는 음성 처리, 슬라이드 캡셔닝, 세그먼트-슬라이드 매핑 등의 핵심 로직을 수행합니다.

---

## 📦 1. 가상환경 설정 및 의존성 설치

```bash
# 프로젝트 루트에서 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
# Mac / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# 필수 패키지 설치
pip install -r requirements.txt
```

---

## 🗂️ 2. .env 파일 설정

루트 디렉토리에 `.env` 파일을 생성하고 아래 항목을 설정합니다:

```env
# Database Configuration
DATABASE_URI=mysql+pymysql://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:<PORT>/<DB_NAME>

# JWT Configuration
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# File Upload Configuration
UPLOAD_FOLDER=file
DATA_DIR=data

# API Keys (각 서비스별 설정 필수)
OPENAI_API_KEY=<your-openai-api-key>
CLOVA_API_KEY=<your-clova-api-key>
GOOGLE_API_KEY=<your-google-api-key>
GOOGLE_APPLICATION_CREDENTIALS=<path-to-your-google-credentials.json>

# Server Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=8000
FLASK_DEBUG=True

# Processing Configuration
STT_RESULT_PATH=data/stt_result/stt_result.json
```

---

## 3. 외부 API 키 설정 주의사항

### 네이버 CLOVA

- **Clova Speech API** 사용을 위한 **segment-spliter 서비스 활성화 필수**
- [Naver Developers](https://www.ncloud.com)에서 애플리케이션 등록 후 API Key 발급
- 발급 받은 `CLOVA_API_KEY`를 `.env`에 입력

### 구글 STT

- Google Cloud Console에서 **Speech-to-Text API 사용 설정**
- 서비스 계정 키(JSON)를 생성하고, 해당 경로를 `.env`의 `GOOGLE_APPLICATION_CREDENTIALS` 항목에 입력

---

## 🔧 4. FFmpeg & Poppler 설치

### Mac (Homebrew 기준)

````bash
brew install ffmpeg
brew install poppler
```### Ubuntu / Debian

> `ffmpeg`: 음성 분할 및 처리
> `poppler`: PDF → 이미지 변환(pdf2image 사용)

---

## 🚀 5. 백엔드 서버 실행

```bash
# 가상환경이 활성화된 상태에서 실행
python run.py
````

---
