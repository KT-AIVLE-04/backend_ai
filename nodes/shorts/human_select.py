from schemas.shorts_schema import Scenario
from langgraph.types import interrupt
from states.shorts_state import ShortsState

def user_select_scenario(state: ShortsState) -> ShortsState:
    result = interrupt({
        "scenarios": state.scenarios
    })

    state.final_scenario = Scenario(title=result["final_scenario"].title, content=result["final_scenario"].content)
    state.ad_duration = result["ad_duration"]
    state.image_list = result["image_list"]
    return state