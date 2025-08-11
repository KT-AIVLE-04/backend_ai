from openai import OpenAI
from states.agent_state import State
from config.settings import settings

client = OpenAI(api_key=settings.openai_api_key)

def summarize_scenes(state: State) -> State:
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
    return """당신은 영상 제작의 일관성을 보장하는 전문가입니다.

여러 장면으로 구성된 영상에서 **시각적 일관성**을 유지하기 위해 장면들을 분석하고 요약해주세요.

🎯 **요약 목적**: 
- 각 장면별로 이미지를 생성할 때 **스타일, 색감, 분위기의 일관성** 유지
- 분리된 장면들을 하나의 완성된 영상으로 연결했을 때 자연스러운 흐름 보장

📋 **분석 및 요약 요소**:
1. **전체 영상의 핵심 테마와 메시지**
2. **일관된 시각적 스타일** (색감, 조명, 질감 등)
3. **공통된 분위기와 톤** (밝음/어두움, 따뜻함/차가움, 역동적/정적 등)
4. **반복되는 시각 요소** (소품, 배경, 카메라 기법 등)
5. **브랜드 아이덴티티 반영 방향**

📦 **출력 형식**:
간결하고 명확한 문단 형태로 작성하되, 이미지 생성 AI가 참고하기 쉽도록 구체적인 시각적 요소를 포함해주세요.
불필요한 설명이나 해석은 제외하고, 장면의 요약본만 3문장 정도로 제시해주세요."""

def create_user_prompt(state: State):
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

위 장면들을 분석하여, 각 장면별 이미지 생성 시 일관성을 유지할 수 있도록 전반적인 스토리를 요약해주세요."""

    return prompt