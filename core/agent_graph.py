# core/agent_graph.py
from typing import Literal
from langgraph.graph import StateGraph, START, END
from states.agent_state import State
from nodes.scenarios_generator import generate_scenarios
from nodes.scenario_editor import edit_scenario
from nodes.synopsis_generator import generate_synopsis
from nodes.action_scene_generator import generate_action_scenes
from nodes.veo_prompt_generator import generate_all_veo_prompts
from nodes.flux_prompt_generator import generate_all_flux_prompts 


# 그래프 정의 시작
builder = StateGraph(State)

# 분기 처리
def has_edit_request(state: State) -> Literal["needs_edit", "skip_edit"]:
    if state.edit_request:
        return "needs_edit"
    return "skip_edit"

def should_continue(state: State) -> Literal["confirmed", "repeat"]:
    return "confirmed" if state.confirmed else "repeat"

# 노드 추가
builder.add_node("generate_scenarios", generate_scenarios)
builder.add_node("edit_scenario", edit_scenario)
builder.add_node("generate_synopsis", generate_synopsis)
builder.add_node("generate_action_scenes", generate_action_scenes)
builder.add_node("generate_all_flux_prompts", generate_all_flux_prompts)
builder.add_node("generate_all_veo_prompts", generate_all_veo_prompts)

# 노드 연결
builder.add_edge(START, "generate_scenarios")
builder.add_conditional_edges(
    "generate_scenarios",
    has_edit_request,
    {
        "needs_edit": "edit_scenario",      # 피드백 있으면 수정 흐름으로
        "skip_edit": END                    # 피드백 없으면 여기서 끝
    }
)
builder.add_conditional_edges(
    "edit_scenario",
    should_continue,
    {
        "repeat": "edit_scenario",
        "confirmed": "generate_synopsis",  # 다음 단계로 이동
    }
)
builder.add_edge("generate_synopsis", "generate_action_scenes")
# builder.add_edge("generate_action_scenes", "generate_all_flux_prompts")
builder.add_edge("generate_action_scenes", "generate_all_veo_prompts")
# builder.add_edge("generate_all_flux_prompts", END)
builder.add_edge("generate_all_veo_prompts", END)

# 컴파일
graph = builder.compile()