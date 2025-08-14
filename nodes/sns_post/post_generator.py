# nodes/sns_post/post_generator.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from config.settings import settings
from states.sns_post_state import SNSPostState, PostData
import json
from utils.json_utils import to_json_str
from langchain_core.output_parsers import StrOutputParser

def generate_post(state: SNSPostState) -> SNSPostState:
    print("\n3️⃣ [POST_GENERATOR] 게시글 생성 시작")
    
    llm = ChatOpenAI(temperature=0.5, model="gpt-4o-mini", streaming=False, api_key=settings.openai_api_key)

    post_prompt = ChatPromptTemplate([
        ("system", """당신은 KPI 중심의 전문 SNS 마케터입니다.
        주어진 입력 정보를 바탕으로 '해시태그 없는' 게시글 본문을 생성합니다.

        [출력 형식]
        {{
            "title": "게시글 제목",
            "content": "게시글 본문",
        }}
        - 반드시 '순수 JSON'만 반환하세요.
        - 마크다운 금지, 코드블록 금지, 백틱(`) 금지, 추가 필드 금지, 한국어로 작성.

        [작성 규칙]
        - 플랫폼 특성 반영(톤, 길이, 이모지 사용 여부).
        - 업종 전문성 드러나되 광고성 문구 남발 금지.
        - "content"에는 자연스러운 1문장의 콜투액션을 포함하세요.
        - **'매장 위치(location)' 값이 비어있거나 None이면, 지역 관련 태그는 생성하지 말고 무시**
        """),
        ("human", """다음 정보를 바탕으로 SNS 게시글을 생성하세요:

        콘텐츠 정보:{content_summary}
        키워드: {user_keywords}
        플랫폼: {sns_platform}
        업종: {business_type}
        매장 위치: {location}
        트렌드 정보:{trend_analysis}
        
        위 정보를 종합하여 매력적인 SNS 게시글을 JSON 형식으로 생성하세요.""")
    ])
   
    messages = post_prompt.invoke(
        {
            "content_summary" : to_json_str(state.content_summary),
            "user_keywords" : state.user_keywords,
            "sns_platform" : state.sns_platform,
            "business_type" : state.business_type,
            "location" : state.location or "미지정",
            "trend_analysis" : to_json_str(state.trend_analysis)
        }
    )
    try:
        chain = llm | StrOutputParser()
        response = chain.invoke(messages)

        try:
            post = PostData(**json.loads(response))
            print("[결과]", post)
        except Exception:
            print("⚠️ [POST_GENERATOR] JSON 파싱 실패, 원문 보존")
            
        return state.model_copy(update={"generated_post": post})
    except Exception as e:
        print(f"❌ [POST_GENERATOR] 오류: {e}")
        return state