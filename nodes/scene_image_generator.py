import json
import random
from config.settings import settings
from states.agent_state import State
from openai import OpenAI
import replicate
from utils.image_utils import combine_images

def generate_scene_images(state: State) -> State:
    
    openai_client = OpenAI(api_key=settings.openai_api_key)
    replicate_client = replicate.Client(api_token=settings.replicate_api_key)
    
    print(f"총 {len(state.scenes)}개 장면의 이미지를 생성합니다.")
    
    for i, scene in enumerate(state.scenes):
        print(f"\n=== 장면 {i+1}/{len(state.scenes)} 처리 중 ===")
        print(f"장면 제목: {scene.title}")
        
        try:
            # GPT-4o로 이미지 선택 및 프롬프트 생성
            scene_config = generate_scene_config_for_flux_kontext(
                openai_client, state, scene, i
            )
            
            if not scene_config:
                print(f"장면 {i+1} 분석 실패, 건너뜁니다.")
                continue
            
            # 선택된 이미지들로 참고 이미지 생성
            selected_image_urls = [
                state.image_list[idx].url 
                for idx in scene_config["image_index"]
                if idx < len(state.image_list)
            ]
            
            if not selected_image_urls:
                print(f"장면 {i+1}: 참고할 이미지가 없어 건너뜁니다.")
                continue
                
            # 참고 이미지 합성
            reference_image_url = combine_images(selected_image_urls)
            
            # flux-kontext-max로 이미지 생성
            scene_image_url = replicate_client.run(
                "black-forest-labs/flux-kontext-max",
                input={
                    "prompt": scene_config["flux-kontext-prompt"],
                    "input_image": reference_image_url,
                    "go_fast": False,
                    "aspect_ratio": "9:16", 
                    "output_format": "jpg",
                    "prompt_upsampling": False
                }
            )
            
            # 결과 URL 처리
            if hasattr(scene_image_url, 'url'):
                image_url = scene_image_url.url
            elif isinstance(scene_image_url, str):
                image_url = scene_image_url
            else:
                image_url = str(scene_image_url)
            
            state.scenes_image_list.append(image_url)
            print(f"장면 {i+1} 이미지 생성 완료: {image_url}")
            
        except Exception as e:
            print(f"장면 {i+1} 이미지 생성 중 오류: {e}")
            continue
    
    print(f"\n이미지 생성 완료: {len(state.scenes_image_list)}/{len(state.scenes)}개")
    return state

def generate_scene_config_for_flux_kontext(openai_client, state, scene, scene_index):
    """
    GPT-4o를 사용하여 장면 분석 후 참고 이미지 선택 및 flux-kontext 프롬프트 생성
    """
    system_message = create_system_message()
    user_prompt = create_user_prompt(state, scene, scene_index)
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1500,
            temperature=0.3
        )
        
        response_text = response.choices[0].message.content.strip()
        print(f"GPT-4o 분석 결과: {response_text}")
        
        # JSON 파싱
        try:
            scene_config = json.loads(response_text)
            return scene_config
        except json.JSONDecodeError:
            # 코드 블록으로 감싸진 경우 처리
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
                scene_config = json.loads(json_text)
                return scene_config
            else:
                print(f"JSON 파싱 실패: {response_text}")
                return None
        
    except Exception as e:
        print(f"GPT-4o 호출 오류: {e}")
        return None

def create_system_message():
    return """당신은 영상 제작에서 각 장면의 첫 프레임 이미지 생성을 담당하는 전문가입니다.

🎯 **역할**: 
- 장면 설명을 분석하여 첫 프레임에 적합한 참고 이미지를 선정
- flux-kontext-max AI가 첫 프레임 이미지를 생성할 수 있는 최적의 프롬프트 작성

📋 **분석 과정**:
1. 장면의 첫 프레임에 어떤 시각적 요소가 필요한지 파악
2. 전체 영상 스타일 가이드(scene_summary)를 바탕으로 일관성 유지 방향 결정
3. 제공된 이미지들 중 가장 적합한 참고 이미지 선택
4. flux-kontext-max가 이해하기 쉬운 영어 프롬프트 생성

🔧 **선택 기준**:
- 장면의 주요 객체/소품과 일치하는 이미지
- 원하는 분위기/색감을 구현할 수 있는 이미지  
- 브랜드 아이덴티티를 잘 반영하는 이미지

📦 **출력 형식** (JSON만, 코드 블록이나 추가 설명 금지):
{
  "image_index": [0, 1],
  "flux-kontext-prompt": "A detailed English prompt for flux-kontext-max describing the first frame of the scene, incorporating visual style consistency and brand elements from reference images."
}

⚠️ **제약사항**:
- image_index는 반드시 배열 형태 (단일 이미지도 [0] 형태)
- flux-kontext-prompt는 영어로 작성
- 첫 프레임만을 위한 프롬프트 (전체 장면 아님)
- 구체적이고 명확한 시각적 묘사 포함"""

def create_user_prompt(state, scene, scene_index):
    prompt = f"""다음 장면의 첫 프레임 이미지 생성을 위해 참고 이미지를 선택하고 프롬프트를 작성해주세요:

📌 현재 장면 (장면 {scene_index + 1}):
제목: {scene.title}
설명: {scene.content}

📌 전체 스타일 가이드:
{state.scene_summary if state.scene_summary else '스타일 가이드 없음'}

📌 매장 정보:
- 매장명: {state.store_name}
- 업종: {state.business_type}  
- 브랜드 컨셉: {', '.join(state.brand_concept)}

📌 참고 가능한 이미지들:"""

    for i, img_info in enumerate(state.image_list):
        main_objects = ", ".join(img_info.main_objects) if img_info.main_objects else "분석되지 않음"
        description = img_info.description if img_info.description else "설명 없음"
        prompt += f"""
이미지 {i}: 
- 핵심 요소: {main_objects}
- 설명: {description}"""

    prompt += f"""

위 정보를 바탕으로:
1. 이 장면의 첫 프레임에 가장 적합한 참고 이미지를 선택하세요
2. 선택한 이미지들과 스타일 가이드를 반영한 flux-kontext 프롬프트를 작성하세요
3. 브랜드 일관성을 유지하면서도 이 장면만의 특색을 살려주세요

JSON 형식으로만 응답해주세요."""

    return prompt