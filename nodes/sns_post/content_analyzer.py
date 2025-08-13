# nodes/sns_post/content_analyzer.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config.settings import settings
from states.sns_post_state import SNSPostState, ContentData
import base64, os, json, re
from urllib.parse import urlparse

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

def _guess_image_mime(ext: str) -> str:
    ext = ext.lower()
    if ext in {'.jpg', '.jpeg'}: return 'image/jpeg'
    if ext == '.png': return 'image/png'
    if ext == '.gif': return 'image/gif'
    if ext == '.webp': return 'image/webp'
    return 'application/octet-stream'

def _is_http_url(s: str) -> bool:
    try:
        u = urlparse(s)
        return u.scheme in ("http", "https") and bool(u.netloc)
    except Exception:
        return False

def _fallback_content(state: SNSPostState, note: str) -> ContentData:
    # content_summary를 항상 ContentData로 통일
    return ContentData(
        title="콘텐츠 요약",
        content=note,
        keywords=state.user_keywords or [],
        mood="중립",
        target_audience="일반"
    )

def _extract_json(text: str):
    # 순수 JSON 강제 실패 시 관대한 추출
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None

def analyze_content(state: SNSPostState) -> SNSPostState:
    print("🖼️ [CONTENT_ANALYZER] 콘텐츠 분석 시작")

    content_path = state.content_data if isinstance(state.content_data, str) else None
    user_keywords = state.user_keywords or []
    user_keywords_str = ", ".join(user_keywords) if user_keywords else "없음"

    # 메시지 공통 프롬프트
    system_msg = SystemMessage(content=(
        "당신은 미디어 콘텐츠 분석 전문가입니다. 반드시 '순수 JSON'만 반환하세요.\n"
        '[출력 형식]\n'
        '{"title":"...","content":"...","keywords":["..."],"mood":"...","target_audience":"..."}\n'
        "규칙: 마크다운 금지, 코드블록 금지, 백틱(`) 금지, 추가 필드 금지, 한국어로 작성."
    ))

    llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini", streaming=False, api_key=settings.openai_api_key)

    # 1) HTTP(S) 이미지 URL
    if content_path and _is_http_url(content_path):
        ext = os.path.splitext(urlparse(content_path).path)[1].lower()
        if ext and ext not in IMAGE_EXTS:
            print(f"ℹ️ 비이미지(영상/기타) URL 감지: {ext} -> 메타 요약으로 대체")
            fb = _fallback_content(
                state,
                f"{os.path.basename(urlparse(content_path).path) or '원격 파일'} 기반 콘텐츠. 업종={state.business_type}, 플랫폼={state.sns_platform}"
            )
            return state.model_copy(update={"content_summary": fb})

        human_text = (
            "분석 요청 정보:\n"
            f"- 미디어 타입: image\n"
            f"- 사용자 키워드: {user_keywords_str}\n"
            f"- SNS 플랫폼: {state.sns_platform}\n"
            f"- 업종: {state.business_type}\n"
            "이미지 분석 후 위 JSON 스키마로만 반환."
        )
        human_msg = HumanMessage(content=[
            {"type": "text", "text": human_text},
            {"type": "image_url", "image_url": {"url": content_path}}
        ])
        try:
            response = llm.invoke([system_msg, human_msg])

            data = _extract_json(response.content or "")
            if not data:
                raise ValueError("JSON 파싱 실패")
            content = ContentData(**data)
            return state.model_copy(update={"content_summary": content})
        except Exception as e:
            print(f"⚠️ [CONTENT_ANALYZER] 원격 이미지 분석 실패: {e}")
            fb = _fallback_content(
                state,
                f"원격 이미지 분석 실패. 업종={state.business_type}, 플랫폼={state.sns_platform}"
            )
            return state.model_copy(update={"content_summary": fb})

    # 2) 로컬 파일 경로 없는 경우 → 텍스트 기반
    if not content_path or not os.path.exists(content_path):
        print(f"⚠️ 파일 없음 또는 경로 오류: {content_path} -> 텍스트 처리")
        fb = _fallback_content(
            state,
            f"텍스트 기반 콘텐츠. 업종={state.business_type}, 플랫폼={state.sns_platform}"
        )
        return state.model_copy(update={"content_summary": fb})

    # 3) 로컬 비이미지(영상/기타) → 메타 요약
    ext = os.path.splitext(content_path)[1].lower()
    if ext not in IMAGE_EXTS:
        print(f"ℹ️ 비이미지(영상/기타) 감지: {ext} -> 파일명/메타 기반 요약으로 대체")
        fb = _fallback_content(
            state,
            f"{os.path.basename(content_path)} 파일 기반 콘텐츠. 업종={state.business_type}, 플랫폼={state.sns_platform}"
        )
        return state.model_copy(update={"content_summary": fb})

    # 4) 로컬 이미지 → base64 분석
    try:
        with open(content_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"❌ 파일 읽기 오류: {e}")
        fb = _fallback_content(
            state,
            f"파일 읽기 실패: {os.path.basename(content_path)}. 업종={state.business_type}, 플랫폼={state.sns_platform}"
        )
        return state.model_copy(update={"content_summary": fb})

    mime = _guess_image_mime(ext)

    human_text = (
        "분석 요청 정보:\n"
        f"- 미디어 타입: image\n"
        f"- 업종: {state.business_type}\n"
        f"- SNS 플랫폼: {state.sns_platform}\n"
        f"- 사용자 키워드: {user_keywords_str}\n"
        "이미지 분석 후 위 JSON 스키마로만 반환."
    )
    human_msg = HumanMessage(content=[
        {"type": "text", "text": human_text},
        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
    ])

    try:
        response = llm.invoke([system_msg, human_msg])
        data = _extract_json(response.content)
        if not data:
            raise ValueError("JSON 파싱 실패")
        content = ContentData(**data)
        print("🤍", content)
        return state.model_copy(update={"content_summary": content})
    except Exception as e:
        print(f"❌ [CONTENT_ANALYZER] 오류: {e}")
        fb = _fallback_content(
            state,
            f"이미지 분석 실패: {os.path.basename(content_path)}. 업종={state.business_type}, 플랫폼={state.sns_platform}"
        )
        return state.model_copy(update={"content_summary": fb})
