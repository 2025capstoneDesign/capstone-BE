import os
import json

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
from datetime import datetime

from requests import Session
from werkzeug.utils import secure_filename
from app.database.session import get_db
from app.model.history import History
from app.model.user import User
from app.service2.summary import generate_summary
from app.schema.realtime_schema import KeywordSearchRequest, SegmentMatch, TextMoveRequest
from app.service.auth_service import get_current_user
from app.service3.realtime_service import find_longest_staying_slide, load_or_create_result_json, save_result_json, transcribe_audio_with_timestamps

router = APIRouter()


# 실시간 변환 결과들이 저장되는 폴더 
"""
file/
└── 20250602_013000/               ← job_id
    ├── 강의슬라이드.pdf             ← 사용자가 처음 업로드한 PDF 파일
    ├── captioning_results.json   ← 이미지 캡셔닝 결과 (슬라이드 분석)
    ├── result.json               ← 슬라이드별 누적 STT 및 요약 결과
    └── 20250602_013101/          ← 사용자가 1차 오디오 업로드한 시각
    │   ├── audio.wav             ← 업로드된 오디오 파일
    │   └── meta.json             ← 체류 시간 등 슬라이드 메타데이터
    └── 20250602_013150/
        ├── audio.wav             ← 2차 업로드 오디오
        └── meta.json             ← 2차 슬라이드 체류 메타데이터
"""
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
    실시간 세션 시작 API
    PDF 슬라이드 파일(doc_file)을 file 폴더에 저장하며, 내부적으로 job_id를 생성하고 디렉토리 생성
    job_id를 반환
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



@router.post("/realtime-process/{job_id}")
async def real_time_process(
    job_id: str,
    audio_file: Optional[UploadFile] = File(None),
    meta_json: Optional[str] = Form(None),
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
                    # result.json 불러오기
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

                    # 다시 result.json에 저장
                    save_result_json(job_dir, result_data)
                    return result_data
                


        # 오디오 or 메타 없음 → 기존 결과만 반환
        return load_or_create_result_json(job_dir)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



@router.post("/search-keyword-locations", response_model=Dict[str, List[SegmentMatch]])
def search_segments_by_keyword(request: KeywordSearchRequest):
    """
    file/{job_id}/result.json에 저장된 데이터를 기반으로
    사용자가 입력한 키워드가 포함된 슬라이드 및 세그먼트를 찾아 반환하는 API
    """
    keyword = request.keyword.lower()
    job_id = request.job_id

    # result.json 경로 구성
    result_path = os.path.join(DATA_DIR, job_id, "result.json")
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="해당 job_id의 result.json 파일이 존재하지 않습니다.")

    # 파일 로드
    with open(result_path, "r", encoding="utf-8") as f:
        result_data = json.load(f)

    matches: List[SegmentMatch] = []

    # 슬라이드 및 세그먼트 탐색
    for slide_id, slide_data in result_data.items():
        segments = slide_data.get("Segments", {})
        for segment_id, segment_info in segments.items():
            text = segment_info.get("text", "")
            if keyword in text.lower():
                matches.append(SegmentMatch(
                    slide=slide_id,
                    segment_id=segment_id,
                    text=text
                ))

    return {"results": matches}



@router.post("/end-realtime-process/{job_id}")
async def end_real_time_process(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    마지막 슬라이드의 넘김 버튼(혹은 '변환 끝')을 눌렀을 때 호출되는 api
    file/{job_id}/result.json 에 저장된 슬라이드별 누적 STT 및 요약 결과를 History DB에 저장
    result.json의 결과를 History DB에 저장
    """

    job_dir = os.path.join(DATA_DIR, job_id)

    # file/{job_id} 에 있는 파일명 추출 
    uploaded_pdf_filename = None
    for file in os.listdir(job_dir):
        if file.lower().endswith(".pdf"):
            uploaded_pdf_filename = file
            break

    # file/{job_id}/result.json 속의 내용 result_data 가져오기 
    result_path = os.path.join(job_dir, "result.json")
    if not os.path.exists(result_path):
        raise FileNotFoundError("result.json 파일이 존재하지 않습니다.")
    
    with open(result_path, "r", encoding="utf-8") as f:
        result_data = json.load(f)
    
    # 파일명과 result_data 활용해 History DB에 저장장
    new_history = History(
        user_email=current_user.email,  
        filename=uploaded_pdf_filename,
        notes_json=result_data,
    )
    db.add(new_history)
    db.commit()
    db.refresh(new_history)



@router.post("/move-text-manually/{job_id}")
async def move_text_manually(job_id: str, request: TextMoveRequest):
    """
    문장을 한 슬라이드에서 다른 슬라이드로 이동시킨 후,
    두 슬라이드 모두에 대해 요약을 다시 생성하는 API.
    """
    try:
        job_dir = os.path.join(DATA_DIR, job_id)
        result_path = os.path.join(job_dir, "result.json")
        caption_path = os.path.join(job_dir, "captioning_results.json")

        if not os.path.exists(result_path) or not os.path.exists(caption_path):
            raise HTTPException(status_code=404, detail="필요한 파일이 없습니다.")

        # 파일 로드
        result_data = load_or_create_result_json(job_dir)
        with open(caption_path, "r", encoding="utf-8") as f:
            captioning_data = json.load(f)

        # 1. from_slide에서 문장 제거
        from_segments = result_data[request.from_slide]["Segments"]
        for seg in from_segments.values():
            if request.sentence in seg["text"]:
                seg["text"] = seg["text"].replace(request.sentence, "").strip()

        # 2. to_slide에 문장 추가
        to_segments = result_data[request.to_slide]["Segments"]
        first_seg = next(iter(to_segments.values()))

        from_num = int(request.from_slide.replace("slide", ""))
        to_num = int(request.to_slide.replace("slide", ""))

        # 조건에 따라 문장 앞 또는 뒤에 추가
        if to_num > from_num:
            first_seg["text"] = request.sentence + " " + first_seg["text"]
        else:
            first_seg["text"] += " " + request.sentence
                

        # 3. 요약 재생성 대상 슬라이드 목록
        affected_slides = [request.from_slide, request.to_slide]

        for slide_key in affected_slides:
            slide_number = int(slide_key.replace("slide", ""))
            slide_data = captioning_data[slide_number - 1]
            segments = result_data[slide_key]["Segments"]
            merged_text = "\n".join(seg["text"] for seg in segments.values())

            summary = generate_summary(slide_data, merged_text)

            result_data[slide_key]["Concise Summary Notes"] = f"🧠Concise Summary Notes\n{summary['concise_summary']}"
            result_data[slide_key]["Bullet Point Notes"] = f"✅Bullet Point Notes\n{summary['bullet_points']}"
            result_data[slide_key]["Keyword Notes"] = f"🔑Keyword Notes\n{summary['keywords']}"
            result_data[slide_key]["Chart/Table Summary"] = f"📊Chart/Table Summary\n{summary['chart_summary']}"

        save_result_json(job_dir, result_data)

        return {
            "message": f"'{request.sentence}' 문장을 {request.from_slide} → {request.to_slide}로 이동하고, 두 슬라이드 요약을 재생성했습니다.",
            "updated_slides": affected_slides
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
