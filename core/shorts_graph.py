# core/agent_graph.py
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.redis import RedisSaver
from nodes.shorts.input_image_analyzer import analyse_input_images
from nodes.shorts.scenes_summarizer import summarize_scenes
import redis
from nodes.shorts.scene_generator import generate_scenes
from nodes.shorts.scene_image_generator import generate_scene_images
from nodes.shorts.human_select import user_select_scenario
from states.shorts_state import ShortsState
from nodes.shorts.scenarios_generator import generate_scenarios

# 그래프 정의 시작
builder = StateGraph(ShortsState)

# 노드 등록
builder.add_node("analyse_input_images", analyse_input_images)
builder.add_node("create_scenarios", generate_scenarios)
builder.add_node("user_select_scenario", user_select_scenario)
builder.add_node("generate_scenes", generate_scenes)
builder.add_node("generate_scene_images", generate_scene_images)
builder.add_node("summarize_scenes", summarize_scenes)

# 노드 연결
builder.set_entry_point("create_scenarios")
builder.add_edge("create_scenarios", "user_select_scenario")
builder.add_edge("user_select_scenario", "analyse_input_images")
builder.add_edge("analyse_input_images", "generate_scenes")
builder.add_edge("generate_scenes", "summarize_scenes")
builder.add_edge("summarize_scenes", "generate_scene_images")
builder.add_edge("generate_scene_images", END)

redis_client = redis.Redis.from_url("redis://localhost:6379")
checkpointer = RedisSaver(redis_client=redis_client, ttl={"default_ttl": 3600})
graph = builder.compile(checkpointer=checkpointer)