# core/agent_graph.py
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from nodes.action_scene_generator import generate_action_scenes
from nodes.human_select import user_select_scenario
from states.agent_state import State
from nodes.scenarios_generator import generate_scenarios

# 그래프 정의 시작
builder = StateGraph(State)

# 노드 등록
builder.add_node("create_scenarios", generate_scenarios)
builder.add_node("user_select_scenario", user_select_scenario)
builder.add_node("generate_scenes", generate_action_scenes)

# 노드 연결
builder.set_entry_point("create_scenarios")
builder.add_edge("create_scenarios", "user_select_scenario")
builder.add_edge("user_select_scenario", "generate_scenes")
builder.add_edge("generate_scenes", END)

# # 분기 처리
# def has_edit_request(state: State) -> Literal["needs_edit", "skip_edit"]:
#     if state.edit_request:
#         return "needs_edit"
#     return "skip_edit"

# def should_continue(state: State) -> Literal["confirmed", "repeat"]:
#     return "confirmed" if state.confirmed else "repeat"

# # 노드 추가
# builder.add_node("generate_scenarios", generate_scenarios)
# builder.add_node("edit_scenario", edit_scenario)
# builder.add_node("generate_synopsis", generate_synopsis)
# builder.add_node("generate_action_scenes", generate_action_scenes)
# builder.add_node("generate_all_flux_prompts", generate_all_flux_prompts)
# builder.add_node("generate_all_veo_prompts", generate_all_veo_prompts)

# # 노드 연결
# builder.add_edge(START, "generate_scenarios")
# builder.add_conditional_edges(
#     "generate_scenarios",
#     has_edit_request,
#     {
#         "needs_edit": "edit_scenario",      # 피드백 있으면 수정 흐름으로
#         "skip_edit": END                    # 피드백 없으면 여기서 끝
#     }
# )
# builder.add_conditional_edges(
#     "edit_scenario",
#     should_continue,
#     {
#         "repeat": "edit_scenario",
#         "confirmed": "generate_synopsis",  # 다음 단계로 이동
#     }
# )
# builder.add_edge("generate_synopsis", "generate_action_scenes")
# # builder.add_edge("generate_action_scenes", "generate_all_flux_prompts")
# builder.add_edge("generate_action_scenes", "generate_all_veo_prompts")
# # builder.add_edge("generate_all_flux_prompts", END)
# builder.add_edge("generate_all_veo_prompts", END)

# 컴파일
checkpointer = InMemorySaver()
graph = builder.compile(
    checkpointer=checkpointer
)