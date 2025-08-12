# nodes/sns_post/trend_analyzer.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from datetime import datetime
from config.settings import settings
from states.sns_post_state import SNSPostState, TrendData
import json
from utils.json_utils import to_json_str
from langchain_core.output_parsers import StrOutputParser

def analyze_trend(state: SNSPostState) -> SNSPostState:
    """트렌드 분석"""
    print("📊 [TREND_ANALYZER] 트렌드 분석 시작")
    
    llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini", streaming=False, api_key=settings.openai_api_key)
    
    trend_prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 SNS 트렌드 분석 전문가입니다.
        주어진 정보를 바탕으로 최신 SNS 트렌드를 분석하고 추천해주세요.
        
        [출력 형식]
        {{
            "keywords": ["..."], # 트렌딩 키워드
            "hashtags": ["..."], # 인기 해시태그
            "memes": ["..."], # 최신 밈
            "current_issues": ["..."], # 시사 이슈
            "popular_topics": ["..."], # 인기 주제
            "business_trend": ["..."], # 업종 트랜드
            "season_trend": ["..."], # 계절 트랜드
            "location_trend": ["..."] # 지역 트랜드
        }}
        - 반드시 '순수 JSON'만 반환하세요.
        - 마크다운 금지, 코드블록 금지, 백틱(`) 금지, 추가 필드 금지, 한국어로 작성.
        """),
        ("human", """분석 요청 정보:
        - 게시할 콘텐츠: {content_summary}
        - 사용자가 중요하게 생각하는 키워드: {user_keywords}
        - 업로드할 SNS 플랫폼: {sns_platform}
        - 업종: {business_type}
        - 매장 위치: {location}
        - 현재 날짜: {current_date}
        """)
    ])
    print('state.content_summary', state.content_summary)
    messages = trend_prompt.invoke(
        {
            "content_summary" : to_json_str(state.content_summary),
            "user_keywords" : state.user_keywords,
            "sns_platform" : state.sns_platform,
            "business_type" : state.business_type,
            "location" : state.location,
            "current_date" : datetime.now().strftime("%Y-%m-%d")
        }
    )
    
    try:
        chain = llm | StrOutputParser()
        response = chain.invoke(messages)        
        try:
            trend = TrendData(**json.loads(response))
            print("🤍", trend)

        except Exception:
            print("⚠️ [TREND_ANALYZER] JSON 파싱 실패, 원문 보존")
        
        print("✅ [TREND_ANALYZER] 분석 완료")
        
        return state.model_copy(update={"trend_analysis": trend})
        
    except Exception as e:
        print(f"❌ [TREND_ANALYZER] 오류: {e}")
        return state