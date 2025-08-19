from config.settings import settings
from states.shorts_state import ShortsState
import os
import re
import json
import requests
import random
import time
from datetime import datetime
import shutil
from typing import List, Dict, Optional, Any
from moviepy.editor import VideoFileClip, VideoClip
import replicate


def generate_video_series(state: ShortsState) -> ShortsState:
    client_video = replicate.Client(api_token = settings.replicate_api_key)

    os.makedirs("./temp", exist_ok = True)
    os.makedirs(state.output_dir, exist_ok = True)

    if not state.seedance_results:
        print("Seedance 프롬프트 없음")
        return state
    
    
    state.video_urls = []
    state.video_files = []
    base_seed = int(time.time())

    print("Seedance 비디오 생성 시작")
    print("=" * 60)

    num_segments = len(state.seedance_results)

    for i in range(num_segments):
        prompt = state.seedance_results[i]["main_prompt"]
        start_image = state.scenes_image_list[i]

        last_image = ""
        if i < num_segments - 1:
            last_image = state.scenes_image_list[i + 1]

        
        video_url = generate_video_segment(
            client_video = client_video,
            prompt = prompt,
            start_image_path = start_image,
            last_image_path = last_image,
            seed = base_seed + (i * 1000)
        )

        
        if video_url:
            print(f"Scene {i+1} URL: {video_url}\n")
            state.video_urls.append(video_url)

            filename = f"scene_{i+1}.mp4"
            filepath = os.path.join(state.output_dir, filename)

            if download_video(safe_get_url(video_url), filepath):
                state.video_files.append(filepath)

            # Replicate API 호출 과부화 방지
            time.sleep(2)

    
    state.final_video_path = process_video_sequence(
        video_paths = state.video_files,
        fade_duration = 0.8,
        last_fadeout_duration = 2.5,
        fade_type = 'ease_in_out',
        output_path = "complete_video_no_audio.mp4"
    )

    return state


# ============= Helper Functions (Video Generation) =============

def generate_video_segment(client_video, 
                           prompt: str,
                           start_image_path: str,
                           last_image_path: str,
                           seed: Optional[int] = None) -> Optional[str]:
    if(last_image_path != ""):
        try:
            # Seedance-1-lite 모델
            output = client_video.run(
                "bytedance/seedance-1-lite",
                input = {
                    "prompt": prompt.strip(),
                    "image": start_image_path,
                    "last_frame_image": last_image_path,
                    "duration": 5,
                    "resolution": "1080p",
                    "aspect_ratio": "9:16",
                    "fps": 24,
                    "seed": seed if seed else int(time.time())
                }
            )

            return safe_get_url(output)

        except Exception as e:
            raise Exception(f"영상 생성 오류: {e}")

    else:
        try:
            # Seedance-1-lite 모델
            output = client_video.run(
                "bytedance/seedance-1-lite",
                input = {
                    "prompt": prompt.strip(),
                    "image": start_image_path,
                    "duration": 5,
                    "resolution": "1080p",
                    "aspect_ratio": "9:16",
                    "fps": 24,
                    "seed": seed if seed else int(time.time())
                }
            )
            
            return safe_get_url(output)

        except Exception as e:
            raise Exception(f"영상 생성 오류: {e}")



def safe_get_url(output):
    """비디오 결과 URL 추출"""
    if output is None:
        return None

    if isinstance(output, str):
        return output

    elif isinstance(output, list) and len(output) > 0:
        return output[0]

    elif hasattr(output, 'url'):
        return output.url if isinstance(output.url, str) else str(output.url)

    elif hasattr(output, '__iter__'):
        return next(iter(output), None)

    else:
        return str(output)



def download_video(url: str, filename: str, retries: int = 5, delay: int = 5) -> bool:
    """비디오 다운로드 (재시도 포함)"""
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"영상 다운로드 완료: {filename}")
            return True
        except Exception as e:
            print(f"[시도 {attempt}/{retries}] 다운로드 오류: {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                return False




# ============= Helper Functions (Video Edition) =============

def process_video_sequence(video_paths: List[str],
                           fade_duration: float = 0.7,
                           last_fadeout_duration: float = 2.0,
                           fade_type: str = 'ease_in_out',
                           output_path: str = "complete_video_no_audio.mp4",
                           temp_dir: str = "temp_processing") -> str:
    """영상 시퀀스 처리"""

    fade_functions = {
        'ease_in_out': lambda t: 3*t**2 - 2*t**3,
        'ease_in': lambda t: t**2,
        'ease_out': lambda t: 1 - (1-t)**2,
        'linear': lambda t: t
    }

    os.makedirs(temp_dir, exist_ok = True)

    try:
        # 1단계: 모든 영상 해상도 확인
        resolutions = []
        for i, path in enumerate(video_paths):
            if not os.path.exists(path):
                raise FileNotFoundError(f"영상 파일을 찾을 수 없습니다: {path}")

            clip = VideoFileClip(path)
            resolutions.append(clip.size)

            print(f"파일 확인 ({i+1}/{len(video_paths)}): {os.path.basename(path)} - {clip.size}")

            clip.close()

        # 2단계: 목표 해상도 지정 (가장 작은 해상도 통일)
        min_width = min(res[0] for res in resolutions)
        min_height = min(res[1] for res in resolutions)
        target_resolution = (min_width, min_height)

        print(f"지정 해상도: {target_resolution}")

        # 3단계: 첫 번째 클립 처리
        current_output = os.path.join(temp_dir, "temp_0.mp4")
        first_clip = VideoFileClip(video_paths[0]).resize(target_resolution)

        first_clip.write_videofile(
            current_output,
            codec = 'libx264',
            audio_codec = 'aac',
            fps = 24,
            bitrate = '12000k',
            preset = 'medium',
            verbose = False,
            logger = None
        )

        first_clip.close()

        # 4단계: 순차적 크로스페이드 적용
        for i in range(1, len(video_paths)):
            prev_output = current_output
            current_output = os.path.join(temp_dir, f"temp_{i}.mp4")

            clip1 = VideoFileClip(prev_output)
            clip2 = VideoFileClip(video_paths[i]).resize(target_resolution)

            result = apply_crossfade(clip1, clip2, fade_duration, fade_functions[fade_type])

            result.write_videofile(
                current_output,
                codec = 'libx264',
                audio_codec = 'aac',
                fps = 24,
                bitrate = '12000k',
                preset = 'medium',
                verbose = False,
                logger = None
            )

            clip1.close()
            clip2.close()

            result.close()

            if os.path.exists(prev_output):
                os.remove(prev_output)

            print(f"진행률: {i}/{len(video_paths)-1} 완료")

        # 5단계: 페이드아웃 적용
        final_clip = VideoFileClip(current_output)
        faded_clip = apply_fadeout(final_clip, last_fadeout_duration, fade_functions[fade_type])

        faded_clip.write_videofile(
            output_path,
            codec = 'libx264',
            audio_codec = 'aac',
            fps = 24,
            bitrate = '12000k',
            preset = 'medium',
            verbose = False,
            logger = None
        )

        final_clip.close()
        faded_clip.close()

        return output_path

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        print("임시 파일 정리 완료")



def apply_crossfade(clip1: VideoFileClip, clip2: VideoFileClip, fade_duration: float, fade_func) -> VideoClip:
    """클립들간 크로스페이드 적용"""

    def make_frame(t):
        if t < clip1.duration - fade_duration:
            return clip1.get_frame(t)
        
        elif t < clip1.duration:
            progress = (t - (clip1.duration - fade_duration)) / fade_duration
            alpha = fade_func(progress)

            frame1 = clip1.get_frame(t)
            frame2 = clip2.get_frame(t - (clip1.duration - fade_duration))

            # 안전성 검사
            if frame1.shape != frame2.shape:
                print(f"프레임 크기 불일치: {frame1.shape} vs {frame2.shape}")
                
                # 더 작은 크기에 맞춤
                min_h = min(frame1.shape[0], frame2.shape[0])
                min_w = min(frame1.shape[1], frame2.shape[1])
                frame1 = frame1[:min_h, :min_w]
                frame2 = frame2[:min_h, :min_w]

            return (1 - alpha) * frame1 + alpha * frame2
        
        else:
            return clip2.get_frame(t - (clip1.duration - fade_duration))

    duration = clip1.duration + clip2.duration - fade_duration
    crossfaded = VideoClip(make_frame, duration=duration)
    crossfaded = crossfaded.set_fps(clip1.fps)

    return crossfaded



def apply_fadeout(clip: VideoClip, last_fadeout_duration: float, fade_func) -> VideoClip:
    """마지막 클립 페이드아웃 적용"""

    def make_frame(t):
        frame = clip.get_frame(t)

        if t >= clip.duration - last_fadeout_duration:
            progress = (clip.duration - t) / last_fadeout_duration
            alpha = fade_func(progress)
            return frame * alpha

        return frame

    faded = VideoClip(make_frame, duration=clip.duration)
    faded = faded.set_fps(clip.fps)

    return faded
