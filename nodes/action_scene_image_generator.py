import random
from config.settings import settings
from states.agent_state import State
import replicate
from utils.image_utils import combine_images
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
import json

def generate_action_scene_images(state: State) -> State:
    client = replicate.Client(api_token=settings.replicate_api_key)

    # 액션 씬 내용들을 영어로 번역
    translated_contents = translate_action_scenes_to_english(state.action_scenes)

    combined_image_url = combine_images(state.image_list)
    
    for i, action_scene in enumerate(state.action_scenes):
        # 번역된 내용 사용
        action_scene_content = translated_contents[i]
        prompt = create_action_scene_image_prompt(action_scene_content)

        action_scene_image_url = client.run(
            "black-forest-labs/flux-kontext-max",
            input={
                "prompt": prompt,
                "input_image": combined_image_url,
                "go_fast": False, 
                "aspect_ratio": "9:16",
                "output_format": "jpg",
                "prompt_upsampling": False
            }
        )

        # FileOutput 객체를 URL 문자열로 변환
        if hasattr(action_scene_image_url, 'url'):
            image_url = action_scene_image_url.url
        elif isinstance(action_scene_image_url, str):
            image_url = action_scene_image_url
        else:
            image_url = str(action_scene_image_url)
        
        print(image_url)
        state.action_scenes_image_list.append(image_url)

    return state

def create_action_scene_image_prompt(action_scene_content: str):
    prompt = f"""
TASK:
1. Analyze the provided input image (a stitched photo of the business/store or products).
   - Extract key visual elements: brand colors, textures, signature product shapes, and overall style.
2. **Do NOT directly copy or reuse the exact composition of the input image.**
3. **Recompose and redesign the scene based on the given action scene description**,  
   naturally incorporating the extracted brand elements (e.g., color palette, textures, signature products).
4. If the action scene requires elements that are not present in the input image,  
   add them in a way that aligns with the brand identity derived from the input image.

ACTION SCENE :  
"{action_scene_content}"

OUTPUT REQUIREMENTS:
- Generate exactly ONE image.
- Use realistic photographic quality suitable for a video frame.
- Reconstruct the scene to match the action scene while reflecting brand identity.
- Do NOT simply duplicate or overlay the input image.
- Ensure no text, watermarks, or human figures are present.
"""
    return prompt

def translate_action_scenes_to_english(action_scenes):
    """액션 씬 내용들을 순서대로 영어로 번역"""
    
    # 모든 액션 씬 내용을 순서대로 수집
    contents = [scene.content for scene in action_scenes]
    
    # 번역 프롬프트 생성
    prompt_template = PromptTemplate(
        input_variables=["contents"],
        template="""
당신은 마케팅 및 영상 제작 콘텐츠를 전문으로 번역하는 전문 번역가입니다.

다음 한국어 액션 씬 설명을 영어로 번역하세요. 단, 다음 사항을 유지해야 합니다:
	1.	장면의 순서를 정확히 유지할 것
	2.	모든 카메라 및 시각적 세부사항을 그대로 보존할 것
	3.	마케팅 효과와 감정적인 톤을 유지할 것
	4.	전문 영상 제작 용어를 사용할 것

한국어 액션 씬 내용:
{contents}

요구사항:
	•	각 장면 설명을 정확히 번역할 것
	•	카메라 앵글, 움직임, 조명, 색상에 대한 설명을 모두 유지할 것
	•	5초 장면 타이밍 맥락을 유지할 것
	•	전문 영상 제작 영어 용어를 사용할 것
	•	출력은 반드시 동일한 순서의 JSON 배열 형태로만 반환할 것

출력 형식:
["translated scene 1", "translated scene 2", "translated scene 3", ...]
"""
    )
    
    llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini", api_key=settings.openai_api_key)
    chain = prompt_template | llm | StrOutputParser()
    
    # 내용들을 문자열로 변환 (번호와 함께)
    numbered_contents = []
    for i, content in enumerate(contents, 1):
        numbered_contents.append(f"{i}. {content}")
    
    contents_str = "\n\n".join(numbered_contents)
    
    result = chain.invoke({"contents": contents_str})
    
    # JSON 파싱해서 리스트 반환
    try:
        # JSON 형태로 응답이 온 경우 파싱
        if result.strip().startswith('['):
            return json.loads(result.strip())
        else:
            # 일반 텍스트로 온 경우 줄바꿈으로 분리
            lines = result.strip().split('\n')
            return [line.strip() for line in lines if line.strip()]
    except json.JSONDecodeError:
        # JSON 파싱 실패시 원본 내용 반환
        return contents