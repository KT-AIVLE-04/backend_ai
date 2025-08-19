from config.settings import settings
from states.shorts_state import ShortsState
import os
import requests
import time
from typing import List, Dict, Optional, Tuple, Any


def generate_music(state: ShortsState) -> ShortsState:
    suno_url = "https://api.sunoapi.org/api/v1/generate"
    suno_api_key = settings.suno_api_key

    if not state.music_prompt:
        print("Suno 음악 생성 프롬프트 없음\n")
        return state
    
    os.makedirs(state.music_output_dir, exist_ok = True)

    try:
        payload = {
            "prompt": state.music_prompt['prompt'],
            "style": state.music_prompt['style'],
            "title": state.music_prompt['title'],
            "customMode": True,
            "instrumental": True,
            "model": "V4_5PLUS",
            "negativeTags": ', '.join(state.music_prompt['negativeTags']),
            "callBackUrl": "https://api.example.com/callback"
        }

        headers = {
            "Authorization": f"Bearer {suno_api_key}",
            "Content-Type": "application/json"
        }

        print("Suno 음악 생성 시작")
        print("=" * 60)

        response = requests.post(suno_url, json = payload, headers = headers)

        result = response.json()

        task_id = result["data"]["taskId"]

        if not task_id:
            raise Exception("Task ID 없음")

        
        print("음악 생성 중...")
        audio_url_1, audio_url_2 = get_audio_url(task_id, suno_api_key)

        if not audio_url_1 or not audio_url_2:
            raise Exception("오디오 생성 실패")
        

        state.music_urls = [audio_url_1]
        if audio_url_2:
            state.music_urls.append(audio_url_2)

        print("음악 생성 완료")
        print("=" * 60)


        for i, url in enumerate(state.music_urls, 1):
            filename = f"audio_{i}.mp3"
            filepath = os.path.join(state.music_output_dir, filename)
                
            if download_audio_file(url, filepath):
                state.music_files.append(filepath)
                print(f"오디오 파일: {filename} 저장 완료")
        
            else:
                print(f"오디오 파일: {filename} 다운로드 실패")
        
        return state
    
    except Exception as e:
        raise Exception(f"Suno 음악 생성 실패: {str(e)}")




# ================= Helper Functions =================

def get_audio_url(task_id: str, suno_api_key: str) -> Tuple[Optional[str], Optional[str]]:
    url = f"https://api.sunoapi.org/api/v1/generate/record-info?taskId={task_id}"
    headers = {"Authorization": f"Bearer {suno_api_key}"}

    # 시도 횟수
    max_retries = 100
    retries = 0

    while retries < max_retries:
        try:
            response = requests.get(url, headers=headers)
            data = response.json()

            status = data.get('data', {}).get('status')
            print(f"[{retries+1}/{max_retries}] Status: {status}")

            if status in ('PENDING', 'TEXT_SUCCESS', 'FIRST_SUCCESS'):
                time.sleep(10)
                retries += 1
                continue
            
            elif status == 'SUCCESS':
                suno_data = data.get('data', {}).get('response', {}).get('sunoData', [])
                audio_url_1 = suno_data[0].get('audioUrl') if len(suno_data) > 0 else None
                audio_url_2 = suno_data[1].get('audioUrl') if len(suno_data) > 1 else None
                return audio_url_1, audio_url_2

            else:
                return None, None
    
        except Exception as e:
            raise Exception(f"오디오 추출 실패 {e}")

    raise TimeoutError("Suno 오디오 생성 시간 초과")





def download_audio_file(url: str, filename: str) -> bool:
    """오디오 파일 다운로드"""
    try:
        response = requests.get(url)
        response.raise_for_status()

        
        with open(filename, 'wb') as f:
            f.write(response.content)

        print(f"다운로드 완료: {filename}")
      
        return True

    
    except Exception as e:
        print(f"오디오 파일 다운 실패: {e}")
      
        return False
