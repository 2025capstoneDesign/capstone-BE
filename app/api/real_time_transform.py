from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
import os
import json

from werkzeug.utils import secure_filename
from app.service3.realtime_service import find_longest_staying_slide, load_or_create_result_json, save_result_json, transcribe_audio_with_timestamps

router = APIRouter()
DATA_DIR = 'file'


def create_job_directory(job_id: str):
    """jobId에 해당하는 디렉토리 구조 생성"""
    job_dir = os.path.join(DATA_DIR, job_id)
    audio_dir = os.path.join(job_dir, 'audio')
    os.makedirs(audio_dir, exist_ok=True)
    return job_dir, audio_dir


@router.post("/start-realtime")
async def start_realtime(doc_file: Optional[UploadFile] = File(None)):
    """
    실시간 세션 시작 API.
    PDF 슬라이드 파일(doc_file)을 업로드하며, 내부적으로 job_id를 생성하고 디렉토리 생성.
    """
    try:
        # job_id = 현재 시간 기반 생성
        job_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_dir = create_job_directory(job_id)

        if doc_file:
            filename = secure_filename(doc_file.filename)
            pdf_path = os.path.join(job_dir, filename)
            with open(pdf_path, "wb") as f:
                f.write(await doc_file.read())

        return {"jobId": job_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.post("/api/realTime/real-time-process/{job_id}")
async def real_time_process(
    job_id: str,
    audio_file: Optional[UploadFile] = File(None),
    meta_json: Optional[str] = Form(None)
):
    """
    실시간 오디오/메타데이터 업로드 API
    사용자가 슬라이드를 넘기며 녹음한 오디오 파일과 해당 시점 메타 정보를 업로드
    오디오를 STT로 변환하고 가장 오래 체류한 슬라이드에 누적 저장
    """
    try:
        # job 디렉토리 확인
        job_dir = os.path.join(DATA_DIR, job_id)
        if not os.path.exists(job_dir):
            raise HTTPException(status_code=404, detail="Job ID not found")

        # 현재 시각 기반 sub 디렉토리 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sub_dir = os.path.join(job_dir, timestamp)
        os.makedirs(sub_dir, exist_ok=True)

        audio_path = None
        meta_data = None

        # 오디오 저장
        if audio_file:
            audio_path = os.path.join(sub_dir, "audio.wav")
            with open(audio_path, "wb") as f:
                f.write(await audio_file.read())

        # 메타 데이터 저장 및 파싱
        if meta_json:
            try:
                meta_data = json.loads(meta_json)
                with open(os.path.join(sub_dir, "meta.json"), 'w', encoding='utf-8') as f:
                    json.dump(meta_data, f, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON format")

        # STT + 슬라이드 누적 처리
        if audio_path and meta_data:
            longest_slide = find_longest_staying_slide(meta_data)

            if longest_slide is not None:
                stt_result = transcribe_audio_with_timestamps(audio_path)

                if stt_result and 'text' in stt_result:
                    result_data = load_or_create_result_json(job_dir)

                    slide_key = f"slide{longest_slide}"
                    segment_key = f"segment{longest_slide}"

                    # 슬라이드 항목 초기화
                    if slide_key not in result_data:
                        result_data[slide_key] = {
                            "Concise Summary Notes": "",
                            "Bullet Point Notes": "",
                            "Keyword Notes": "",
                            "Segments": {}
                        }

                    # 세그먼트 항목 초기화
                    if segment_key not in result_data[slide_key]["Segments"]:
                        result_data[slide_key]["Segments"][segment_key] = {
                            "text": "",
                            "isImportant": "false",
                            "reason": "",
                            "linkedConcept": "",
                            "pageNumber": ""
                        }

                    # 텍스트 누적
                    existing_text = result_data[slide_key]["Segments"][segment_key]["text"]
                    new_text = stt_result["text"]
                    result_data[slide_key]["Segments"][segment_key]["text"] = (
                        existing_text + " " + new_text if existing_text else new_text
                    )

                    # 저장
                    save_result_json(job_dir, result_data)
                    return result_data

        # 오디오 or 메타 없음 → 기존 결과만 반환
        return load_or_create_result_json(job_dir)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))