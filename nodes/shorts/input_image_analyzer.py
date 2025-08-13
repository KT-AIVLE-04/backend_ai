
import json
from config.settings import settings
from openai import OpenAI
from states.shorts_state import ShortsState

client = OpenAI(api_key=settings.openai_api_key)

def analyse_input_images(state: ShortsState) -> ShortsState:
    
    if not state.image_list:
        return state
    
    # 이미지 분석 프롬프트 작성
    prompt = f"""
당신은 광고 제작을 위한 이미지 분석 전문가입니다. 
업종: {state.business_type}
매장명: {state.store_name}

제공된 이미지들은 {state.business_type} 매장의 사진들입니다. 각 이미지를 분석하여 다음 정보를 JSON 형태로 제공해주세요:

1. main_object: 이미지에서 광고에 활용할 수 있는 핵심 요소들 (예: "딸기케이크", "커피", "매장 내부", "매장 외부", "상의 전면" 등)
2. brand_identity: 이미지에서 파악할 수 있는 브랜드의 분위기나 아이덴티티 (예: "파스텔", "따뜻함", "모던", "빈티지" 등)
3. description: 이미지에 대한 구체적인 설명 (1-2줄)

응답 형식:
[
  {{
    "main_object": ["요소1", "요소2"],
    "brand_identity": ["분위기1", "분위기2"],
    "description": "이미지에 대한 구체적 설명"
  }}
]

각 이미지를 제공된 순서대로 분석하되, 배열의 순서는 이미지가 제공된 순서와 일치해야 합니다. 광고 제작 관점에서 유용한 정보를 중심으로 추출해주세요.
JSON 형태로만 응답해주세요. 코드블럭은 제외하세요.
"""

    try:
        # 이미지 URL들을 메시지로 구성
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        # 각 이미지를 메시지에 추가
        for i, img_info in enumerate(state.image_list):
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {"url": img_info.url}
            })
        
        # GPT-4o API 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=2000,
            temperature=0.2
        )
        
        # 응답에서 JSON 추출
        response_text = response.choices[0].message.content.strip()
        print("API 응답:")
        print(response_text)
        
        # JSON 파싱 시도
        try:
            analysis_results = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 실패: {e}")
            # JSON이 코드 블록으로 감싸져 있을 수 있음
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
                try:
                    analysis_results = json.loads(response_text)
                except json.JSONDecodeError as e2:
                    return state
            else:
                return state
        
        # brand_identity 수집 (중복 제거)
        all_brand_identities = set(state.brand_concept)
        
        # 분석 결과를 state의 image_list에 순서대로 매핑
        updated_count = 0
        for i in range(min(len(analysis_results), len(state.image_list))):
            analysis = analysis_results[i]
            img_info = state.image_list[i]
            
            img_info.main_objects = analysis.get("main_object", [])
            img_info.description = analysis.get("description", "")
            
            # brand_identity를 brand_concept에 추가
            brand_identities = analysis.get("brand_identity", [])
            all_brand_identities.update(brand_identities)
            updated_count += 1
        
        # 업데이트된 brand_concept 설정
        state.brand_concept = list(all_brand_identities)
        print(state)
        
        return state
        
    except Exception as e:
        return state