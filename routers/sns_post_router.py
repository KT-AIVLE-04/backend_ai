# routers/sns_post_router.py
from fastapi import APIRouter, HTTPException
from schemas.sns_post_schema import (
    SNSPostRequest, 
    HashtagRequest, 
    PostResponse, 
    HashtagResponse,
    FullPostResponse
)
from core.sns_post_graph import run_sns_post_generation
from states.sns_post_state import SNSPostState
from nodes.sns_post.hashtag_generator import generate_hashtags
from typing import List

router = APIRouter(prefix="/sns-post", tags=["SNS Post"])

@router.post("/generate-post", response_model=PostResponse)
async def generate_post(request: SNSPostRequest):
    """
    SNS 게시물 제목, 본문 생성합니다.
    """
    try:
        # 워크플로우 실행
        final_state = run_sns_post_generation(
            content_data=request.content_data,
            content_type=request.content_type,
            sns_platform=request.sns_platform,
            business_type=request.business_type,
            user_keywords=request.user_keywords,
            location=request.location
        )
        
        if not final_state.generated_post:
            raise HTTPException(status_code=500, detail="게시물 생성에 실패했습니다.")
        
        return PostResponse(
            title=final_state.generated_post.title,
            content=final_state.generated_post.content,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"게시물 생성 중 오류가 발생했습니다: {str(e)}")

@router.post("/generate-hashtags", response_model=HashtagResponse)
async def generate_hashtags(request: HashtagRequest):
    """
    기존 게시물 정보를 바탕으로 해시태그만 생성합니다.
    """
    try:
        # 트렌드 분석을 위한 임시 상태 생성
        temp_state = SNSPostState(
            content_data="",  # 해시태그 생성에는 불필요
            content_type="image",  # 기본값으로 설정
            sns_platform=request.sns_platform,
            business_type=request.business_type,
            user_keywords=request.user_keywords,
            location=request.location
        )
        
        # 1. 트렌드 분석 실행
        from nodes.sns_post.trend_analyzer import analyze_trend
        temp_state = analyze_trend(temp_state)
        
        # 2. 임시 PostData 생성
        from states.sns_post_state import PostData
        temp_post = PostData(
            title=request.post_title,
            content=request.post_content,
        )
        
        # 3. generated_post 설정
        temp_state = temp_state.model_copy(update={"generated_post": temp_post})
        
        # 4. 해시태그 생성
        final_state = generate_hashtags(temp_state)
        
        return HashtagResponse(
            hashtags=final_state.hashtags
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"해시태그 생성 중 오류가 발생했습니다: {str(e)}")

@router.post("/generate-full", response_model=FullPostResponse)
async def generate_full_post(request: SNSPostRequest):
    """
    게시물과 해시태그를 모두 생성합니다.
    """
    try:
        # 워크플로우 실행
        final_state = run_sns_post_generation(
            content_data=request.content_data,
            content_type=request.content_type,
            sns_platform=request.sns_platform,
            business_type=request.business_type,
            user_keywords=request.user_keywords,
            location=request.location
        )
        
        if not final_state.generated_post:
            raise HTTPException(status_code=500, detail="게시물 생성에 실패했습니다.")
        
        return FullPostResponse(
            post=PostResponse(
                title=final_state.generated_post.title,
                content=final_state.generated_post.content,
            ),
            hashtags=final_state.hashtags
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"전체 생성 중 오류가 발생했습니다: {str(e)}")

