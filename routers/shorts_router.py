# routers/agent_router.py
from fastapi import APIRouter
from services.shorts_service import resume_agent_flow, run_agent_flow
from schemas.shorts_schema import ScenarioRequest, ScenarioResponse, VideoRequest

router = APIRouter(prefix="/api/shorts/agent", tags=["Shorts Agent"])

@router.post("/scenarios", response_model=ScenarioResponse)
def invoke_agent(payload: ScenarioRequest):
    """
    LangGraph 마케팅 에이전트를 실행하여 시나리오 3개 생성 후 결과 반환
    """
    return run_agent_flow(payload)

@router.post("/videos")
def resume_agent_after_select_scenario(
    payload: VideoRequest
):
    """
    시나리오 선택 후 LangGraph 마케팅 에이전트를 재개해서 장면/장면이미지 생성 후 결과 반환
    """
    return resume_agent_flow(payload)