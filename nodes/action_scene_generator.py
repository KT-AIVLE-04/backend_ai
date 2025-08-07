# nodes/action_scene_generator.py
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from schemas.agent_schema import ActionScene
from states.agent_state import State
from config.settings import settings
import json, re, ast


def generate_action_scenes(state: State) -> State:

    action_scenes_prompt = create_action_scenes_prompt_template()

    llm = ChatOpenAI(temperature = 0.7, model = "gpt-4o-mini", streaming = True, api_key=settings.openai_api_key)
    chain_action_scenes = action_scenes_prompt | llm | StrOutputParser()
    action_scenes = chain_action_scenes.invoke({
        'business_type': state.business_type,
        'brand_concept': state.brand_concept,
        'platform': state.platform,
        'ad_type': state.ad_type,
        'target_audience': state.target_audience,
        'scenario_prompt': state.scenario_prompt,
        'scenario_title': state.final_scenario.title,
        'scenario_content': state.final_scenario.content,
        'ad_duration': state.ad_duration
    })

    action_scenes = extract_json(action_scenes)
    
    for scene_key, scene_info in action_scenes.items():
        action_scene = ActionScene(
            scene_number=int(scene_key),
            title=scene_info['장면 제목'],
            content=scene_info['장면 설명']
        )
        state.action_scenes.append(action_scene)

    print(state.action_scenes)
    return state


def create_action_scenes_prompt_template():

    prompt_template = PromptTemplate(
        input_variables = ["business_type", "brand_concept", "platform", "ad_type", "target_audience", "scenario_prompt", "scenario_title", "scenario_content", "ad_duration"],
        template ="""
당신은 수백만 조회수를 만든 SNS 바이럴 영상 전문가입니다.  
소비자의 감정을 사로잡고 매장을 방문하게 만들 수 있도록,  
주어진 시나리오를 기반으로 **영상 AI가 인식 가능한 {ad_duration}의 장면**으로 분할 구성해주세요.

📌 매장 정보:
- 업종: {business_type}
- 브랜드 컨셉: {brand_concept}

📌 광고 조건:
- 플랫폼: {platform}
- 광고 유형: {ad_type}
- 타겟 고객: {target_audience}
- 특별 요구사항: {scenario_prompt} ※ 반드시 반영해주세요.

📌 시나리오 정보:
- 시나리오 제목: {scenario_title}
- 시나리오 내용: {scenario_content}

---

🎯 **장면 구성 원칙**

1. 총 3개의 독립된 장면을 작성해주세요.  
   - 각 장면은 **8초 분량**입니다.  
   - **하드 컷 전환**으로 각 장면이 명확히 구분되어야 하며, **장면 간 소재 또는 연출이 겹치지 않아야 합니다.**

2. **Hook → 중간 전달 → 강렬한 마무리** 구조를 장면 내에 포함해주세요.  
   - 예: 첫 2초에 시선을 끄는 연출 → 중간에 제품/공간의 핵심 요소 전달 → 마지막 1~2초에 잔상이나 임팩트 마무리.

3. **촬영 및 시각 표현 가이드**
   - **카메라 표현 필수**: 드론 뷰, 클로즈업, 팬, 틸트, 줌, 슬로우 모션 등 기술적 용어 사용
   - **시각적 요소 표현 필수**: 색감, 질감, 조명, 배경, 소품, 움직임 등을 **AI가 구현 가능하도록 구체적**으로 묘사
   - **제한 사항**:
     - 텍스트, 자막, 대사, 나레이션 금지
     - 복잡한 스토리라인, 추상적 표현, 은유적 설명 금지

---

📦 **출력 형식** (아래 형식으로만 응답해주세요. 다른 설명 금지):

{{
    "1": {{
        "장면 제목": "첫 번째 장면의 Hook 제목 (간결하고 주목도 높은 문장)",
        "장면 설명": "8초 분량의 구체적인 장면 묘사를 3~4문장으로 작성해주세요. 각 장면은 시각적 장면을 중심으로 카메라 움직임, 조명, 배경, 색감, 소품의 상태와 움직임 등을 명확하게 설명해야 하며, 비디오 생성 AI가 바로 적용할 수 있도록 상세히 기술해주세요."
    }},
    "2": {{
        "장면 제목": "두 번째 장면의 Hook 제목",
        "장면 설명": "8초 분량의 구체적인 장면 묘사..."
    }},
    "3": {{
        "장면 제목": "세 번째 장면의 Hook 제목",
        "장면 설명": "8초 분량의 구체적인 장면 묘사..."
    }}
}}
"""
    )

    return prompt_template

def extract_json(content: str):
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", content)
    json_str = match.group(1) if match else content
    cleaned = json_str.replace('\n', '').replace('\r', '').replace('\t', '').strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:

        try:
            return ast.literal_eval(cleaned)
        except Exception as e:
            return None