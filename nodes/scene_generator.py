# nodes/scene_generator.py
from openai import OpenAI
from schemas.agent_schema import Scene
from states.agent_state import State
from config.settings import settings
import json, re, ast


def generate_scenes(state: State) -> State:
    # OpenAI 클라이언트 초기화
    client = OpenAI(api_key=settings.openai_api_key)
    
    # 시스템 메시지와 사용자 프롬프트 생성
    system_message = create_system_message()
    user_prompt = create_user_prompt(state)
    
    # 메시지 구성
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        print(f"API 응답: {content}")
        
        scenes_data = extract_json(content)
        
        if scenes_data:
            for scene_info in scenes_data:
                scene = Scene(
                    title=scene_info['장면 제목'],
                    content=scene_info['장면 설명']
                )
                state.scenes.append(scene)
        else:
            print("Warning: Failed to parse scenes JSON")

        print(state.scenes)
        return state
        
    except Exception as e:
        print(f"장면 생성 중 오류 발생: {e}")
        return state


def create_system_message():
    return """당신은 수백만 조회수를 만든 SNS 바이럴 영상 전문가입니다.

🎯 **장면 구성 원칙**
1. 각 장면은 **정확히 8초 분량**이어야 합니다.
   - **하드 컷 전환**으로 각 장면이 명확히 구분되고, **장면 간 소재·연출이 절대 중복되지 않게** 작성하세요.

2. 장면 전체 스토리는 **Hook → 중간 전달 → 제품 중심 마무리** 구조를 포함합니다.
   - **첫 장면**: 강렬하고 임팩트 있는 연출로 이목을 집중시키는 훅 (예: 드라마틱한 변화, 예상 밖 연출, 시각적 충격)
   - **중간**: 제품/공간의 핵심 가치와 매력 요소를 자연스럽게 전달
   - **마지막 장면**: 홍보하려는 제품이나 브랜드를 명확히 보여주며 강렬한 인상으로 마무리 (로고, 제품샷, 매장 전경 등)

3. 제품 특성을 극대화한 참신하고 독창적인 연출 필수
   - 영화적·마법적 시각효과, 시간 흐름/공간 변형/사물 변신 등 창의적 아이디어 포함

4. **촬영·시각 표현 가이드**
   - 카메라 용어 필수: 드론 뷰, 클로즈업, 팬, 틸트, 줌, 슬로모션 등
   - 시각 요소 필수: 색감, 질감, 조명, 배경, 소품, 움직임 등 구체적으로
   - 금지: 텍스트/자막/대사/나레이션, 복잡한 스토리·은유

📦 **출력 규칙**
- **JSON 배열**만 출력 (코드 블록, 추가 설명, 서두·마무리 문장 금지)
- 각 장면은 다음 형식:
[
  {
    "장면 제목": "Hook 제목 (간결·주목도 높은 문장)",
    "장면 설명": "8초 분량의 장면을 마침표 기준 3~4문장으로 구체 묘사. 카메라 움직임, 조명, 배경, 색감, 소품 상태와 움직임을 상세 기술."
  }
]
"""

def create_user_prompt(state: State):
    scene_count = state.ad_duration // 8
    
    prompt = f"""다음 정보를 바탕으로 **정확히 {scene_count}개의 장면**을 생성하세요.
- 각 장면은 반드시 8초 분량입니다.
- 출력은 JSON 배열 형식만 사용하세요. 코드 블록, 추가 설명 금지.

📌 매장 정보:
- 업종: {state.business_type}
- 매장명: {state.store_name}
- 브랜드 컨셉: {', '.join(state.brand_concept)}

📌 광고 조건:
- 플랫폼: {state.platform}
- 광고 유형: {state.ad_type}
- 타겟 고객: {state.target_audience}
- 특별 요구사항: {state.scenario_prompt} ※ 반드시 반영

📌 시나리오:
- 제목: {state.final_scenario.title}
- 내용: {state.final_scenario.content}"""

    if state.image_list and any(img.main_objects or img.description for img in state.image_list):
        prompt += "\n\n📌 활용해야 할 이미지 요소 (각 장면에 최소 1개 이상 반영):"
        for i, img_info in enumerate(state.image_list):
            main_objects = ", ".join(img_info.main_objects) if img_info.main_objects else ""
            description = img_info.description if img_info.description else ""
            prompt += f"\n- 이미지 {i+1}: {main_objects} ({description})"
    
    return prompt

def extract_json(content: str):
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", content)
    json_str = match.group(1) if match else content
    
    # 이중 중괄호를 단일 중괄호로 변환 (PromptTemplate 이스케이프 해제)
    json_str = json_str.replace('{{', '{').replace('}}', '}')
    
    cleaned = json_str.replace('\n', '').replace('\r', '').replace('\t', '').strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(cleaned)
        except Exception:
            return None