from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# 요청 스키마
class SNSPostRequest(BaseModel):
    content_data: str = Field(..., description="콘텐츠 데이터 (파일 경로 또는 텍스트)")
    content_type: Literal["image", "video"] = Field(default="image", description="콘텐츠 타입")
    user_keywords: List[str] = Field(default_factory=list, description="사용자 키워드")
    sns_platform: Literal["instagram", "facebook", "youtube"] = Field(..., description="SNS 플랫폼")
    business_type: str = Field(..., description="업종")
    location: Optional[str] = Field(None, description="위치 (선택사항)")

class HashtagRequest(BaseModel):
    post_title: str = Field(..., description="게시물 제목")
    post_content: str = Field(..., description="게시물 내용")
    user_keywords: List[str] = Field(default_factory=list, description="사용자 키워드")
    sns_platform: Literal["instagram", "facebook", "youtube"] = Field(..., description="SNS 플랫폼")
    business_type: str = Field(..., description="업종")
    location: Optional[str] = Field(None, description="위치 (선택사항)")

# 응답 스키마
class PostResponse(BaseModel):
    title: str = Field(..., description="게시물 제목")
    content: str = Field(..., description="게시물 내용")

class HashtagResponse(BaseModel):
    hashtags: List[str] = Field(..., description="생성된 해시태그 목록")

class FullPostResponse(BaseModel):
    post: PostResponse = Field(..., description="게시물 정보")
    hashtags: List[str] = Field(..., description="해시태그 목록")

