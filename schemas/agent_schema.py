# schemas/agent_schema.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class AgentRequest(BaseModel):
    store_name: str
    store_address: str
    category: str
    platform: str
    scenario_prompt: str
    edit_request: List[Dict[str, str]] = Field(default_factory=list)
    confirmed: bool = False

class Scenario(BaseModel):
    id: str
    title: str
    content: str

class AgentResponse(BaseModel):
    scenarios: List[Scenario] = Field(default_factory=list)
    final_scenario: Optional[Scenario] = None
    chatbot_answer: Optional[str] = None
    flux_prompts: List[Dict[str, str]] = Field(default_factory=list)
    veo_prompts: List[Dict[str, str]] = Field(default_factory=list)
