from schemas.agent_schema import Scenario
from langgraph.types import interrupt
from states.agent_state import State

def user_select_scenario(state: State) -> State:
    result = interrupt({
        "scenarios": state.scenarios
    })

    state.final_scenario = Scenario(title=result["final_scenario"].title, content=result["final_scenario"].content)
    return state