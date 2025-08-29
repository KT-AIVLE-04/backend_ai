from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class PostMetrics(BaseModel):
    """게시글 지표"""
    post_id: int = Field(..., description = "게시글 ID")
    view_count: int = Field(..., description = "조회수")
    like_count: int = Field(..., description = "좋아요 수")
    comment_count: int = Field(..., description = "댓글 수")


class PostEmotionData(BaseModel):
    """게시글 내 댓글 감정 분석"""
    positive_count: int = Field(..., description = "긍정 댓글 수")
    negative_count: int = Field(..., description = "부정 댓글 수")
    neutral_count: Optional[int] = Field(..., description = "중립 댓글 수")
    positive_keywords: List[str] = Field(..., description = "긍정 키워드 리스트")
    negative_keywords: List[str] = Field(..., description = "부정 키워드 리스트")
    neutral_keywords: Optional[List[str]] = Field(..., description = "중립 키워드 리스트")


class PostAnalysisRequest(BaseModel):
    """게시글 성과 분석 요청"""
    metrics: PostMetrics
    emotion_data: PostEmotionData
    title: Optional[str]
    description: Optional[str]
    url: Optional[str]
    tags: Optional[List[str]]
    publish_at: Optional[str]


class PostAnalysisResponse(BaseModel):
    """게시글 성과 분석 보고서"""
    performance_score: float
    performance_grade: str
    content_effectiveness: Dict
    detailed_analysis: Dict
    insights: List[Dict]
    content_recommendations: List[Dict]
    strategy: Dict
    action_items: List[Dict]


class PostAnalysisMarkdownReport(BaseModel):
    markdown_report: str
