# schemas/agent_schema.py
from pydantic import BaseModel, Field
from typing import List, Optional


class Scenario(BaseModel):
    title: str
    content: str


class ScenarioRequest(BaseModel):
    # 매장 정보
    store_name: str
    business_type: str

    # 브랜드 컨셉
    brand_concept: List[str]

    # 광고 정보
    platform: str
    ad_type: str
    target_audience: str
    
    # 사용자의 시나리오 요구사항
    scenario_prompt: str


class ScenarioResponse(BaseModel):
    session_id: str
    scenarios: List[Scenario] = Field(default_factory = list)


class Scene(BaseModel):
    title: str
    content: str


class VideoRequest(BaseModel):
    session_id: str
    title: str
    content: str
    ad_duration: int
    image_list: List[str]


class VideoResponse(BaseModel):
    key: Optional[str] = Field(default = None, description = "S3에 저장된 최종 비디오 key")


class InputImageInfo(BaseModel):
    url: str
    main_objects: List[str] = Field(default_factory = list)
    description: str = ""
