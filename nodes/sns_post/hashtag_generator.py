# nodes/sns_post/hashtag_generator.py
import re, json
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from states.sns_post_state import SNSPostState
from config.settings import settings
from utils.json_utils import to_json_str
from langchain_core.output_parsers import StrOutputParser

def _normalize_hashtags(raw: List[str]) -> List[str]:
    norm = []
    for t in raw or []:
        t = t.strip()
        t = re.sub(r"\s+", "", t)              # 공백 제거
        t = re.sub(r"[^\w#가-힣]", "", t)       # 이모지/기타 제거
        if not t: continue
        if not t.startswith("#"):
            t = f"#{t}"
        norm.append(t.lower())
    # 의미중복(#여행, #travel 정도는 유지할지 정책화 가능)
    out = []
    seen = set()
    for t in norm:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out

def _cap_by_platform(tags: List[str], platform: str) -> List[str]:
    limits = {
        "instagram": (7, 11),
        "facebook": (2, 3),
        "youtube": (3, 5),
    }
    lo, hi = limits.get(platform, (3, 5))
    return tags[:hi]

def generate_hashtags(state: SNSPostState) -> SNSPostState:
    print("\n4️⃣ [HASHTAG_GENERATOR] 해시태그 생성 시작")
    if not state.generated_post:
        print("⚠️ 생성된 게시글이 없습니다.")
        return state

    llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini", streaming=False, api_key=settings.openai_api_key)

    hashtag_prompt = ChatPromptTemplate([
        ("system", """당신은 KPI 중심의 해시태그 최적화 전문가입니다.
        입력(게시글, 업종, 지역, 트렌드)을 바탕으로 플랫폼별 노출과 참여를 극대화하는 해시태그를 생성하세요.

        [출력 형식]
        #태그1, #태그2, #태그3, #태그4
        - 쉼표로 구분된 해시태그 리스트만 반환하세요.
        - 마크다운 금지, 코드블록 금지, 백틱(`) 금지, JSON 금지.
        - 각 태그는 '#'로 시작해야 합니다.

        [플랫폼별 권장 개수]
        - instagram: 7~11개
        - facebook: 2~3개
        - youtube: 3~5개

        [플랫폼별 우선순위(중요 → 덜 중요)]
        - Instagram: ① 핵심 콘텐츠 키워드 ② 세분화/타겟(지역·속성) ③ 트렌드/인기 ④ 오리지널/브랜드
        - Facebook : ① 캠페인/이벤트 ② 개인·커뮤니티 ③ 키워드+지역
        - YouTube : ① 영상 주제(콘텐츠 타입) ② 트렌드/빅키워드(예: #Shorts) ③ 세분화 타겟 ④ 브랜드/채널

        [품질/규칙]
        - 모든 태그는 '#'로 시작, 공백·이모지·URL 금지, 한국어 중심(필요 시 혼잡도 낮은 영문 보조)
        - 중복·의미중복(표기차/단복수) 제거
        - 플랫폼 한도 초과 금지
        - **'매장 위치(location)' 값이 비어있거나 None이면, 지역 관련 태그는 생성하지 말고 무시**
        - **'사용자 키워드(user_keywords)' 값이 비어있거나 빈 리스트([])이면, 키워드 기반 태그는 생략하고 나머지 규칙에 맞게 생성**
        """),
        ("human", """다음 정보를 바탕으로 해시태그를 생성하세요:
        
        - 게시글 제목: {post_title}
        - 게시글 내용: {post_content}
        - 사용자 키워드: {user_keywords}
        - SNS 플랫폼: {sns_platform}
        - 업종: {business_type}
        - 매장 위치: {location}
        - 트렌드 분석 결과: {trend_analysis}
        """)
    ])
    
    messages = hashtag_prompt.invoke(
        {
            "post_title" : state.generated_post.title,
            "post_content" : state.generated_post.content,
            "user_keywords" : state.user_keywords,
            "sns_platform" : state.sns_platform,
            "business_type" : state.business_type,
            "location" : state.location,
            "trend_analysis" : to_json_str(state.trend_analysis)
        }
    )
    
    try:
        chain = llm | StrOutputParser()
        response = chain.invoke(messages)
        print("[결과]", response)

        # 쉼표로 구분된 해시태그를 파싱
        raw_tags = [tag.strip() for tag in response.split(',') if tag.strip()]
        tags = _normalize_hashtags(raw_tags)
        tags = _cap_by_platform(tags, state.sns_platform)

        return state.model_copy(update={"hashtags": tags})
    except Exception as e:
        print(f"❌ [HASHTAG_GENERATOR] 오류: {e}")
        return state