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

    if response.final_video_path:
        video_sessions[payload.session_id] = {
            "final_video_path": response.final_video_path,
            "final_video_filename": response.final_video_filename,
            "scene_video_urls": response.scene_video_urls
        }
    
    return response




################ LLM 작성 코드 (확인 필요) ################
@router.get("/video/{session_id}/download")
async def download_final_video(session_id: str):
    """비디오 다운로드"""
    session_info = video_sessions.get(session_id)

    if not session_info:
        raise HTTPException(status_code = 404, detail = "Session not found")
    
    video_path = Path(session_info["final_video_path"])
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        path = str(video_path),
        media_type = "video/mp4",
        filename = session_info["final_video_filename"],
        headers = {
            "Content-Disposition": f'attachment; filename="{session_info["final_video_filename"]}"'
        }
    )


@router.get("/video/{session_id}/stream")
async def stream_final_video(session_id: str, range: Optional[str] = None):
    """최종 비디오 스트리밍 (Range Request 지원)"""
    session_info = video_sessions.get(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    video_path = Path(session_info["final_video_path"])
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    file_size = video_path.stat().st_size
    
    # Range Request 처리
    if range:
        start = 0
        end = file_size - 1
        
        range_str = range.replace("bytes=", "")
        if "-" in range_str:
            start_str, end_str = range_str.split("-")
            if start_str:
                start = int(start_str)
            if end_str:
                end = int(end_str)
        
        content_length = end - start + 1
        
        def iterfile():
            with open(video_path, "rb") as file:
                file.seek(start)
                remaining = content_length
                while remaining:
                    chunk_size = min(8192, remaining)
                    data = file.read(chunk_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data
        
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": "video/mp4",
        }
        
        return StreamingResponse(iterfile(), status_code=206, headers=headers)
    
    return FileResponse(
        path = str(video_path),
        media_type = "video/mp4",
        headers = {"Accept-Ranges": "bytes"}
    )


@router.get("/video/{session_id}/scenes")
async def get_scene_videos(session_id: str):
    """개별 씬 비디오 URL 목록 조회"""
    session_info = video_sessions.get(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return JSONResponse(content={
        "session_id": session_id,
        "scene_count": len(session_info["scene_video_urls"]),
        "scene_video_urls": session_info["scene_video_urls"],
        "metadata": session_info["metadata"]
    })


@router.get("/video/{session_id}/scene/{scene_index}")
async def get_scene_video_url(session_id: str, scene_index: int):
    """특정 씬 비디오 URL 조회"""
    session_info = video_sessions.get(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    scene_urls = session_info["scene_video_urls"]
    if scene_index < 0 or scene_index >= len(scene_urls):
        raise HTTPException(status_code=404, detail="Scene index out of range")
    
    return JSONResponse(content={
        "session_id": session_id,
        "scene_index": scene_index,
        "scene_url": scene_urls[scene_index],
        "total_scenes": len(scene_urls)
    })


@router.get("/video/{session_id}/info")
async def get_video_info(session_id: str):
    """비디오 세션 전체 정보 조회"""
    session_info = video_sessions.get(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    video_path = Path(session_info["final_video_path"])
    
    return JSONResponse(content={
        "session_id": session_id,
        "final_video": {
            "filename": session_info["final_video_filename"],
            "path": session_info["final_video_path"],
            "exists": video_path.exists(),
            "size_mb": round(video_path.stat().st_size / (1024 * 1024), 2) if video_path.exists() else 0
        },
        "scenes": {
            "count": len(session_info["scene_video_urls"]),
            "urls": session_info["scene_video_urls"]
        },
        "metadata": session_info["metadata"]
    })