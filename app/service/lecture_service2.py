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
from app.service.progress_tracker import update_progress, save_result, save_partial_result
from app.service.ai_service import transcribe_audio_file, generate_note, analyze_image, get_libreoffice_path
from app.service.mapping_service import LectureSlideMapper

LIBREOFFICE_PATH = get_libreoffice_path()
mapper = LectureSlideMapper()

async def run_process(job_id: str, audio_path: str, ppt_path: str, skip_transcription: bool):
    try:
        update_progress(job_id, 5, "오디오 파일 저장 시작")

        # 텍스트 변환
        update_progress(job_id, 10, "오디오 → 텍스트 변환 준비")
        if skip_transcription:
            with open(os.path.join("download", "lecture_text.txt"), "r", encoding="utf-8") as f:
                lecture_text = f.read()
        else:
            lecture_text = transcribe_audio_file(audio_path)
        update_progress(job_id, 30, "오디오 텍스트 변환 완료")

        # PPT 저장 및 PDF 변환
        temp_dir = os.path.dirname(audio_path)
        update_progress(job_id, 32, "PPT → PDF 변환 시작")
        subprocess.run([LIBREOFFICE_PATH, "--headless", "--convert-to", "pdf", "--outdir", temp_dir, ppt_path], check=True)
        pdf_filename = os.path.splitext(os.path.basename(ppt_path))[0] + ".pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)
        if not os.path.exists(pdf_path):
            raise Exception("PDF 변환 실패")
        update_progress(job_id, 36, "PPT → PDF 변환 완료")

        # PDF → 이미지
        update_progress(job_id, 40, "PDF → 이미지 변환 중")
        images = convert_from_path(
            pdf_path,
            poppler_path=r"C:\Program Files\Poppler\poppler-24.08.0\Library\bin"
        )
        update_progress(job_id, 50, "PDF → 이미지 변환 완료")

        # 이미지 캡셔닝
        update_progress(job_id, 55, "이미지 캡셔닝 시작")
        slide_captions = []
        for idx, img in enumerate(images):
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            image_url = f"data:image/jpeg;base64,{img_base64}"
            caption = await analyze_image(image_url)
            slide_captions.append(caption)
            update_progress(job_id, 56 + int((idx+1) / len(images) * 4), f"{idx+1}/{len(images)} 슬라이드 캡셔닝 완료")

        update_progress(job_id, 60, "모든 이미지 캡셔닝 완료")

        # 세그먼트 분리
        update_progress(job_id, 65, "세그먼트 분리 중")
        segments = mapper.preprocess_and_split_text(lecture_text)

        # 슬라이드-세그먼트 매핑
        update_progress(job_id, 70, "슬라이드-세그먼트 매핑 중")
        results = mapper.map_lecture_text_to_slides(segment_texts=segments, slide_texts=slide_captions)

        slide_to_segments = {f"slide{i+1}": [] for i in range(len(slide_captions))}
        for res in results:
            segment_idx = res["segment_index"]
            slide_idx = res["matched_slide_index"]
            similarity_score = res["similarity_score"]
            slide_key = f"slide{slide_idx+1}"
            slide_to_segments[slide_key].append({
                "segment_index": segment_idx,
                "text": segments[segment_idx],
                "similarity_score": round(similarity_score, 4)
            })

        sorted_slide_to_segments = OrderedDict(sorted(slide_to_segments.items(), key=lambda x: int(x[0].replace("slide", ""))))

        # 슬라이드별 GPT 필기 생성
        update_progress(job_id, 75, "슬라이드별 필기 생성 중")
        for i, (slide_key, segment_list) in enumerate(sorted_slide_to_segments.items()):
            slide_idx = int(slide_key.replace("slide", "")) - 1
            slide_caption = slide_captions[slide_idx]
            matched_segment_texts = [seg["text"] for seg in segment_list]
            note_sections, _ = generate_note(slide_caption, matched_segment_texts)

            # 점진적 저장
            save_partial_result(job_id, slide_key, note_sections)

            # 점진적 진행률 증가
            pct = 75 + int((i + 1) / len(sorted_slide_to_segments) * 25)
            update_progress(job_id, pct, f"{slide_key} 필기 생성 완료")
            await asyncio.sleep(0)

        update_progress(job_id, 100, "작업 완료")

        shutil.rmtree(temp_dir)

    except Exception as e:
        update_progress(job_id, -1, f"에러 발생: {str(e)}")
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
