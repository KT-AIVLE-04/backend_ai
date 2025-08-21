import json
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
from schemas.comments_analysis_schema import EmotionAnalysisRequest, EmotionAnalysisResponse, IndividualResult, KeywordResult
from services.comments_analysis_service import analyze_comments


router = APIRouter(prefix = "/api/comments", tags = ["Comments Analysis"])

@router.post("/analyze", response_model = EmotionAnalysisResponse)
async def analyze_emotions(request: EmotionAnalysisRequest):
    """댓글 리스트 감정 분석 및 키워드 추출"""
    
    try:
        result = analyze_comments(
            comment_objects = request.comments,
        )

        individual_results = []
        for item in result["individual_results"]:
            individual_result = IndividualResult(
                id = item["id"],
                result = item["result"],
            )

            individual_results.append(individual_result)
        
        return EmotionAnalysisResponse(
            individual_results = individual_results,
            keywords = KeywordResult(**result["keywords"])
        )
        
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"댓글 감정 분석 중 오류 발생: {str(e)}")