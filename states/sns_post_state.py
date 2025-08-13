# states/sns_post_state.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class ContentData(BaseModel):
    title: str = ""
    content: str = ""
    keywords: List[str] = Field(default_factory=list)
    mood: str = ""
    target_audience: str = ""

class TrendData(BaseModel):
    keywords: List[str] = Field(default_factory=list, description="트렌딩 키워드")
    hashtags: List[str] = Field(default_factory=list, description="인기 해시태그")
    memes: List[str] = Field(default_factory=list, description="최신 밈")
    current_issues: List[str] = Field(default_factory=list, description="시사 이슈")
    popular_topics: List[str] = Field(default_factory=list, description="인기 주제")
    business_trend: List[str] = Field(default_factory=list, description="업종 트랜드")
    season_trend: List[str] = Field(default_factory=list, description="계절 트랜드")
    location_trend: List[str] = Field(default_factory=list, description="지역 트랜드")

class PostData(BaseModel):
    title: str = ""
    content: str = ""

class SNSPostState(BaseModel):
    # 입력
    content_data: str  # 파일 경로 또는 텍스트
    sns_platform: Literal["instagram", "facebook", "youtube"]
    business_type: str
    user_keywords: List[str] = Field(default_factory=list)
    location: Optional[str] = None  # 선택

    # 중간 생성물
    content_summary: Optional[ContentData] = None  
    trend_analysis: Optional[TrendData] = None
    generated_post: Optional[PostData] = None
    hashtags: List[str] = Field(default_factory=list)

