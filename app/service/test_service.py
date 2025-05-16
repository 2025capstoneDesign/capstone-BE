import whisper
import tempfile
import os
import subprocess
from fastapi import UploadFile

model = whisper.load_model("small")

async def detect_language_from_video(file: UploadFile):
    print("언어 감지 함수 들어오기 성공")

    # 1. 업로드된 영상 파일을 임시 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        temp_video.write(await file.read())
        temp_video_path = temp_video.name

    # 2. 앞 30초 오디오 추출 (wav)
    temp_audio_fd, temp_audio_path = tempfile.mkstemp(suffix=".wav")
    os.close(temp_audio_fd)

    ffmpeg_cmd = [
        "ffmpeg", "-y",  # -y: 기존 파일 덮어쓰기
        "-i", temp_video_path,
        "-t", "30",          # 앞쪽 30초만
        "-ar", "16000",      # Whisper 권장 샘플링레이트
        "-ac", "1",          # 모노 채널
        "-loglevel", "error",  # 로그 최소화
        temp_audio_path
    ]

    subprocess.run(ffmpeg_cmd, check=True)

    # 3. Whisper로 언어 감지 및 텍스트 추출
    result = model.transcribe(temp_audio_path)
    language = result.get("language")
    text = result.get("text")

    # 4. 임시 파일 정리
    os.remove(temp_video_path)
    os.remove(temp_audio_path)

    return {"language": language, "text": text}
