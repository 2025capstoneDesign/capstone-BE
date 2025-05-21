from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.model.user import User
from app.model.history import History
from app.service.auth_service import get_current_user
from app.service2.progress_tracker2 import progress_tracker, get_progress, get_result
from app.service2.run_process2 import run_process_v2

import os, shutil, uuid

router = APIRouter()

@router.post("/start-process-v2")
async def start_process_v2(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    doc_file: UploadFile = File(...),
    skip_transcription: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job_id = str(uuid.uuid4())
    progress_tracker[job_id] = {"progress": 0, "message": "작업 대기 중"}

    # 임시 디렉토리에 파일 저장
    temp_dir = os.path.join("download", job_id)
    os.makedirs(temp_dir, exist_ok=True)
    audio_path = os.path.join(temp_dir, "audio.wav")
    doc_path = os.path.join(temp_dir, doc_file.filename)

    with open(audio_path, "wb") as f:
        shutil.copyfileobj(audio_file.file, f)
    with open(doc_path, "wb") as f:
        shutil.copyfileobj(doc_file.file, f)

    background_tasks.add_task(
        run_process_v2,
        job_id,
        audio_path,
        doc_path,
        skip_transcription,
        doc_file.filename,
        current_user.email,
        db
    )

    return {"job_id": job_id}


@router.get("/process-status-v2/{job_id}")
async def get_process_status(job_id: str):
    progress = get_progress(job_id)
    if not progress:
        return JSONResponse(status_code=404, content={"message": "작업 ID를 찾을 수 없습니다."})
    return progress


@router.get("/process-result-v2/{job_id}")
async def get_process_result(job_id: str):
    result = get_result(job_id)
    if not result:
        return JSONResponse(status_code=404, content={"message": "결과를 찾을 수 없습니다. 진행 중이거나 실패했을 수 있습니다."})
    return result
