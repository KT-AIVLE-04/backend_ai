# states/agent_state.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

from schemas.agent_schema import Scene, Scenario

class State(BaseModel):
    # 초기에 필요한 필드들
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

    # 나중에 채워질 필드들
    ad_duration: int = 15 # default
    scenarios: List[Scenario] = Field(default_factory=list)  # {"title", "content"}
    final_scenario: Optional[Scenario] = None  # {"title", "content"}
    scenes: List[Scene] = Field(default_factory=list)
    scenes_image_list: List[str] = Field(default_factory=list)