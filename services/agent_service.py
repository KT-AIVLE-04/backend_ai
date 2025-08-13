# services/agent_service.py
import uuid
from core.agent_graph import graph
from langgraph.types import Command
from states.agent_state import State
from schemas.agent_schema import Scenario, ScenarioRequest, ScenarioResponse, InputImageInfo, VideoRequest, VideoResponse

def run_agent_flow(payload: ScenarioRequest) -> ScenarioResponse:
     # 새로운 세션 ID 생성
    session_id = str(uuid.uuid4())
    
    state = State(**payload.model_dump())

    result = graph.invoke(
        state,
        config={"configurable": {"thread_id": session_id}}
    )

    if "__interrupt__" in result:
        # interrupt에서 시나리오 추출
        interrupt_data = result["__interrupt__"][0].value
        scenarios = interrupt_data.get("scenarios", [])
        
        # ScenarioResponse로 반환
        return ScenarioResponse(session_id=session_id, scenarios=scenarios)

    return ScenarioResponse(session_id=session_id, scenarios=[])

def resume_agent_flow(
    payload: VideoRequest
) -> VideoResponse:
    session_id = payload.session_id
    scenario = Scenario(title=payload.title, content=payload.content)
    image_list = [
        InputImageInfo(url=url) for url in payload.image_list
    ]

    resumed_result = graph.invoke(
        Command(resume={"final_scenario": scenario, "ad_duration": payload.ad_duration, "image_list": image_list}),
        config={"configurable": {"thread_id": session_id}}
    )
    
    print(resumed_result)
    print(type(resumed_result))
    
    return VideoResponse(
        scenes=resumed_result["scenes"], 
        ai_scenes_image_list=resumed_result["scenes_image_list"]
    )