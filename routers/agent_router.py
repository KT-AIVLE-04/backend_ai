# routers/agent_router.py
from fastapi import APIRouter
from services.agent_service import resume_agent_flow, run_agent_flow
from schemas.agent_schema import ScenarioRequest, ScenarioResponse, SelectScenarioRequest

router = APIRouter(prefix="/api/shorts/scenario", tags=["Agent"])

@router.post("/invoke", response_model=ScenarioResponse)
async def invoke_agent(payload: ScenarioRequest):
    """
    LangGraph 마케팅 에이전트를 실행하고 결과 반환
    """
    return await run_agent_flow(payload)

@router.post("/select")
async def select_scenario(
    payload: SelectScenarioRequest
):
    """
    시나리오 선택 후 LangGraph 마케팅 에이전트를 재개하고 결과 반환
    """
    return await resume_agent_flow(payload)