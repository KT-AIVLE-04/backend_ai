from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal


class CommentInput(BaseModel):
    """SNS 댓글 입력 데이터"""
    id: int = Field(..., description = "댓글 ID")
    created_at: Optional[str] = Field(None, description = "생성 일시")
    updated_at: Optional[str] = Field(None, description = "수정 일시")
    author_id: Optional[str] = Field(None, description = "작성자 ID")
    content: str = Field(..., description = "댓글 내용")
    like_count: Optional[int] = Field(0, description = "좋아요 수")
    post_id: Optional[int] = Field(None, description = "게시물 ID")
    published_at: Optional[str] = Field(None, description = "게시 일시")
    sns_comment_id: Optional[str] = Field(None, description = "SNS 댓글 ID")


class EmotionAnalysisRequest(BaseModel):
    """감정 분석 요청 스키마"""
    comments: List[CommentInput] = Field(..., description = "분석할 댓글 객체 리스트")


class IndividualResult(BaseModel):
    """개별 댓글 분석 결과"""
    id: int = Field(..., description = "댓글 ID")
    result: Literal["POSITIVE", "NEGATIVE", "NEUTRAL"] = Field(..., description = "감정 분석 결과")


class KeywordResult(BaseModel):
    """키워드 추출 결과"""
    positive: List[str] = Field(default_factory=list, description = "긍정 키워드 리스트")
    negative: List[str] = Field(default_factory=list, description = "부정 키워드 리스트")


class EmotionAnalysisResponse(BaseModel):
    """감정 분석 응답 스키마"""
    individual_results: List[IndividualResult] = Field(..., description = "개별 댓글 분석 결과(긍정 or 부정 or 중립)")
    keywords: KeywordResult = Field(..., description = "추출 키워드")
