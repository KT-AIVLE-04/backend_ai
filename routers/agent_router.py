# routers/agent_router.py
from fastapi import APIRouter
from services.agent_service import run_agent_flow
from schemas.agent_schema import AgentRequest, AgentResponse

router = APIRouter(prefix="/agent", tags=["Agent"])

@router.post("/invoke", response_model=AgentResponse)
def invoke_agent(payload: AgentRequest):
    """
    LangGraph 마케팅 에이전트를 실행하고 결과 반환
    """
    return run_agent_flow(payload)