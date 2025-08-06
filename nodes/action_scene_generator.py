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

    llm = ChatOpenAI(temperature = 0.6, model = "gpt-4o-mini", streaming = True, api_key=settings.openai_api_key)
    chain_action_scenes = action_scenes_prompt | llm | StrOutputParser()
    action_scenes = chain_action_scenes.invoke({
        'scenario': state.final_scenario.content,
        'action_scenes_count': state.ad_duration // 5
    })

    action_scenes = extract_json(action_scenes)
    
    for scene_key, scene_info in action_scenes.items():
        action_scene = ActionScene(
            scene_number=int(scene_key),
            title=scene_info['장면 제목'],
            content=scene_info['장면 설명']
        )
        state.action_scenes.append(action_scene)

    return state


def create_action_scenes_prompt_template():

    prompt_template = PromptTemplate(
        input_variables = ["scenario", "action_scenes_count"],
        template ="""
당신은 1000만 조회수 SNS 영상을 만든 바이럴 마케팅 전문가로서, 소비자의 감정을 뒤흔드는 강력한 장면을 설계하는 전문가입니다.
주어진 시나리오를 {action_scenes_count}개의 장면으로 분할해주세요.

다음은 주어진 시나리오입니다. 꼼꼼하게 검토하세요. \n\n {scenario} \n\n

## 필수 준수 사항:

### 1. 장면 구성 원칙
- **총 {action_scenes_count}개 장면**: 각 장면은 정확히 5초 분량
- **장면 전환**: 연속적 흐름이 아닌 명확한 컷 전환으로 구성
- **Hook 구조**: 각 장면이 독립적으로도 매력적이어야 함
- **홍보 효과**: 시청자의 관심을 끌고 방문 욕구를 자극해야 함

### 2. 숏폼 광고 최적화
- **첫 1초**: 즉시 시선을 사로잡는 임팩트 있는 시작
- **중간 3초**: 핵심 내용을 명확하게 전달
- **마지막 1초**: 다음 장면으로의 자연스러운 마무리 또는 강렬한 여운

### 3. 비디오 생성 AI 호환성
- **구체적 묘사**: 카메라 앵글, 움직임, 조명, 색감 등 상세 명시
- **기술적 용어**: 드론뷰, 클로즈업, 팬닝, 줌인/아웃 등 정확한 촬영 용어 사용
- **시각적 요소**: 텍스처, 색상, 분위기 등 시각적 특징 구체화
- **금지 사항**: 사람 등장 금지, 복잡한 스토리라인 배제, 자막 및 텍스트 금지, 모호한 표현 금지

### 4. 장면 전환 스타일
- **하드 컷**: 장면 간 명확한 구분
- **테마 연결**: 각 장면이 전체 브랜드 메시지를 강화
- **시각적 임팩트**: 각 장면마다 다른 강조점

## 출력 형식:
다음 JSON 형식으로만 응답해주세요. 다른 텍스트는 포함하지 마세요.

{{
    "1": {{
        "장면 제목": "첫 번째 장면의 훅(Hook) 제목을 한 줄로 작성",
        "장면 설명": "5초 분량의 구체적인 장면 묘사를 3-4줄로 작성. 장면 설명, 카메라 움직임, 요소의 움직임 및 상태, 조명, 색감 등을 비디오 생성 AI가 정확히 이해할 수 있도록 상세히 기술"
    }},
    "2": {{
        "장면 제목": "두 번째 장면의 훅(Hook) 제목을 한 줄로 작성",
        "장면 설명": "5초 분량의 구체적인 장면 묘사를 3-4줄로 작성. 장면 설명, 카메라 움직임, 요소의 움직임 및 상태, 조명, 색감 등을 비디오 생성 AI가 정확히 이해할 수 있도록 상세히 기술"
    }},
    ...
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