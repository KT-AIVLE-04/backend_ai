import json
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
import aiohttp
from schemas.report_analysis_schema import PostAnalysisRequest, SNSPostResponse, StoreResponse, PostAnalysisMarkdownReport
from services.analysis_report_service import generate_final_report


router = APIRouter(prefix = "/api/analysis", tags = ["Post Final Analysis"])
BASE_URL = "https://aivle.r-e.kr"

async def fetch_sns_post_data(post_id) -> SNSPostResponse:
    """GET /api/sns/posts/{id} 호출"""

    async with aiohttp.ClientSession() as session:
        try:
            url = f"{BASE_URL}/api/sns/posts/{post_id}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    post_data = data.get("result", {})

                    return SNSPostResponse(**post_data)
                
                else:
                    raise HTTPException(
                        status_code = response.status,
                        detail = f"SNS 게시글 조회 API 실패: {post_id}"
                    )
                    
        except aiohttp.ClientError as e:
            raise Exception(f"SNS Post 데이터 GET 실패 {e}")



async def fetch_store_data(store_id) -> StoreResponse:
    """GET /api/stores/{storeId} 호출"""

    async with aiohttp.ClientSession() as session:
        try:
            url = f"{BASE_URL}/api/stores/{store_id}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    store_data = data.get("result", {})

                    return StoreResponse(**store_data)
                
                else:
                    raise HTTPException(
                        status_code = response.status,
                        detail = "Stores 데이터 조회 API 실패"
                    )
                    
        except aiohttp.ClientError as e:
            raise Exception(f"Stores 데이터 GET 실패 {e}")



@router.post("/report", response_model = PostAnalysisMarkdownReport)
async def analyze_emotions(request: PostAnalysisRequest, 
                           store_id: Optional[str] = Header(None, alias = "X-STORE-ID")):
    """게시글 성과 분석 리포트 데이터 생성"""
    
    try:
        if store_id and not request.industry:
            store_id = int(store_id)
            store_data = await fetch_store_data(store_id)

            request.industry = store_data.industry

            print(f"Stores Industry 데이터 업데이트 완료\n")

        sns_post = None

        if not request.title or not request.description or not request.tags or not request.publish_at or not request.url:
            sns_post = await fetch_sns_post_data(request.metrics.post_id)

        if not request.title and sns_post:
            request.title = sns_post.title
        
        if not request.description and sns_post:
            request.description = sns_post.description

        if not request.tags and sns_post:
            request.tags = sns_post.tags

        if not request.publish_at and sns_post:
            request.publish_at = sns_post.publishAt
        
        if not request.url and sns_post:
            request.url = sns_post.url

        print(f"SNS Post 데이터 업데이트 완료\n")


        markdown_report = generate_final_report(request)
        

        return markdown_report
        
    
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"게시글 성과 분석 리포트 데이터 생성 중 오류 발생: {str(e)}")
