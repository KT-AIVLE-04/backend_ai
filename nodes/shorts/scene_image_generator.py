import json
import asyncio
from config.settings import settings
from states.shorts_state import ShortsState
from openai import OpenAI
import replicate
from utils.image_utils import combine_images
from core.decorators import timed_node

@timed_node
def generate_scene_images(state: ShortsState) -> ShortsState:
    
    openai_client = OpenAI(api_key=settings.openai_api_key)
    replicate_client = replicate.Client(api_token=settings.replicate_api_key)
    
    print(f"총 {len(state.scenes)}개 장면의 이미지를 생성합니다.")
    
    # 모든 장면에 대해 한 번의 LLM 호출로 설정 생성
    all_scene_configs = generate_all_scenes_config_for_flux_kontext(openai_client, state)

    # 비동기 이미지 생성을 동기 방식으로 실행
    try:
        # 현재 실행 중인 이벤트 루프가 있는지 확인
        asyncio.get_running_loop()

        # 이미 실행중인 이벤트 루프가 있으면, 별도의 스레드에서 새로운 이벤트 루프를 생성해서 비동기 작업 실행
        image_urls = run_async_in_sync(generate_images_async(replicate_client, state, all_scene_configs))
    except RuntimeError:
        # 실행 중인 루프가 없으면 새로 생성
        image_urls = asyncio.run(generate_images_async(replicate_client, state, all_scene_configs))
    
    # 결과를 순서대로 state.scenes_image_list에 저장
    state.scenes_image_list.extend(image_urls)
    
    print(f"\n이미지 생성 완료: {len(state.scenes_image_list)}/{len(state.scenes)}개")
    return state

def run_async_in_sync(coro):
    """
    실행 중인 이벤트 루프에서 코루틴을 동기적으로 실행
    """
    import concurrent.futures
    
    def run_in_thread():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_thread)
        return future.result()

async def generate_images_async(replicate_client, state, all_scene_configs):
    """
    모든 장면의 이미지를 병렬로 생성하고 순서대로 결과를 반환
    """
    tasks = []
    
    for i, (scene, scene_config) in enumerate(zip(state.scenes, all_scene_configs)):
        print(f"장면 {i+1} 비동기 작업 준비 중: {scene.title}")
        
        # 선택된 이미지들로 참고 이미지 생성
        selected_image_urls = [
            state.image_list[idx].url 
            for idx in scene_config["image_index"]
            if idx < len(state.image_list)
        ]
        
        task = asyncio.create_task(
            generate_single_scene_image_async(
                replicate_client, scene_config, selected_image_urls, i, scene.title
            )
        )
        tasks.append(task)
    
    print("모든 장면 이미지 생성 작업을 병렬로 시작합니다...")
    
    # 모든 작업이 완료될 때까지 대기하고 순서대로 결과 수집
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 결과 처리 (예외 처리 및 None 필터링)
    image_urls = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"장면 {i+1} 이미지 생성 중 오류: {result}")
            continue
        elif result is None:
            print(f"장면 {i+1} 이미지 생성 실패 또는 설정 없음")
            continue
        else:
            image_urls.append(result)
            print(f"장면 {i+1} 이미지 생성 완료: {result}")
    
    return image_urls

async def generate_single_scene_image_async(replicate_client, scene_config, selected_image_urls, scene_index, scene_title):
    """
    단일 장면의 이미지를 비동기로 생성
    """
    try:
        loop = asyncio.get_event_loop()
        
        if not selected_image_urls:
            # 참고 이미지 없이 생성
            scene_image_url = await loop.run_in_executor(
                None,
                lambda: replicate_client.run(
                    "black-forest-labs/flux-kontext-max",
                    input={
                        "prompt": scene_config["flux-kontext-prompt"],
                        "go_fast": False,
                        "aspect_ratio": "16:9", 
                        "output_format": "jpg",
                        "prompt_upsampling": False
                    }
                )
            )
        else:
            # 참고 이미지와 함께 생성
            reference_image_url = await loop.run_in_executor(
                None,
                lambda: combine_images(selected_image_urls)
            )
            
            scene_image_url = await loop.run_in_executor(
                None,
                lambda: replicate_client.run(
                    "black-forest-labs/flux-kontext-max",
                    input={
                        "prompt": scene_config["flux-kontext-prompt"],
                        "input_image": reference_image_url,
                        "go_fast": False,
                        "aspect_ratio": "16:9", 
                        "output_format": "jpg",
                        "prompt_upsampling": False
                    }
                )
            )
        
        # 결과 URL 처리
        if hasattr(scene_image_url, 'url'):
            image_url = scene_image_url.url
        elif isinstance(scene_image_url, str):
            image_url = scene_image_url
        else:
            image_url = str(scene_image_url)
        
        return image_url
        
    except Exception as e:
        print(f"장면 {scene_index+1} ({scene_title}) 이미지 생성 중 오류: {e}")
        raise e

def generate_all_scenes_config_for_flux_kontext(openai_client, state):
    """
    모든 장면에 대해 한 번의 LLM 호출로 이미지 선택 및 flux-kontext 프롬프트 생성
    """
    system_message = create_batch_system_message()
    user_prompt = create_batch_user_prompt(state)
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=4000,
            temperature=0.3
        )
        
        response_text = response.choices[0].message.content.strip()
        print(f"GPT-4o-mini 배치 분석 결과: {response_text}")
        
        # JSON 파싱
        try:
            all_configs = json.loads(response_text)
            return all_configs
        except json.JSONDecodeError:
            # 코드 블록으로 감싸진 경우 처리
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
                all_configs = json.loads(json_text)
                return all_configs
            else:
                print(f"JSON 파싱 실패: {response_text}")
                return None
        
    except Exception as e:
        print(f"GPT-4o-mini 배치 호출 오류: {e}")
        return None

def create_batch_system_message():
    return """당신은 영상 제작에서 각 장면의 첫 프레임 이미지 생성을 담당하는 전문가입니다.

🎯 **역할**: 
- 여러 장면의 설명을 분석하여 각 장면의 첫 프레임에 적합한 참고 이미지를 선정
- 각 장면마다 flux-kontext-max AI가 첫 프레임 이미지를 생성할 수 있는 최적의 프롬프트 작성

📋 **분석 과정**:
1. 각 장면의 첫 프레임에 어떤 시각적 요소가 필요한지 파악
2. 전체 영상 스타일 가이드(scene_summary)를 바탕으로 일관성 유지 방향 결정
3. 제공된 이미지들 중 각 장면에 가장 적합한 참고 이미지 선택

🔧 **선택 기준**:
- 장면의 주요 객체/소품과 일치하는 이미지
- 원하는 분위기/색감을 구현할 수 있는 이미지  
- 브랜드 아이덴티티를 잘 반영하는 이미지
- 단, 장면의 주요 객체/소품과 일치하는 것이 없다면 image_index를 빈 리스트로 반환

📦 **출력 형식** (JSON 배열만, 코드 블록이나 추가 설명 금지):
[
  {
    "scene_index": 0,
    "image_index": [0, 1],
    "flux-kontext-prompt": "A detailed English prompt for flux-kontext-max describing the first frame of scene 1"
  },
  {
    "scene_index": 1,
    "image_index": [2],
    "flux-kontext-prompt": "A detailed English prompt for flux-kontext-max describing the first frame of scene 2"
  }
]

⚠️ **제약사항**:
- scene_index는 0부터 시작하는 장면 번호
- image_index는 반드시 배열 형태 (단일 이미지도 [0] 형태)
- flux-kontext-prompt는 영어로 작성
- 각 장면의 첫 프레임만을 위한 프롬프트 (전체 장면 아님)
- **구체적이고 명확한 시각적 묘사만 포함**"""

def create_batch_user_prompt(state):
    prompt = f"""다음 모든 장면들의 첫 프레임 이미지 생성을 위해 각 장면마다 참고 이미지를 선택하고 프롬프트를 작성해주세요:

📌 전체 장면 스타일 요약:
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

📌 처리할 장면들:"""
    
    for i, scene in enumerate(state.scenes):
        prompt += f"""
장면 {i} - {scene.title}:
{scene.content}"""

    prompt += f"""

위 정보를 바탕으로:
1. 각 장면의 첫 프레임에 가장 적합한 참고 이미지를 선택하세요
2. 선택한 이미지들과 스타일 요약을 반영한 flux-kontext 프롬프트를 각 장면마다 작성하세요
3. 브랜드 일관성을 유지하면서도 각 장면만의 특색을 살려주세요

JSON 배열 형식으로만 응답해주세요."""

    return prompt
