import asyncio
from fastapi import UploadFile
from starlette.datastructures import UploadFile as StarletteUploadFile

import sys
import os
sys.path.append(os.path.abspath(".")) 
from app.service.test_service import detect_language_from_video


async def run_test():
    # 테스트할 오디오 파일 열기
    file_path = "download/audio3.wav"
    with open(file_path, "rb") as f:
        upload_file = StarletteUploadFile(filename="audio.wav", file=f)
        result = await detect_language_from_video(upload_file)
        print("Detected Language:", result["language"])
        print("Transcribed Text:", result["text"][:500])  # 일부 출력

# asyncio로 비동기 실행
if __name__ == "__main__":
    asyncio.run(run_test())
