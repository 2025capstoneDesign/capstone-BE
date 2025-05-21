from fastapi import Depends, FastAPI, Form, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi import APIRouter
from requests import Session
# from app.service2.convert_audio import transcribe_audio
from app.api.ai import transcribe_audio
from app.database.session import get_db
from app.model.history import History
from app.model.user import User
from app.service.auth_service import get_current_user
from app.service2.segment_splitter import segment_split
from app.service2.image_captioning import image_captioning
from app.service2.segment_mapping import segment_mapping
from app.service2.summary import create_summary
from datetime import datetime
import os
import shutil
import uuid
import json


router = APIRouter()

def save_final_result(final_result: dict) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_dir = "data/result"
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"result_{timestamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
    return path

@router.post("/process-lecture-v2")
async def process_structured_result(
    audio_file: UploadFile = File(...), 
    doc_file: UploadFile = File(...),
    skip_transcription: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 1. 업로드된 파일 저장
        temp_dir = "temp_upload"
        os.makedirs(temp_dir, exist_ok=True)
        audio_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{audio_file.filename}")
        doc_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{doc_file.filename}")

        with open(audio_path, "wb") as f:
            shutil.copyfileobj(audio_file.file, f)
        with open(doc_path, "wb") as f:
            shutil.copyfileobj(doc_file.file, f)

        # 2. STT → 세그먼트 → 캡셔닝 → 매핑 → 요약
        
        # STT
        if skip_transcription:
            stt_dir = "data/stt_result"
            stt_files = [f for f in os.listdir(stt_dir) if f.startswith("stt_result")]
            if stt_files:
                latest_stt = max(stt_files)
                with open(os.path.join(stt_dir, latest_stt), 'r', encoding='utf-8') as f:
                    stt_result = json.load(f)
        else:
            stt_result = transcribe_audio(audio_path)

        # 세그먼트 분리
        segments = segment_split(stt_data=stt_result)
        if isinstance(segments, dict) and "segments" in segments:
            segments = segments["segments"]

        # 이미지 캡셔닝
        captioning = image_captioning(doc_path)

        # 세그먼트-슬라이드 매핑
        mapping = segment_mapping(
            image_captioning_data=captioning,
            segment_split_data=segments
        )

        # 필기 생성
        summary = create_summary(
            image_captioning_data=captioning,
            segment_mapping_data=mapping
        )

        # 3. 슬라이드별 최종 결과 생성
        structured_result = {}
        for slide_key in mapping.keys():
            if slide_key == "slide0":
                continue
            slide_number = int(slide_key.replace("slide", ""))
            if slide_number > len(captioning):
                continue

            slide_caption = captioning[slide_number - 1]
            segments_data = mapping[slide_key].get("Segments", {})
            summary_data = summary.get(slide_key, {})

            structured_result[slide_key] = {
                "Concise Summary Notes": summary_data.get("Concise Summary Notes", ""),
                "Bullet Point Notes": summary_data.get("Bullet Point Notes", ""),
                "Keyword Notes": summary_data.get("Keyword Notes", ""),
                "Chart/Table Summary": summary_data.get("Chart/Table Summary", {}),
                "Segments": {
                    seg_id: {
                        "text": seg_val.get("text", ""),
                        "isImportant": "false",
                        "reason": "",
                        "linkedConcept": "",
                        "pageNumber": ""
                    } for seg_id, seg_val in segments_data.items()
                }
            }
        
        # 슬라이드별 필기 생성 최종 결과 History DB에 저장
        new_history = History(
            user_email=current_user.email,  
            filename=doc_file.filename,
            notes_json=structured_result,
        )
        db.add(new_history)
        db.commit()
        db.refresh(new_history)

        save_path = save_final_result(structured_result)

        return JSONResponse(content=structured_result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))