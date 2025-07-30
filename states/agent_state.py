# states/agent_state.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class State(BaseModel):
    store_name: str
    store_address: str
    category: str
    platform: str
    scenario_prompt: str
    scenarios: List[Dict[str, str]] = Field(default_factory=list)  # {"id", "title", "content"}
    edit_request: List[Dict[str, str]] = Field(default_factory=list)  # {"selected_id", "feedback"}
    final_scenario: Optional[Dict[str, str]] = None  # {"id", "title", "content"}
    chatbot_answer: Optional[str] = None
    confirmed: bool = False  # 추가) 사용자가 시나리오 수정을 확정했는지 여부
    synopsis: str = ""
    action_scenes: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    flux_prompts: List[Dict[str, str]] = Field(default_factory=list)
    veo_prompts: List[Dict[str, str]] = Field(default_factory=list)