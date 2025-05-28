from typing import List
import os
from fastapi.responses import FileResponse
from requests import Session
from app.database.session import get_db
from app.model.history import History  
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from app.schema.history_schema import HistoryResponse, HistoryDeleteResponse
from app.service.auth_service import get_current_user
from app.model.user import User


router = APIRouter()


# prcoess-lecture의 결과 예시
final_notes = {
  "lecture_title": "2024 운영체제 1차 강의",
  "created_at": "2025-05-16T12:30:00",
  "summary_type": "concise",
  "notes": [
    {
      "slide_index": 1,
      "slide_title": "운영체제란?",
      "note": "운영체제는 하드웨어와 사용자 사이에서 자원을 관리하고 프로그램 실행을 제어하는 소프트웨어입니다. 컴퓨터 시스템의 효율성과 사용자 편의성을 향상시키는 역할을 합니다."
    },
    {
      "slide_index": 2,
      "slide_title": "운영체제의 주요 기능",
      "note": "1. 프로세스 관리\n2. 메모리 관리\n3. 파일 시스템\n4. 입출력 장치 제어\n운영체제는 이 기능들을 통해 다양한 프로그램이 동시에 실행될 수 있도록 지원합니다."
    },
    {
      "slide_index": 3,
      "slide_title": "프로세스와 스레드",
      "note": "프로세스는 실행 중인 프로그램 단위이고, 스레드는 프로세스 내에서 실행되는 작업 단위입니다. 스레드는 메모리 공간을 공유하며 효율적인 자원 사용이 가능합니다."
    },
    {
      "slide_index": 4,
      "slide_title": "문맥 교환 (Context Switching)",
      "note": "CPU가 다른 프로세스로 전환될 때 현재 상태를 저장하고 새로운 프로세스 상태를 복원하는 작업입니다. 이 과정은 시스템 오버헤드를 발생시키지만, 멀티태스킹을 가능하게 합니다."
    }
  ]
}

# 로그인된 사용자 히스토리 전부 불러오기 
@router.get("/my", response_model=List[HistoryResponse])
def get_my_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    histories = db.query(History).filter(History.user_email == current_user.email).all()

    if not histories:
        raise HTTPException(status_code=404, detail="히스토리가 존재하지 않습니다.")

    return histories

# 로그인된 사용자의 특정 히스토리 불러오기 (파일 이름으로 구분)
@router.get("/my/{filename}", response_model=HistoryResponse)
def get_my_history_by_filename(
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    history = db.query(History).filter(
        History.user_email == current_user.email,
        History.filename == filename
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="해당 파일 이름의 히스토리가 존재하지 않습니다.")

    return history


# 히스토리 DB에 저장 
@router.post("/save")
async def save_to_history(
    doc_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_history = History(
        user_email=current_user.email,  
        filename=doc_file.filename,
        notes_json=final_notes,
    )
    db.add(new_history)
    db.commit()
    db.refresh(new_history)
    print("필기 생성 결과 DB에 저장 완료")
    return {"message": "히스토리 저장 성공", "history" : new_history}
    

# 백엔드에 있는 파일을 클라이언트로 전송 -> http://localhost:8000/api/history/my 결과에서 filename 파싱한 다음에 이 api 쓰면 돼
@router.get("/download/{filename}")
def download_file(filename: str):
    base_dir = "download"
    file_path = os.path.join(base_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")

    # pdf는 미리보기 / ppt는 다운로드  
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf" if filename.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

# 히스토리에 있는 파일 삭제 
@router.delete("/my/{filename}", response_model=HistoryDeleteResponse)
def delete_my_history_by_filename(
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # DB에서 해당 히스토리 조회
    history = db.query(History).filter(
        History.user_email == current_user.email,
        History.filename == filename
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="해당 파일 이름의 히스토리가 존재하지 않습니다.")

    # DB에서 삭제
    db.delete(history)
    db.commit()
    print(f"히스토리 DB에서 삭제 완료: {filename}")

    # 3. 백엔드에 있는 파일도 삭제
    # file_path = os.path.join("download", filename)
    # if os.path.exists(file_path):
    #     os.remove(file_path)
    #     print(f"파일 시스템에서 삭제 완료: {file_path}")

    return {"message": "히스토리 삭제 성공", "filename": filename}
