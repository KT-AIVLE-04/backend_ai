# nodes/cene_generator.py
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from schemas.agent_schema import Scene
from states.agent_state import State
from config.settings import settings
import json, re, ast


def generate_scenes(state: State) -> State:

    scenes_prompt = create_scenes_prompt_template()

    llm = ChatOpenAI(temperature = 0.7, model = "gpt-4o", streaming = True, api_key=settings.openai_api_key)
    chain_scenes = scenes_prompt | llm | StrOutputParser()
    scenes = chain_scenes.invoke({
        'business_type': state.business_type,
        'brand_concept': state.brand_concept,
        'platform': state.platform,
        'ad_type': state.ad_type,
        'target_audience': state.target_audience,
        'scenario_prompt': state.scenario_prompt,
        'scenario_title': state.final_scenario.title,
        'scenario_content': state.final_scenario.content,
        'scene_count': state.ad_duration // 5
    })

    scenes = extract_json(scenes)
    
    if scenes:
        for scene_info in scenes:
            scene = Scene(
                title=scene_info['장면 제목'],
                content=scene_info['장면 설명']
            )
            state.scenes.append(scene)
    else:
        print("Warning: Failed to parse scenes JSON")

    print(state.scenes)
    return state


def create_scenes_prompt_template():

    prompt_template = PromptTemplate(
        input_variables = ["business_type", "brand_concept", "platform", "ad_type", "target_audience", "scenario_prompt", "scenario_title", "scenario_content", "scene_count"],
        template ="""
당신은 수백만 조회수를 만든 SNS 바이럴 영상 전문가입니다.  
소비자의 감정을 사로잡고 매장을 방문하게 만들 수 있도록,  
주어진 매장 정보, 광고 조건, 시나리오를 분석한 후 그 내용 기반으로 **영상 AI가 인식 가능한 {scene_count}개의 장면**으로 분할 구성해주세요.

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

1. 총 {scene_count}개의 독립된 장면을 작성해주세요.  
   - 각 장면은 **5초 분량**입니다.  
   - **하드 컷 전환**으로 각 장면이 명확히 구분되어야 하며, **장면 간 소재 또는 연출이 겹치지 않아야 합니다.**

2. **Hook → 중간 전달 → 강렬한 마무리** 구조를 장면 내에 포함해주세요.  
   - 예: 첫 2초에 시선을 끄는 연출 → 중간에 제품/공간의 핵심 요소 전달 → 마지막 1~2초에 잔상이나 임팩트 마무리.

3. **제품 특성을 최대한 활용하여, 참신하고 창의적이며 독특한 연출**을 포함해주세요.  
   - 제품 또는 서비스가 가진 특징을 시각적으로 극대화하고,  
   - 제품의 특징을 극대화하기 위한 ‘영화적’이거나 ‘마법‘ 같은 느낌을 주는 비주얼을 포함해주세요.  
   - 시간의 흐름, 공간 변형, 사물의 변신 등 독창적인 아이디어를 적극 반영해주세요.

4. **촬영 및 시각 표현 가이드**
   - **카메라 표현 필수**: 드론 뷰, 클로즈업, 팬, 틸트, 줌, 슬로우 모션 등 기술적 용어 사용
   - **시각적 요소 표현 필수**: 색감, 질감, 조명, 배경, 소품, 움직임 등을 **AI가 구현 가능하도록 구체적**으로 묘사
   - **제한 사항**:
     - 텍스트, 자막, 대사, 나레이션 금지
     - 복잡한 스토리라인, 추상적 표현, 은유적 설명 금지

---

📦 **출력 형식** (아래 형식으로만 응답해주세요. 다른 설명 금지):

[
    {{
        "장면 제목": "첫 번째 장면의 Hook 제목 (간결하고 주목도 높은 문장)",
        "장면 설명": "5초 분량의 구체적인 장면 묘사를 3~4문장으로 작성해주세요. 각 장면은 시각적 장면을 중심으로 카메라 움직임, 조명, 배경, 색감, 소품의 상태와 움직임 등을 명확하게 설명해야 하며, 비디오 생성 AI가 바로 적용할 수 있도록 상세히 기술해주세요."
    }},
    {{
        "장면 제목": "두 번째 장면의 Hook 제목",
        "장면 설명": "5초 분량의 구체적인 장면 묘사..."
    }},
    ...
]
"""
    )

    return prompt_template

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
        except Exception as e:
            return None