# nodes/scenario_generator.py
import os
from config.settings import settings
import openai
import json
from states.agent_state import State
from utils.image_utils import download_and_encode_image
from schemas.agent_schema import Scenario


def generate_scenarios(state: State, api_key=settings.openai_api_key) -> State:
    # OpenAI 클라이언트 초기화
    client = openai.OpenAI(api_key=api_key)
    
    # System Message 정의
    system_message = """당신은 소상공인을 위한 숏폼 동영상 광고 시나리오 전문가입니다.

다음 규칙을 반드시 준수해주세요:
1. 동영상 촬영 기법이나 과 같은 요소는 없어야 합니다. 스토리만 포함하세요.
2. 텍스트/자막 없어야 합니다.

응답 형식: 
[
    {
        "title": "임팩트 있고 간결한 제목 (20자 이내)",
        "content": "시나리오 설명 (120-150자)"
    },
    {
        "title": "임팩트 있고 간결한 제목 (20자 이내)",
        "content": "시나리오 설명 (120-150자)"
    },
    {
        "title": "임팩트 있고 간결한 제목 (20자 이내)",
        "content": "시나리오 설명 (120-150자)"
    }
]
이와 같이 JSON 배열만 출력해야 합니다. 코드 블록 표시도 포함하지 마세요.
그 외 추가 설명은 포함하지 마세요."""

    # User 프롬프트 생성
    prompt = create_scenario_prompt(state)

    # 메시지 구성 시작
    content_parts = [{"type": "text", "text": prompt}]
    
    # 이미지 처리 및 추가
    for i, url in enumerate(state.image_list):
        print(f"이미지 {i+1} 처리 중: {url}")
        encoded_image = download_and_encode_image(url)
        if encoded_image:
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{encoded_image}",
                    "detail": "low"  # "auto", "low", "high" 중 선택
                }
            })
            print(f"이미지 {i+1} 추가 완료")

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

def create_scenario_prompt(state: State) -> str:
    prompt = f"""
다음 요구사항을 만족하는 소상공인을 위한 숏폼 광고 시나리오를 스토리 형식으로 3개 생성해주세요.

매장 정보:
- 매장명: {state.store_name}
- 업종: {state.business_type}
- 브랜드 컨셉: {state.brand_concept}

광고 요구사항:
- 플랫폼: {state.platform}
- 광고 유형: {state.ad_type}
- 타겟 고객: {state.target_audience}
- 특별 요구사항: {state.scenario_prompt} (무조건 반영)

시나리오 작성 지침:
- 브랜드 컨셉이 시각적으로 드러나도록 색상, 분위기, 소품 등을 설정할 것
- 해당 플랫폼에서 자주 사용하는 광고 시나리오 형식을 참고하여 작성할 것
- 광고 유형에 적합한 연출과 구성으로 작성할 것
- 타겟 고객의 관심과 선호를 반영해 이목을 끌 수 있는 스토리로 구성할 것
- 특별 요구사항은 반드시 반영할 것
- 인물(사람, 손, 얼굴 등 인체 부분)은 등장시키지 말 것
- 단순히 장면과 분위기를 묘사하는 문장만 작성할 것 (설명적 어구는 사용하지 말 것)

이미지 활용 지침:
제공된 {len(state.image_list)}개의 이미지를 모두 분석하고, 각 시나리오에서 구체적으로 활용할 것
"""

    return prompt