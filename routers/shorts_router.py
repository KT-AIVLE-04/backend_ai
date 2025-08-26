# routers/agent_router.py
import os
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pathlib import Path
from typing import Optional, Dict
from services.shorts_service import resume_agent_flow, run_agent_flow
from schemas.shorts_schema import ScenarioRequest, ScenarioResponse, VideoRequest, VideoResponse

router = APIRouter(prefix = "/api/shorts/agent", tags=["Shorts Agent"])
video_sessions: Dict[str, dict] = {}

@router.post("/scenarios", response_model = ScenarioResponse)
async def invoke_agent(payload: ScenarioRequest):
    """
    LangGraph 마케팅 에이전트를 실행하여 시나리오 3개 생성 후 결과 반환
    """
    return run_agent_flow(payload)


@router.post("/videos", response_model = VideoResponse)
async def resume_agent_after_select_scenario(payload: VideoRequest):
    """
    시나리오 선택 후 LangGraph 마케팅 에이전트를 재개해서 장면/장면이미지 생성 후 결과 반환
    """
    response = resume_agent_flow(payload)

    if response.key:
        video_sessions[payload.session_id] = {
            "key": response.key
        }
    
    return response
