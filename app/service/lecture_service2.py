import asyncio
import os
import tempfile
import shutil
import base64
import io
import subprocess

from pdf2image import convert_from_path
from pptx import Presentation
from fastapi import Form, UploadFile
from collections import OrderedDict
from requests import Session
from app.model.history import History
from app.service.progress_tracker import update_progress, save_partial_result
from app.service.ai_service import process_important_segments, generate_note, analyze_image, get_libreoffice_path
from app.service.mapping_service import LectureSlideMapper

LIBREOFFICE_PATH = get_libreoffice_path()
mapper = LectureSlideMapper()

def run_process(
    job_id: str,
    audio_path: str,
    ppt_path: str,
    skip_transcription: bool,
    original_filename: str,
    user_email: str,
    db: Session
):
    try:
        update_progress(job_id, 10, "오디오 텍스트 변환 시작")
        if skip_transcription:
            with open(os.path.join("download", "lecture_text.txt"), "r", encoding="utf-8") as f:
                lecture_text = f.read()
        else:
            import whisper
            model = whisper.load_model("small")
            result = model.transcribe(audio_path)
            lecture_text = result.get("text")
            with open(os.path.join("download", "lecture_text.txt"), "w", encoding="utf-8") as f:
                f.write(lecture_text)
        update_progress(job_id, 30, "텍스트 변환 완료")

        # PPT → PDF 변환
        temp_dir = os.path.dirname(audio_path)
        subprocess.run([LIBREOFFICE_PATH, "--headless", "--convert-to", "pdf", "--outdir", temp_dir, ppt_path], check=True)
        pdf_path = os.path.join(temp_dir, os.path.splitext(os.path.basename(ppt_path))[0] + ".pdf")
        if not os.path.exists(pdf_path):
            raise Exception("PDF 변환 실패")
        update_progress(job_id, 35, "PDF 변환 완료")

        # PDF → 이미지
        images = convert_from_path(pdf_path, poppler_path=os.getenv('POPPLER_PATH'))
        update_progress(job_id, 39, f"총 {len(images)}개의 슬라이드 이미지 추출 완료")

        # 이미지 캡셔닝 (40~60%)
        slide_captions = []
        for idx, img in enumerate(images):
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            image_url = f"data:image/jpeg;base64,{img_base64}"

            caption = asyncio.run(analyze_image(image_url))  # async 못 쓰는 곳
            slide_captions.append(caption)

            pct = 40 + int((idx + 1) / len(images) * 20)
            update_progress(job_id, pct, f"{idx + 1}/{len(images)} 슬라이드 캡셔닝 완료")

        update_progress(job_id, 60, "모든 이미지 캡셔닝 완료")

        # 세그먼트 분리
        update_progress(job_id, 65, "강의 내용 세그먼트 분리 중")
        segments = mapper.preprocess_and_split_text(lecture_text)

        # 매핑
        update_progress(job_id, 70, "슬라이드-세그먼트 매핑 중")
        results = mapper.map_lecture_text_to_slides(segments, slide_captions)

        # 중요 세그먼트 추출
        raw_json = {f"segment{i}": seg for i, seg in enumerate(segments)}
        important_segments_result = process_important_segments(raw_json)

        slide_to_segments = {f"slide{i + 1}": [] for i in range(len(slide_captions))}
        for res in results:
            seg_id = f"segment{res['segment_index']}"
            slide_key = f"slide{res['matched_slide_index'] + 1}"
            slide_to_segments[slide_key].append({
                "segment_key": seg_id,
                "text": segments[res["segment_index"]],
                "isImportant": str(seg_id in important_segments_result).lower(),
                "reason": important_segments_result.get(seg_id, {}).get("reason", ""),
                "linkedConcept": "",
                "pageNumber": ""
            })
        sorted_slide_to_segments = OrderedDict(sorted(slide_to_segments.items(), key=lambda x: int(x[0].replace("slide", ""))))

        # 슬라이드별 필기 생성 (75~95%)
        update_progress(job_id, 75, "슬라이드별 필기 생성 시작")
        final_notes = {}

        for i, (slide_key, segment_list) in enumerate(sorted_slide_to_segments.items()):
            idx = int(slide_key.replace("slide", "")) - 1
            matched_texts = [seg["text"] for seg in segment_list]
            note_sections, _ = generate_note(slide_captions[idx], matched_texts)

            note_sections["Segments"] = {
                seg["segment_key"]: {
                    "text": seg["text"],
                    "isImportant": seg["isImportant"],
                    "reason": seg["reason"],
                    "linkedConcept": seg["linkedConcept"],
                    "pageNumber": seg["pageNumber"]
                } for seg in segment_list
            }
            final_notes[slide_key] = note_sections

            save_partial_result(job_id, slide_key, note_sections)

            pct = 75 + int((i + 1) / len(sorted_slide_to_segments) * 20)
            update_progress(job_id, pct, f"{slide_key} 필기 생성 완료")
            asyncio.run(asyncio.sleep(0))  # non-blocking

        # DB 저장
        new_history = History(
            user_email=user_email,
            filename=original_filename,
            notes_json=final_notes,
        )
        db.add(new_history)
        db.commit()
        update_progress(job_id, 100, "전체 작업 완료")
        shutil.rmtree(temp_dir)

    except Exception as e:
        update_progress(job_id, -1, f"에러 발생: {str(e)}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
