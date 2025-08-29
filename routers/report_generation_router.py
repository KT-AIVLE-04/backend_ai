import json
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
from schemas.report_analysis_schema import PostAnalysisRequest, PostAnalysisMarkdownReport
from services.analysis_report_service import generate_final_report


router = APIRouter(prefix = "/api/analysis", tags = ["Post Final Analysis"])


@router.post("/report", response_model = PostAnalysisMarkdownReport)
async def analyze_emotions(request: PostAnalysisRequest):
    """게시글 성과 분석 리포트 데이터 생성"""
    
    try:
        print("마크다운 텍스트 보고서 생성 요청\n")

        markdown_report = generate_final_report(request)

        print("마크다운 텍스트 보고서 생성 완료\n")

        return markdown_report
        
    
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"게시글 성과 분석 리포트 데이터 생성 중 오류 발생: {str(e)}")
