# services/agent_service.py
import uuid
from core.agent_graph import graph
from langgraph.types import Command
from states.agent_state import State
from schemas.agent_schema import Scenario, ScenarioRequest, ScenarioResponse, SelectScenarioRequest

async def run_agent_flow(payload: ScenarioRequest) -> ScenarioResponse:
     # 새로운 세션 ID 생성
    session_id = str(uuid.uuid4())
    
    state = State(**payload.model_dump())

    result = await graph.ainvoke(
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

async def resume_agent_flow(
    payload: SelectScenarioRequest
):
    scenario = Scenario(title=payload.title, content=payload.content)
    session_id = payload.session_id

    resumed_result = await graph.ainvoke(
        Command(resume={"final_scenario": scenario}),
        config={"configurable": {"thread_id": session_id}}
    )
    
    
    return {"message": "시나리오 확정 완료", "result": resumed_result}