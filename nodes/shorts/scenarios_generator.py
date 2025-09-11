# nodes/scenario_generator.py
import os
from config.settings import settings
import openai
import json
from repositories.in_memory_ad_style_repository import InMemoryAdStyleRepository
from states.shorts_state import ShortsState
from schemas.shorts_schema import Scenario
from core.decorators import timed_node

@timed_node
def generate_scenarios(state: ShortsState, api_key=settings.openai_api_key) -> ShortsState:
    # OpenAI 클라이언트 초기화
    client = openai.OpenAI(api_key=api_key)
    
    # System Message 정의
    system_message = """당신은 소상공인을 위한 숏폼 동영상 광고 시나리오 전문가입니다.

다음 규칙을 반드시 준수해주세요:
1. 동영상 촬영 기법(예: 카메라 무빙, 앵글, 렌즈 등)은 절대 포함하지 마세요. 오직 장면의 연속적인 스토리만 작성하세요.
2. 텍스트, 자막, 대사, 나레이션, 음악은 포함하지 마세요.

응답 형식은 아래와 같이 JSON 배열로만 작성하세요. 코드 블록을 사용하지 마세요.

[
    {
        "title": "임팩트 있고 간결한 제목 (20자 이내)",
        "content": "스토리 형식의 시나리오 설명 (150자 이상)"
    },
    ...
]
그 외 추가 설명은 포함하지 마세요."""

    # User 프롬프트 생성
    prompt = create_scenario_prompt(state)

    print("프롬프트:")
    print(prompt)

    # 메시지 구성 시작
    content_parts = [{"type": "text", "text": prompt}]

    # 최종 메시지 구성
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": content_parts}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()
        print(f"API 응답: {content}")
        
        scenarios = json.loads(content)

        for scenario in scenarios:
            state.scenarios.append(Scenario(title=scenario["title"], content=scenario["content"]))

        return state

    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        print(f"원본 응답: {content}")
        return state
    except Exception as e:
        print(f"API 호출 오류: {e}")
        return state

def create_scenario_prompt(state: ShortsState) -> str:

    repository = InMemoryAdStyleRepository()
    ad_style_list = repository.get_top3_ad_styles_by_business_type(state.business_type)

    prompt = f"""
🎯 목표:
경쟁이 치열한 숏폼 플랫폼에서 **시청자의 시선을 단번에 사로잡을 만큼 독창적이고 감각적인 시나리오** 3가지를 작성해주세요.
주어진 매장 정보, 광고 조건을 분석한 뒤에 그 분석 내용을 바탕으로 시나리오를 작성해주세요.

📌 매장 정보:
- 업종: {state.business_type}
- 브랜드 컨셉: {state.brand_concept}

📌 광고 조건:
- 플랫폼: {state.platform}
- 광고 유형: {state.ad_type}
- 타겟 고객: {state.target_audience}
- 특별 요구사항: {state.scenario_prompt}

📌 시나리오 작성 지침:
1. 세 가지 시나리오는 각각 다른 스타일로 작성하세요.
   - 첫번째 시나리오 스타일: {ad_style_list[0]}
   - 두번째 시나리오 스타일: {ad_style_list[1]}
   - 세번째 시나리오 스타일: {ad_style_list[2]}
2. 브랜드 컨셉과 제품의 특성이 **직관적으로 시각화**될 수 있도록 색감, 분위기, 소품 등을 설정해주세요.
3. 해당 플랫폼의 숏폼 광고 흐름(3-컷 구성 등)을 참고하여 **시작-전개-임팩트 마무리** 흐름으로 구성해주세요.
4. 광고 유형에 맞게 **자연스럽고 세련된** 장면 구성을 해주세요.
5. 타겟 고객이 흥미를 느낄 수 있도록 **감각적이고 반전 있는 장면 연출**에 집중해주세요.
6. ‘특별 요구사항’은 반드시 반영해주세요.
"""

    return prompt