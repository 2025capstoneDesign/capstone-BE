# app/utils/progress_tracker.py
from typing import Dict
from threading import Lock

progress_tracker: Dict[str, Dict] = {}
lock = Lock()

def update_progress(job_id: str, progress: int, message: str):
    with lock:
        if job_id not in progress_tracker:
            progress_tracker[job_id] = {}

        prev_result = progress_tracker[job_id].get("result")
        progress_tracker[job_id]["progress"] = progress
        progress_tracker[job_id]["message"] = message

        if prev_result is not None:
            progress_tracker[job_id]["result"] = prev_result

def get_progress(job_id: str):
    with lock:
        return progress_tracker.get(job_id)

def get_result(job_id: str):
    with lock:
        return progress_tracker.get(job_id, {}).get("result")

def save_result(job_id: str, result):
    with lock:
        if job_id in progress_tracker:
            progress_tracker[job_id]["result"] = result

def save_partial_result(job_id: str, slide_key: str, content):
    with lock:
        if job_id in progress_tracker:
            if "result" not in progress_tracker[job_id]:
                progress_tracker[job_id]["result"] = {}
            progress_tracker[job_id]["result"][slide_key] = content
