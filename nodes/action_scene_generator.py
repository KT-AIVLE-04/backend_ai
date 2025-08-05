# nodes/action_scene_generator.py
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from states.agent_state import State
from config.settings import settings


def generate_action_scenes(state: State) -> State:
 
    # 테스트용
    return {"message": "시나리오 확정 완료", "title": state.final_scenario.title, "content": state.final_scenario.content}

#     def extract_json(content: str):
#        import json, re, ast
#        match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", content)
#        json_str = match.group(1) if match else content
#        cleaned = json_str.replace('\n', '').replace('\r', '').replace('\t', '').strip()

#        try:
#            return json.loads(cleaned)
#        except json.JSONDecodeError:

#            try:
#                return ast.literal_eval(cleaned)
#            except Exception as e:
#                return None

#     prompt_action_scenes = PromptTemplate(
#         input_variables = ["scenario", "synopsis"],
#         template =
# """
# 당신은 1000만 조회수 SNS 영상을 만든 바이럴 마케팅 전문가로서, 소비자의 감정을 뒤흔드는 강력한 장면을 설계하는 전문가입니다.

# 다음은 주어진 시나리오입니다. 꼼꼼하게 검토하세요. \n\n {scenario} \n\n

# 다음은 주어진 시놉시스입니다. 꼼꼼하게 검토하세요. \n\n {synopsis} \n\n

# 다음은 장면 구성 원칙입니다. 꼼꼼하게 검토하세요. \n
# **장면 구성 원칙**:
# 1. **3초 룰**: 각 장면은 3초 내에 강한 인상을 남겨야 함
# 2. **감정 가속**: 장면마다 감정의 강도가 상승해야 함
# 3. **시각적 임팩트**: 스크롤을 멈추게 하는 비주얼 요소 필수
# 4. **스토리 플로우**: Hook → Build-up → Climax → Resolution → CTA 구조


# 다음은 장면 설계 프레임워크입니다. 꼼꼼하게 검토하세요. \n
# **바이럴 장면 설계 프레임워크**:
# **Phase 1: HOOK (0-2초)**
# - 예상치 못한 상황 또는 강렬한 비주얼
# - "뭐지?" "어떻게?" 같은 즉각적 호기심 유발

# **Phase 2: BUILDUP (3-6초)**
# - 문제 상황의 구체적 전개
# - 소비자의 공감대와 감정 몰입 증대

# **Phase 3: REVEAL (7-10초)**
# - 솔루션의 등장과 차별점 강조
# - "와!" "이거다!" 같은 감탄 유발

# **Phase 4: IMPACT (11-13초)**
# - 변화의 순간과 결과 시각화
# - 강렬한 감정적 클라이맥스

# **Phase 5: URGENCY (14-15초)**
# - 즉시 행동 필요성과 혜택 강조


# 다음은 장면 설계 체크리스트입니다. 꼼꼼하게 검토하세요. \n
# **장면 설계 체크리스트**:
# **첫 프레임 임팩트**: 스크롤 중단시킬 강력한 비주얼
# **감정 설계**: 각 장면의 타겟 감정 명확히 설정
# **연결고리**: 장면 간 자연스러운 스토리 플로우
# **모바일 친화**: 세로 화면, 큰 텍스트, 명확한 시각 요소
# **리듬감**: 음악과 편집 리듬을 고려한 장면 길이


# 다음은 시각적 스토리텔링 요소입니다. 꼼꼼하게 검토하세요. \n
# **시각적 스토리텔링 요소**:
# **대비 효과**: Before/After, 문제/해결, 일반/특별
# **환경 설정**: 타겟의 일상과 밀접한 공간과 상황


# 주어진 시나리오와 시놉시스를 바탕으로 **SNS에서 바이럴될 수 있는 강력한 장면 5~8개**를 작성하세요.


# **결과는 반드시 JSON 형식으로 출력**하세요.
# 다음은 출력 예시 형식입니다. 꼼꼼하게 검토하세요. \n

# {{
#     "1": {{
#         "장면 제목": "Hook 장면 제목 1줄로 작성",
#         "장면 설명": "시각적 요소, 인물 행동, 감정 변화 등을 포함하여 3~4줄로 작성",
#         "감정 포인트": "해당 장면에서 유발하려는 핵심 감정을 1줄로 작성",
#         "시간": "예상 재생 시간 (예시: 3~5초)"
#     }},
#         "2": {{
#         "장면 제목": "Hook 장면 제목 1줄로 작성",
#         "장면 설명": "시각적 요소, 인물 행동, 감정 변화 등을 포함하여 3~4줄로 작성",
#         "감정 포인트": "해당 장면에서 유발하려는 핵심 감정을 1줄로 작성",
#         "시간": "예상 재생 시간 (예시: 3~5초)"
#     }},
#         "3": {{
#         "장면 제목": "Hook 장면 제목 1줄로 작성",
#         "장면 설명": "시각적 요소, 인물 행동, 감정 변화 등을 포함하여 3~4줄로 작성",
#         "감정 포인트": "해당 장면에서 유발하려는 핵심 감정을 1줄로 작성",
#         "시간": "예상 재생 시간 (예시: 3~5초)"
#     }},
#     ...
# }}
# """
#     )

#     llm = ChatOpenAI(temperature = 0.6, model = "gpt-4o-mini", streaming = True, api_key=settings.openai_api_key)
#     chain_action_scenes = prompt_action_scenes | llm | StrOutputParser()
#     action_scenes = chain_action_scenes.invoke({
#         'scenario': state.final_scenario['content'],
#         'synopsis': state.synopsis
#     })
#     action_scenes = extract_json(action_scenes)

#     return state.model_copy(update={
#       "action_scenes": action_scenes
#     })
