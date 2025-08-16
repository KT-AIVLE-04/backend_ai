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
    # video_url: str

    # TODO: 테스트
    scenes: List[Scene]
    ai_scenes_image_list: List[str]

    final_video_path: Optional[str] = Field(default = None, description = "최종 비디오 파일 경로")
    final_video_filename: Optional[str] = Field(default = None, description = "최종 비디오 파일명")
    
    # 개별 씬 비디오 URL
    scene_video_urls: List[str] = Field(default_factory = list, description = "각 씬별 생성된 비디오 URL")
    

class InputImageInfo(BaseModel):
    url: str
    main_objects: List[str] = Field(default_factory = list)
    description: str = ""
