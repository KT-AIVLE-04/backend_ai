from states.shorts_state import ShortsState
import os
import re
import json
import time
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter
import cv2
import numpy as np
from scipy import signal
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d


def analyze_final_video(state: ShortsState) -> ShortsState:
    """영상 분석 (오디오 생성에 사용)"""

    if not os.path.exists(state.final_video_path):
        raise FileNotFoundError(f"비디오 파일 없음: {state.final_video_path}")

    
    print("영상 분석 시작")
    print("=" * 60)


    # 비디오 정보 추출
    video_info = get_video_info_safe(state.final_video_path)

    # 프레임 샘플링
    sample_strategy = determine_sampling_strategy(video_info)

    # 분석 수행
    cap = cv2.VideoCapture(state.final_video_path)

    # 분석 데이터 컨테이너
    analysis_data = {
        'brightness': [],
        'color_temps': [],
        'motion': [],
        'hue_values': [],
        'saturation': [],
        'energy_timeline': []
    }

    prev_frame = None
    frame_count = 0
    samples_taken = 0

    while cap.isOpened() and samples_taken < sample_strategy['max_samples']:
        ret, frame = cap.read()
        if not ret:
            break

        # 샘플링 여부 결정
        if frame_count % sample_strategy['interval'] == 0:
            analysis_data = analyze_frame(frame, prev_frame, analysis_data,frame_count, video_info['fps'])
            prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            samples_taken += 1

        frame_count += 1

    
    cap.release()

    # 분석 결과 후처리
    result = process_analysis_results(analysis_data, video_info)
    
    state.video_analysis = result
    print("\n영상 분석 완료")

    return state




# ================= Helper Functions =================

def get_video_info_safe(video_path: str) -> dict:
    """비디오 정보 추출"""
    
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise Exception(f"Cannot open video: {video_path}")

    # 메타데이터
    info = {
        'nframes': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        'fps': cap.get(cv2.CAP_PROP_FPS),
        'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        'fourcc': int(cap.get(cv2.CAP_PROP_FOURCC))
    }

    # FPS 검증 및 보정
    if info['fps'] <= 0 or info['fps'] > 120:
        # 일반적인 FPS 값으로 추정
        common_fps = [23.976, 24, 25, 29.97, 30, 50, 59.94, 60]
        info['fps'] = 30.0  # 기본값
        
        print(f"FPS 추정 사용: {info['fps']}")

    # Duration
    info['duration'] = info['nframes'] / info['fps'] if info['fps'] > 0 else 0

    cap.release()
    
    return info



def determine_sampling_strategy(video_info: dict) -> dict:
    """샘플링 전략"""
    duration = video_info['duration']
    fps = video_info['fps']
    
    if duration < 15:
        # 15초 내: 2프레임마다
        return {'interval': 2, 'max_samples': 200}
        
    else:
        # 15초 이상: FPS/10 간격 (= 2)
        return {'interval': max(1, int(fps/10)), 'max_samples': 500}



def analyze_frame(frame: np.ndarray, 
                  prev_frame: Optional[np.ndarray],
                  analysis_data: dict, 
                  frame_num: int, 
                  fps: float) -> dict:
    """단일 프레임 분석"""

    # 색공간 변환
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

    # 1. 밝기 분석 (LAB 색공간 사용)
    brightness = np.mean(lab[:, :, 0]) / 255.0
    analysis_data['brightness'].append(brightness)

    
    # 2. 색온도 분석
    color_temp = calculate_color_temperature(rgb)
    analysis_data['color_temps'].append(color_temp)

    
    # 3. HSV 분석
    hue_mean = np.mean(hsv[:, :, 0])
    saturation_mean = np.mean(hsv[:, :, 1]) / 255.0
    analysis_data['hue_values'].append(hue_mean)
    analysis_data['saturation'].append(saturation_mean)

    
    # 4. 모션 분석
    if prev_frame is not None:
        motion = calculate_motion_intensity(gray, prev_frame)
        analysis_data['motion'].append(motion)

        # 에너지 분석
        energy = motion * saturation_mean * brightness
        analysis_data['energy_timeline'].append({
            'time': frame_num / fps,
            'energy': energy,
            'motion': motion
        })

    return analysis_data



def calculate_color_temperature(rgb_frame: np.ndarray) -> float:
    """색온도 계산"""
    
    # 평균 RGB 값
    r_mean = np.mean(rgb_frame[:, :, 0])
    # g_mean = np.mean(rgb_frame[:, :, 1])
    b_mean = np.mean(rgb_frame[:, :, 2])

    # 색온도 추정 (McCamy's formula 근사)
    if b_mean > 0:
        # R/B 비율 기반
        rb_ratio = r_mean / b_mean

        # 켈빈 온도로 변환
        if rb_ratio > 1.5:
            return 3000  # Warm (3000K)
        
        elif rb_ratio < 0.6:
            return 6500  # Cool (6500K)
        
        else:
            # 선형 보간
            return 3000 + (rb_ratio - 0.6) * (3500 / 0.9)

    
    return 5000  # 없다면 중성 (5000K)



def calculate_motion_intensity(current: np.ndarray,
                               previous: np.ndarray) -> float:
    """모션 강도 계산"""
    
    # 광학 흐름 또는 프레임 차이
    diff = cv2.absdiff(current, previous)

    # 노이즈 제거
    diff = cv2.GaussianBlur(diff, (5, 5), 0)

    # threshold 적용
    _, thresh = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)

    # 모션 영역 비율
    motion_ratio = np.sum(thresh > 0) / (thresh.shape[0] * thresh.shape[1])

    # Normalization
    return min(1.0, motion_ratio * 10)  

    
    
def analyze_rhythm_advanced(motion_data: List[float],
                            fps: float) -> Dict[str, float]:
    """리듬 분석"""

    if len(motion_data) < 10:
        return {
            'tempo': 100,
            'tempo_confidence': 0.3,
            'beat_strength': 0.5,
            'rhythm_regularity': 0.5
        }

    # 신호 전처리
    motion_array = np.array(motion_data)

    # 스무딩
    smoothed = gaussian_filter1d(motion_array, sigma = 1)

    # 피크 검출
    peaks, properties = find_peaks(smoothed, height = np.mean(smoothed), distance = fps/4)

    if len(peaks) > 1:
        # 피크 간격으로 BPM 계산
        peak_intervals = np.diff(peaks) / fps  # 초 단위
        avg_interval = np.mean(peak_intervals)
        bpm = 60 / avg_interval if avg_interval > 0 else 100

        # 템포 신뢰도 (피크 간격 일관성)
        interval_std = np.std(peak_intervals)
        tempo_confidence = 1 / (1 + interval_std) if interval_std >= 0 else 0.5

        # 비트 강도
        beat_strength = np.mean(properties['peak_heights']) / np.max(smoothed) if np.max(smoothed) > 0 else 0.5

        # 리듬 규칙성
        rhythm_regularity = 1 - (interval_std / (avg_interval + 1e-6))
    
    else:
        bpm = 100
        tempo_confidence = 0.3
        beat_strength = 0.3
        rhythm_regularity = 0.3

    
    return {
        'tempo': np.clip(bpm, 40, 200),
        'tempo_confidence': np.clip(tempo_confidence, 0, 1),
        'beat_strength': np.clip(beat_strength, 0, 1),
        'rhythm_regularity': np.clip(rhythm_regularity, 0, 1)
    }



def extract_color_palette(hue_values: List[float],
                          saturation_values: List[float]) -> List[str]:
    """색상 팔레트 추출"""
    
    if not hue_values:
        return ['neutral']

    # HSV Hue를 색상 카테고리로 변환
    color_names = []
    for hue in hue_values:
        if 0 <= hue < 20 or 340 <= hue:
           color_names.append('red')
        
        elif 20 <= hue < 45:
           color_names.append('orange')
        
        elif 45 <= hue < 65:
           color_names.append('yellow')
        
        elif 65 <= hue < 150:
           color_names.append('green')
        
        elif 150 <= hue < 200:
            color_names.append('cyan')
        
        elif 200 <= hue < 260:
            color_names.append('blue')
        
        elif 260 <= hue < 340:
            color_names.append('purple')

    # 가장 많이 등장하는 색상
    color_counter = Counter(color_names)
    dominant_colors = [color for color, _ in color_counter.most_common(3)]

    
    # 채도 기반 보정
    avg_saturation = np.mean(saturation_values)
    
    if avg_saturation < 0.2:
        dominant_colors.insert(0, 'desaturated')
    
    elif avg_saturation > 0.7:
        dominant_colors.insert(0, 'vibrant')

    
    return dominant_colors



def process_analysis_results(analysis_data: dict,
                             video_info: dict) -> dict:
    """분석 결과 처리 및 통합"""

    # 밝기
    avg_brightness = np.mean(analysis_data['brightness']) if analysis_data['brightness'] else 0.5
    brightness_variance = np.var(analysis_data['brightness']) if analysis_data['brightness'] else 0.1

    # 색온도
    color_temps = analysis_data['color_temps']
    avg_color_temp = np.mean(color_temps) if color_temps else 5000

    # 모션
    motion_data = analysis_data['motion']
    avg_motion = np.mean(motion_data) if motion_data else 0.1

    # 리듬 패턴
    rhythm_pattern = analyze_rhythm_advanced(motion_data, video_info['fps'])

    # 색상 팔레트
    color_palette = extract_color_palette(analysis_data['hue_values'], analysis_data['saturation'])

    # 에너지 커브
    energy_curve = [e['energy'] for e in analysis_data['energy_timeline']]

    # 모션 피크
    motion_peaks = find_motion_peaks(motion_data, video_info['fps'])

    # 시각적 에너지 
    visual_energy = calculate_visual_energy(avg_motion, brightness_variance, rhythm_pattern['beat_strength'])

    # 무드
    dominant_moods = extract_mood(avg_brightness, avg_color_temp, avg_motion, color_palette)

    # 장면 전환 감지
    scene_transitions = detect_scene_changes(motion_data, analysis_data['brightness'], video_info['fps'])

    
    return {
        'duration': video_info['duration'],
        'fps': video_info['fps'],
        'avg_brightness': avg_brightness,
        'brightness_variance': brightness_variance,
        'avg_color_temp': avg_color_temp,
        'motion_intensity': avg_motion,
        'visual_energy': np.clip(visual_energy, 0, 100),
        'scene_transitions': scene_transitions,
        'dominant_colors': dominant_moods,
        'rhythm_pattern': rhythm_pattern,
        'tempo_confidence': rhythm_pattern['tempo_confidence'],
        'color_palette': color_palette,
        'motion_peaks': motion_peaks,
        'energy_curve': energy_curve
    }



def detect_scene_changes(motion_data: List[float],
                         brightness_data: List[float],
                         fps: float) -> List[float]:
    """장면 전환 감지"""
    
    scene_changes = []

    if len(motion_data) < 2:
      return scene_changes

    # 모션 & 밝기 변화 결합
    for i in range(1, len(motion_data)):
        motion_change = abs(motion_data[i] - motion_data[i-1])
        brightness_change = abs(brightness_data[i] - brightness_data[i-1])

        # 복합 변화 점수
        change_score = motion_change * 0.6 + brightness_change * 0.4

        # 임계값 초과 시 장면 전환
        if change_score > 0.3:
            scene_changes.append(i / fps)

    return scene_changes



def find_motion_peaks(motion_data: List[float],
                      fps: float) -> List[float]:
    """모션 피크 시점 찾기"""
    
    if len(motion_data) < 3:
        return []

    from scipy.signal import find_peaks

    motion_array = np.array(motion_data)
    peaks, _ = find_peaks(motion_array,
                          height = np.mean(motion_array) + np.std(motion_array),
                          distance = int(fps/2))  # 최소 0.5초 간격

    return [p / fps for p in peaks]



def calculate_visual_energy(motion: float,
                            brightness_var: float,
                            beat_strength: float) -> float:
    """시각적 에너지 계산"""
    # 가중치 적용
    energy = (
        motion * 0.4 +
        brightness_var * 0.3 +
        beat_strength * 0.3) * 100

    return np.clip(energy, 0, 100)



def extract_mood(brightness: float,
                 color_temp: float,
                 motion: float,
                 colors: List[str]) -> List[str]:
    """종합적인 무드 추출"""
    
    moods = []

    # 밝기 기반
    if brightness > 0.7:
        moods.append('bright')
    elif brightness < 0.3:
        moods.append('dark')

    # 색온도 기반
    if color_temp < 4000:
        moods.append('warm')
    elif color_temp > 6000:
        moods.append('cool')

    # 모션 기반
    if motion > 0.5:
        moods.append('dynamic')
    elif motion < 0.1:
        moods.append('calm')

    # 색상 기반
    if 'vibrant' in colors:
        moods.append('energetic')
    if 'desaturated' in colors:
        moods.append('subtle')

    
    return moods if moods else ['neutral']