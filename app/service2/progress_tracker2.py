"""
job_id별 진행률(%)과 상태 메시지를 저장
작업 도중 중간 결과(슬라이드별 notes)도 임시 저장
완료되면 /process-result로 전체 결과 반환 가능
"""

# 메모리 내 상태 저장소 (Redis 같은 외부 저장소를 쓸 수도 있음)
progress_tracker = {}
result_tracker = {}

# 진행률 업데이트
def update_progress(job_id: str, progress: int, message: str):
    progress_tracker[job_id] = {"progress": progress, "message": message}

# 현재 진행률 가져오기
def get_progress(job_id: str):
    return progress_tracker.get(job_id)

# 중간 결과 저장
def save_partial_result(job_id: str, slide_key: str, note_section: dict):
    if job_id not in result_tracker:
        result_tracker[job_id] = {}
    result_tracker[job_id][slide_key] = note_section

# 전체 결과 반환
def get_result(job_id: str):
    return result_tracker.get(job_id)
