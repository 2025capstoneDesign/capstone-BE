import os
import json
import subprocess

from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

def find_longest_staying_slide(meta_data):
    """메타 데이터에서 가장 오래 체류한 슬라이드 찾기"""
    max_duration = 0
    longest_slide = None
    
    # meta_data가 list인 경우와 dict인 경우 모두 처리
    if isinstance(meta_data, list):
        slides_data = meta_data
    else:
        slides_data = meta_data.get('slides', [])
    
    for slide_info in slides_data:
        # start_time과 end_time을 사용해 duration 계산
        if 'start_time' in slide_info and 'end_time' in slide_info:
            start_time = slide_info['start_time']
            end_time = slide_info['end_time']
            
            # "00:05.236" 형식을 초로 변환
            def time_to_seconds(time_str):
                parts = time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            
            duration = time_to_seconds(end_time) - time_to_seconds(start_time)
        else:
            duration = slide_info.get('duration', 0)
        
        if duration > max_duration:
            max_duration = duration
            # slide_id 또는 pageNumber 사용
            longest_slide = slide_info.get('slide_id') or slide_info.get('pageNumber')
    
    return longest_slide


def load_or_create_result_json(job_dir):
    """result.json 로드하거나 새로 생성"""
    result_path = os.path.join(job_dir, "result.json")
    
    if os.path.exists(result_path):
        with open(result_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}

def save_result_json(job_dir, result_data):
    """result.json 저장"""
    result_path = os.path.join(job_dir, "result.json")
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)




def convert_audio_to_m4a_format(input_path: str, output_path: str):
    """ffmpeg로 m4a 형식으로 변환"""
    command = [
        "ffmpeg",
        "-y",  # 기존 파일 덮어쓰기
        "-i", input_path,
        "-c:a", "aac",  # AAC 인코딩
        "-b:a", "192k",  # 비트레이트
        output_path
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg 변환 실패: {e}")

def transcribe_audio_with_timestamps(audio_file_path: str):
    """주어진 오디오 파일을 m4a형식으로 변환 후 STT 진행, 그 결과를 data/realtime_convert_audio에 json형태로 저장"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    
    print(f"API 키가 로드되었습니다: {api_key[:8]}...")
    
    client = OpenAI(api_key=api_key)
    
    output_dir = "data/realtime_convert_audio"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 변환된 m4a 파일 경로
    converted_path = audio_file_path.replace(".wav", "_converted.m4a")
    # wav -> m4a
    convert_audio_to_m4a_format(audio_file_path, converted_path)

    try:
        with open(converted_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
            )
        
        json_data = {
            "text": transcript
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_file = os.path.join(output_dir, f"realtime_stt_result_{timestamp}.json")
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"변환이 완료되었습니다. 결과가 {output_file}에 저장되었습니다.")
        print("JSON 결과:")
        print(json.dumps(json_data, ensure_ascii=False, indent=2))

        return json_data
        
    except Exception as e:
        print(f"오류가 발생했습니다: {str(e)}")
        return None
    finally:
        if os.path.exists(converted_path):
            os.remove(converted_path)



