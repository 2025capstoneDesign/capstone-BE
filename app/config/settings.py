from pydantic_settings import BaseSettings

# Settings 클래스에 .env 파일에 있는 모든 키를 정의
class Settings(BaseSettings):
    # 데이터베이스 및 JWT
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AWS
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_S3_BUCKET: str

    # OPENAI
    OPENAI_API_KEY: str

    # CLOVA
    CLOVA_API_KEY: str


    class Config:
        env_file = ".env"

settings = Settings()
