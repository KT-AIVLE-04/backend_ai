from config.settings import settings
from states.shorts_state import ShortsState
import os
import re
import json
import copy
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import anthropic


def generate_suno_music_prompt(state: ShortsState) -> ShortsState:
    if not state.video_analysis:
        print("비디오 분석 결과를 확인할 수 없음\n")
        return state
    
    client = anthropic.Anthropic(api_key = settings.claude_api_key)

    context = {
        'industry': state.business_type.lower(),
        'brand': state.store_name,
        'target': state.target_audience,
        'brand_concept': state.brand_concept
    }

    # 템플릿 선택
    template = select_and_adjust_template(context['industry'], state.video_analysis)


    # 특징 추출 (기존 템플릿 정보와 병합)
    advanced_features = extract_advanced_features(state.video_analysis)
    template = merge_advanced_features(template, advanced_features)


    print("Suno 음악 생성 프롬프트 생성 시작")
    print("=" * 60)

    suno_data = generate_prompt(client, template, state.video_analysis, context)

    optimized_data = optimize_for_suno(suno_data, template)

    validation = validate_suno_prompt(optimized_data)

    metadata = generate_metadata(template, state.video_analysis, validation, context['industry'])

    alternatives = generate_alternatives(optimized_data, template)

    
    state.music_prompt = optimized_data
    state.music_alternatives = alternatives

    print("\n음악 프롬프트 생성 완료")

    
    return state




# ================= Helper Functions =================

# in-memory 형식으로 변경 예정
industry_templates = {
    'beauty': {
        'base_style': 'elegant luxurious feminine fresh',
        'suno_styles': ['ambient', 'cinematic', 'pop'],
        'core_instruments': ['piano', 'strings', 'harp', 'soft synth'],
        'mood_descriptors': ['graceful', 'polished', 'dreamy', 'sophisticated', 'fresh', 'clean'],
        'tempo_range': (75, 110),
        'energy': 'soft-moderate',
        'avoid_elements': ['aggressive drums', 'distorted guitar', 'heavy bass', 'heavy metal', 'dark ambient']
    },
    'fashion': {
        'base_style': 'modern stylish confident',
        'suno_styles': ['electronic', 'pop'],
        'core_instruments': ['synth bass', 'electronic drums', 'electric piano'],
        'mood_descriptors': ['edgy', 'bold', 'runway', 'chic'],
        'tempo_range': (115, 130),
        'energy': 'high',
        'avoid_elements': ['folk instruments', 'classical orchestra', 'country']
    },
    'food': {
        'base_style': 'warm cozy organic',
        'suno_styles': ['folk', 'indie'],
        'core_instruments': ['acoustic guitar', 'ukulele', 'soft drums'],
        'mood_descriptors': ['inviting', 'fresh', 'homey', 'joyful'],
        'tempo_range': (85, 110),
        'energy': 'comfortable',
        'avoid_elements': ['industrial', 'harsh synth', 'metal']
    },
    'cafe': {
        'base_style': 'relaxed warm acoustic',
        'suno_styles': ['jazz', 'indie', 'folk'],
        'core_instruments': ['acoustic guitar', 'soft piano', 'brushed drums', 'double bass'],
        'mood_descriptors': ['cozy', 'intimate', 'mellow', 'welcoming', 'smooth'],
        'tempo_range': (70, 95),
        'energy': 'gentle',
        'avoid_elements': ['heavy electric guitar', 'aggressive drums', 'loud synth', 'industrial']
    },
    'technology': {
        'base_style': 'futuristic innovative digital',
        'suno_styles': ['electronic', 'experimental'],
        'core_instruments': ['synthesizer', 'vocoder', 'digital drums'],
        'mood_descriptors': ['cutting-edge', 'precise', 'dynamic'],
        'tempo_range': (120, 140),
        'energy': 'intense',
        'avoid_elements': ['acoustic', 'vintage', 'organic']
    }
}

def select_and_adjust_template(industry: str, 
                               analysis: Dict[str, Any]) -> Dict[str, Any]:
    """업종별 템플릿 선택 및 비디오 분석 미세 조정"""

    # 기본 템플릿 선택
    base_template = industry_templates.get(industry, industry_templates['technology'])

    # Deep copy로 안전한 수정
    template = copy.deepcopy(base_template)

    # 1. BPM 조정
    video_tempo = analysis.get('rhythm_pattern', {}).get('tempo', 100)
    confidence = analysis.get('tempo_confidence', 0.5)

    if confidence > 0.7:
        # 높은 신뢰도: 비디오 템포 사용
        template['detected_bpm'] = int(round(video_tempo / 5) * 5)

    else:
        # 낮은 신뢰도: 템플릿 범위 중간값
        min_bpm, max_bpm = template['tempo_range']
        template['detected_bpm'] = (min_bpm + max_bpm) // 2

    
    # 2. 에너지 레벨 조정
    visual_energy = analysis.get('visual_energy', 50)
    
    if visual_energy > 70:
        template['energy'] = 'intense'
        template['mood_descriptors'].append('energetic')

    elif visual_energy < 30:
        template['energy'] = 'soft'
        template['mood_descriptors'].append('calm')

    
    # 3. 밝기 기반 무드 조정
    brightness = analysis.get('avg_brightness', 0.5)

    if brightness > 0.7:
        template['mood_descriptors'].extend(['bright', 'uplifting'])

    elif brightness < 0.3:
        template['mood_descriptors'].extend(['dark', 'moody'])


    # 4. 장면 전환 빈도 기반 구조 조정
    transitions_per_minute = len(analysis.get('scene_transitions', [])) * 60 / analysis.get('duration', 30)
    
    if transitions_per_minute > 10:
        template['structure_hint'] = 'dynamic fast-paced'

    elif transitions_per_minute < 3:
        template['structure_hint'] = 'ambient slow-evolving'

    else:
        template['structure_hint'] = 'balanced progression'


    # 중복 제거
    template['mood_descriptors'] = list(set(template['mood_descriptors']))

    return template



def extract_advanced_features(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """음악 특징 추출"""

    features = {}

    # 1. 에너지 패턴 분석
    energy_curve = analysis.get('energy_curve', [])
    
    if energy_curve and len(energy_curve) > 3:
        energy_array = np.array(energy_curve)
        
        gradient = np.gradient(energy_array)
        
        mean_gradient = np.mean(gradient)
            
        if mean_gradient > 0.1:
            features['progression'] = 'building'
        
        elif mean_gradient < -0.1:
            features['progression'] = 'fading'
            
        else:
            features['progression'] = 'steady'
            
        
        features['dynamic_range'] = np.std(energy_array)

    
    # 2. 리듬 패턴
    motion_peaks = analysis.get('motion_peaks', [])

    if motion_peaks:
        features['rhythm_intensity'] = len(motion_peaks) / analysis.get('duration', 30)


    # 3. 색상 기반 감정
    dominant_colors = analysis.get('dominant_colors', [])

    if dominant_colors:
        warm_colors = sum(1 for c in dominant_colors if c in ['warm', 'bright', 'energetic'])
        cool_colors = sum(1 for c in dominant_colors if c in ['cool', 'dark', 'calm'])

        if warm_colors > cool_colors:
            features['color_emotion'] = 'warm'
        
        elif cool_colors > warm_colors:
            features['color_emotion'] = 'cool'
            
        else:
            features['color_emotion'] = 'neutral'

    return features



def merge_advanced_features(template: Dict[str, Any],
                            features: Dict[str, Any]) -> Dict[str, Any]:
    """특징 + 템플릿 병합"""

    merged = template.copy()

    # 진행 패턴 반영
    progression = features.get('progression', 'steady')

    if progression == 'building':
        merged['arrangement'] = 'crescendo build-up'
   
    elif progression == 'fading':
        merged['arrangement'] = 'diminuendo fade-out'
    
    else:
        merged['arrangement'] = 'steady flow'
    
    
    # 다이나믹 레인지 반영
    dynamic_range = features.get('dynamic_range', 0)
    
    if dynamic_range > 0.5:
        merged['dynamics'] = 'wide dynamic range'
    
    else:
        merged['dynamics'] = 'compressed consistent'

    
    # 색상 감정 반영
    color_emotion = features.get('color_emotion', 'neutral')

    if color_emotion == 'warm':
        merged['tone'] = 'warm analog'
    
    elif color_emotion == 'cool':
        merged['tone'] = 'cool digital'

    
    return merged



def generate_prompt(client: anthropic.Anthropic,
                    template: Dict[str, Any],
                    analysis: Dict[str, Any],
                    context: Dict[str, Any]) -> Dict[str, Any]:
    """Suno 프롬프트 생성"""

    system_prompt = """
    You are a Suno AI music prompt expert. Suno prefers CONCISE, FOCUSED prompts.

    CRITICAL RULES FOR SUNO:
    1. Prompt: Maximum 6000 characters
    2. Style: Single word from Suno's supported styles
    3. Title: Creative, memorable, under 100 characters
    4. NegativeTags: What to avoid (Max 8 items)

    SUNO PROMPT BEST PRACTICES:
    - Start with BPM (e.g., "120bpm")
    - List 2-3 key instruments
    - Add 2-3 mood descriptors
    - Keep it simple and clear
    - Avoid complex descriptions

    SUPPORTED STYLES:
    ambient, cinematic, electronic, pop, rock, jazz, classical,
    hip-hop, r&b, indie, folk, world, experimental

    OUTPUT FORMAT:
    Return ONLY valid JSON with these exact fields:
    {
        "prompt": "short descriptor",
        "style": "single-style",
        "title": "Creative Title",
        "negativeTags": ["tag1", "tag2"]
    }
    """

    # Suno 스타일 추출
    suno_style = template['suno_styles'][0] if template.get('suno_styles') else 'electronic'

    
    user_prompt = f"""
    Create a Suno music prompt for:

    VIDEO DATA:
    - Duration: {analysis.get('duration', 30):.1f}s
    - BPM: {template['detected_bpm']}
    - Energy: {template['energy']}
    - Visual Energy: {analysis.get('visual_energy'):.0f}/100

    MUSIC REQUIREMENTS:
    - Industry: {context.get('industry')}
    - Base Style: {template['base_style']}
    - Instruments: {', '.join(template['core_instruments'][:4])}
    - Mood: {', '.join(template['mood_descriptors'][:4])}
    - Suggested Style: {suno_style}

    Create a Suno prompt that is:
    1. Under 6000 characters
    2. Starts with {template['detected_bpm']}bpm
    3. Matches the {template['energy']} energy level
    4. Appropriate for {context.get('industry')} industry

    Return ONLY the JSON object.
    """

    try:
        response = client.messages.create(
            model = "claude-sonnet-4-20250514",
            max_tokens = 500,
            temperature = 0.3,
            system = system_prompt,
            messages = [
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        response_text = response.content[0].text.strip()

        # JSON 추출
        if "```json" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            response_text = response_text[json_start:json_end]

        
        # JSON 파싱
        try:
            return json.loads(response_text)
        
        except json.JSONDecodeError as e:
            raise Exception(f"Suno 음악 생성 프롬프트 JSON 파싱 실패: {str(e)}")

    
    except Exception as e:
        raise Exception(f"Suno 음악 생성 프롬프트 생성 실패: {str(e)}")



def optimize_for_suno(suno_data: Dict[str, Any],
                      template: Dict[str, Any]) -> Dict[str, Any]:
    """Suno 프롬프트 최적화"""

    optimized = copy.deepcopy(suno_data)

    valid_styles = ['ambient', 'cinematic', 'electronic', 'pop', 'rock', 
                   'jazz', 'classical', 'hip-hop', 'r&b', 'indie', 'folk', 
                   'world', 'experimental']

    
    # Style 정규화 (Suno 지원 스타일 맞춤)
    style = optimized.get('style', '').lower()


    if style not in valid_styles:
        style_map = {
            'classical crossover': 'cinematic',
            'ambient pop': 'ambient',
            'future bass': 'electronic',
            'synthwave': 'electronic',
            'orchestral': 'classical',
            'trap': 'hip-hop'
        }
        
        optimized['style'] = style_map.get(style, 'electronic')


    # NegativeTags 정리
    negative_tags = optimized.get('negativeTags', [])

    # 템플릿 avoid_elements 추가
    if template.get('avoid_elements'):
        negative_tags.extend(template['avoid_elements'])

    
    # 중복 제거 및 제한
    negative_tags = list(set(negative_tags))[:10]

    
    # 기본 네거티브 태그 추가 (없으면)
    if not negative_tags:
        negative_tags = ['noise', 'distortion', 'low quality', 'amateur']

    
    optimized['negativeTags'] = negative_tags


    return optimized


def validate_suno_prompt(suno_data: Dict[str, Any]) -> Dict[str, Any]:
    """Suno 프롬프트 검증"""

    validation = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'confidence_score': 1.0
    }

    valid_styles = ['ambient', 'cinematic', 'electronic', 'pop', 'rock', 
                   'jazz', 'classical', 'hip-hop', 'r&b', 'indie', 'folk', 
                   'world', 'experimental']
    
    required_fields = ['prompt', 'style', 'title', 'negativeTags']

    # 1. Prompt 필드 확인 검증
    for field in required_fields:
        if field not in suno_data:
            validation['errors'].append(f"Missing required field: {field}")
            validation['is_valid'] = False
            validation['confidence_score'] -= 0.3
        
        elif not suno_data[field]:
            validation['errors'].append(f"Empty field: {field}")
            validation['is_valid'] = False
            validation['confidence_score'] -= 0.2


    # 2. Prompt 검증
    prompt = suno_data.get('prompt', '')

    # 길이 체크
    if len(prompt) > 6000:
        validation['warnings'].append(f"Prompt too long: {len(prompt)} chars")
        validation['confidence_score'] -= 0.1
    
    elif len(prompt) < 1000:
        validation['warnings'].append(f"Prompt too short: {len(prompt)} chars")
        validation['confidence_score'] -= 0.1

    # BPM 포함 여부 확인
    if not re.search(r'\d+bpm', prompt.lower()):
        validation['warnings'].append("No BPM specified")
        validation['confidence_score'] -= 0.1

    
    # 3. Style 검증
    style = suno_data.get('style', '')

    if style not in valid_styles:
        validation['errors'].append(f"Invalid style: {style}")
        validation['is_valid'] = False
        validation['confidence_score'] -= 0.2

    # 4. Title 검증
    title = suno_data.get('title', '')

    if len(title) > 100:
        validation['warnings'].append(f"Title too long: {len(title)} chars")
        validation['confidence_score'] -= 0.1

    
    # 5. NegativeTags 검증
    negative_tags = suno_data.get('negativeTags', [])
    
    if not isinstance(negative_tags, list):
        validation['errors'].append("negativeTags must be a list")
        validation['is_valid'] = False
        validation['confidence_score'] -= 0.1
    
    elif len(negative_tags) > 10:
        validation['warnings'].append(f"Too many negative tags: {len(negative_tags)}")
        validation['confidence_score'] -= 0.1

    
    validation['confidence_score'] = max(0, validation['confidence_score'])

    return validation



def generate_metadata(template: Dict[str, Any],
                      analysis: Dict[str, Any],
                      validation: Dict[str, Any],
                      industry: str) -> Dict[str, Any]:
    """메타데이터 생성"""

    return {
        'industry': industry,
        'video_duration': analysis.get('duration', 30),
        'detected_bpm': template.get('detected_bpm'),
        'energy_level': template.get('energy'),
        'visual_energy': analysis.get('visual_energy'),
        'confidence_score': validation.get('confidence_score'),
        'template_used': template.get('base_style'),
        'scene_count': len(analysis.get('scene_transitions')),
        'brightness_level': 'bright' if analysis.get('avg_brightness') > 0.6 else 'dark' if analysis.get('avg_brightness') < 0.4 else 'neutral'
    }



def generate_alternatives(main_data: Dict[str, Any],
                          template: Dict[str, Any]) -> List[Dict[str, Any]]:
    """대체 프롬프트 생성"""

    alternatives = []

    # 1. 다른 스타일 버전
    if len(template.get('suno_styles', [])) > 1:
        alt1 = copy.deepcopy(main_data)
        
        alt_style = template['suno_styles'][1]

        alt1['style'] = alt_style
        alt1['title'] = f"{main_data['title']} (Style Change)"
        alternatives.append(alt1)


    # 2. 다른 템포 버전
    alt2 = copy.deepcopy(main_data)

    current_bpm = template.get('detected_bpm', 100)
    
    alt2['prompt'] = re.sub(r'\d+bpm', f"{current_bpm - 20}bpm", alt2['prompt'])

    
    alt2['title'] = f"{main_data['title']} (BPM Change)"
    alternatives.append(alt2)


    return alternatives[:2]
