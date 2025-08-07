# schemas/agent_schema.py
from pydantic import BaseModel, Field
from typing import List

class Scenario(BaseModel):
    title: str
    content: str

class ScenarioRequest(BaseModel):
    # 매장 정보
    store_name: str
    business_type: str

    # 브랜드 컨셉
    brand_concept: List[str]

    #이미지 리스트
    image_list: List[str]

    # 광고 정보
    platform: str
    ad_type: str
    target_audience: str
    
    # 사용자의 시나리오 요구사항
    scenario_prompt: str

class ScenarioResponse(BaseModel):
    session_id: str
    scenarios: List[Scenario] = Field(default_factory=list)

class ActionScene(BaseModel):
    scene_number: int
    title: str
    content: str

class ActionScenesRequest(BaseModel):
    session_id: str
    title: str
    content: str
    ad_duration: int

class ActionScenesResponse(BaseModel):
    action_scenes: List[ActionScene]
    action_scenes_image_list: List[str]
