from openai import OpenAI
from states.shorts_state import ShortsState
from config.settings import settings
from core.decorators import timed_node

client = OpenAI(api_key=settings.openai_api_key)

@timed_node
def summarize_scenes(state: ShortsState) -> ShortsState:
    """
    장면들을 분석하여 일관성 유지를 위한 요약 생성
    이미지 생성 시 스타일, 색감, 분위기의 일관성을 유지하기 위해 사용
    """
    
    if not state.scenes:
        print("장면이 없어 요약을 생성할 수 없습니다.")
        return state
    
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
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.3  # 일관성을 위해 낮은 temperature 사용
        )
        
        scene_summary = response.choices[0].message.content.strip()
        state.scene_summary = scene_summary
        
        print(f"장면 요약 생성 완료:")
        print(scene_summary)
        
        return state
        
    except Exception as e:
        print(f"장면 요약 생성 중 오류 발생: {e}")
        return state

def create_system_message():
    return """당신은 영상의 통합적 스타일링을 담당하는 시각 디렉터입니다.

전체 장면들을 종합적으로 분석하여, **핵심 색상 팔레트, 전체적인 분위기, 그리고 일관된 스타일 방향성**을 중심으로 스토리를 요약해주세요.

🎯 **핵심 분석 요소**:
1. **주요 색상 팔레트** (2-3가지 핵심 색상과 보조 색상)
2. **전체적인 무드와 분위기** (고급스러운, 활기찬, 따뜻한, 모던한 등)
3. **일관된 스타일 방향성** (미니멀, 빈티지, 컨템포러리, 내추럴 등)
4. **공통 시각적 특성** (조명의 성격, 질감, 카메라 톤 등)
5. **브랜드 아이덴티티와의 조화**

📦 **출력 요구사항**:
- 개별 장면별 설명이 아닌 **전체 영상의 통합적 스토리 요약**
- 색상, 분위기, 스타일을 중심으로 한 **시각적 가이드라인 성격**의 요약
- 이미지 생성 시 일관성 있는 결과물을 위한 **핵심 키워드 중심** 작성
- 3-4문장으로 간결하게 정리"""

def create_user_prompt(state: ShortsState):
    prompt = f"""다음 {len(state.scenes)}개 장면을 분석하여 일관성 유지를 위한 요약을 작성해주세요:

📌 매장 정보:
- 업종: {state.business_type}
- 브랜드 컨셉: {', '.join(state.brand_concept)}
- 플랫폼: {state.platform}
- 타겟 고객: {state.target_audience}

📌 전체 시나리오:
- 제목: {state.final_scenario.title}
- 내용: {state.final_scenario.content}

📌 개별 장면들:"""

    for i, scene in enumerate(state.scenes, 1):
        prompt += f"""

장면 {i}: {scene.title}
내용: {scene.content}"""

    prompt += """

위 전체 장면들을 종합 분석하여, 핵심이 되는 색상 팔레트, 전반적인 분위기, 그리고 일관된 스타일 방향성을 중심으로 스토리를 요약해주세요.
개별 장면의 세부사항보다는 전체 영상을 관통하는 시각적 통일성에 중점을 두어 작성해주세요."""

    return prompt