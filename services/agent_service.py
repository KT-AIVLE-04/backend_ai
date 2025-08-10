# services/agent_service.py
import uuid
from core.agent_graph import graph
from langgraph.types import Command
from states.agent_state import State
from schemas.agent_schema import ActionScenesResponse, Scenario, ScenarioRequest, ScenarioResponse, ActionScenesRequest

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
    payload: ActionScenesRequest
) -> ActionScenesResponse:
    scenario = Scenario(title=payload.title, content=payload.content)
    session_id = payload.session_id

    resumed_result = graph.invoke(
        Command(resume={"final_scenario": scenario, "ad_duration": payload.ad_duration}),
        config={"configurable": {"thread_id": session_id}}
    )
    
    print(resumed_result)
    print(type(resumed_result))

    return ActionScenesResponse(session_id=session_id, scenes=resumed_result["action_scenes"], scenes_image_list=resumed_result["image_list"], ai_scenes_image_list=resumed_result["action_scenes_image_list"])