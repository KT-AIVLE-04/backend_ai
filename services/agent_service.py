# services/agent_service.py
from core.agent_graph import graph
from states.agent_state import State
from schemas.agent_schema import AgentRequest, AgentResponse

def run_agent_flow(payload: AgentRequest) -> AgentResponse:
    state = State(**payload.dict()) 
    result = graph.invoke(state)
    result_dict = dict(result)
    # print("[CHECK] AgentResponse(**result_dict):", AgentResponse(**result_dict))
    return AgentResponse(**result_dict)