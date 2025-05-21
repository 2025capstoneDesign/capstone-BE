import os
import shutil
import json
from sqlalchemy.orm import Session
from app.model.history import History
from app.api.ai import transcribe_audio
from app.service2.segment_splitter import segment_split
from app.service2.image_captioning import analyze_image, convert_pdf_to_images, image_captioning
from app.service2.segment_mapping import segment_mapping
from app.service2.summary import generate_summary
from app.service2.progress_tracker2 import update_progress, save_partial_result

def run_process_v2(
    job_id: str,
    audio_path: str,
    doc_path: str,
    skip_transcription: bool,
    original_filename: str,
    user_email: str,
    db: Session
):
    try:
        update_progress(job_id, 5, "파일 준비 완료")

        # 1. STT
        if skip_transcription:
            stt_dir = "data/stt_result"
            stt_files = [f for f in os.listdir(stt_dir) if f.startswith("stt_result")]
            if stt_files:
                latest_stt = max(stt_files)
                with open(os.path.join(stt_dir, latest_stt), 'r', encoding='utf-8') as f:
                    stt_result = json.load(f)
        else:
            update_progress(job_id, 10, "오디오 텍스트 변환 중")
            stt_result = transcribe_audio(audio_path)
        update_progress(job_id, 30, "STT 완료")

        # 2. 세그먼트 분리
        segments = segment_split(stt_data=stt_result)
        if isinstance(segments, dict) and "segments" in segments:
            segments = segments["segments"]
        update_progress(job_id, 35, "세그먼트 분리 완료")

        # 3. 이미지 캡셔닝 (40% → 60%)
        update_progress(job_id, 40, "이미지 캡셔닝 시작")

        encoded_images = convert_pdf_to_images(doc_path)
        total_slides = len(encoded_images)
        captioning = []

        for i, img_str in enumerate(encoded_images):
            image_url = f"data:image/jpeg;base64,{img_str}"

            analysis = analyze_image(image_url)

            result = {
                "slide_number": i + 1,
                "type": analysis["type"],
                "title_keywords": analysis["title_keywords"],
                "secondary_keywords": analysis["secondary_keywords"],
                "detail": analysis["detail"]
            }
            captioning.append(result)

            pct = 40 + int((i + 1) / total_slides * 20)
            update_progress(job_id, pct, f"{i + 1}/{total_slides} 슬라이드 캡셔닝 완료")

        update_progress(job_id, 60, "이미지 캡셔닝 완료")

        # 4. 세그먼트-슬라이드 매핑
        mapping = segment_mapping(
            image_captioning_data=captioning,
            segment_split_data=segments
        )
        update_progress(job_id, 65, "슬라이드-세그먼트 매핑 완료")

        # 5. 슬라이드별 필기 생성 (70% → 90%)
        update_progress(job_id, 70, "슬라이드별 필기 생성 시작")

        structured_result = {}
        filtered_mapping = {k: v for k, v in mapping.items() if k != "slide0"}
        total = len(filtered_mapping)

        for i, (slide_key, segments_data) in enumerate(filtered_mapping.items()):
            idx = int(slide_key.replace("slide", "")) - 1
            if idx >= len(captioning):
                continue

            merged_segments = "\n".join(
                seg_val.get("text", "") for seg_val in segments_data.get("Segments", {}).values()
            )

            slide_caption = captioning[idx]

            summary_data = generate_summary(slide_caption, merged_segments)

            structured_result[slide_key] = {
                "Concise Summary Notes": f"🧠Concise Summary Notes\n{summary_data['concise_summary']}",
                "Bullet Point Notes": f"✅Bullet Point Notes\n{summary_data['bullet_points']}",
                "Keyword Notes": f"🔑Keyword Notes\n{summary_data['keywords']}",
                "Chart/Table Summary": f"📊Chart/Table Summary\n{summary_data['chart_summary']}",
                "Segments": {
                    seg_id: {
                        "text": seg_val.get("text", ""),
                        "isImportant": "false",
                        "reason": "",
                        "linkedConcept": "",
                        "pageNumber": ""
                    } for seg_id, seg_val in segments_data.get("Segments", {}).items()
                }
            }

            save_partial_result(job_id, slide_key, structured_result[slide_key])

            pct = 70 + int((i + 1) / total * 20)  # 최대 90%
            update_progress(job_id, pct, f"{slide_key} 필기 생성 완료")

        # 6. DB 저장 및 종료
        new_history = History(
            user_email=user_email,
            filename=original_filename,
            notes_json=structured_result,
        )
        db.add(new_history)
        db.commit()

        update_progress(job_id, 100, "전체 작업 완료")
        shutil.rmtree(os.path.dirname(audio_path))

    except Exception as e:
        update_progress(job_id, -1, f"에러 발생: {str(e)}")
        if os.path.exists(os.path.dirname(audio_path)):
            shutil.rmtree(os.path.dirname(audio_path))
