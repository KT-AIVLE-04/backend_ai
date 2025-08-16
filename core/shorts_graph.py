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

from nodes.shorts.seedance_prompt_generator import seedance_prompt_generation
from nodes.shorts.video_series_generator import generate_video_series
from nodes.shorts.video_analyzer import analyze_final_video
from nodes.shorts.suno_music_prompt_generator import generate_suno_music_prompt
from nodes.shorts.music_generator import generate_music
from nodes.shorts.merge_video_audio import merge_video_with_audio

# 그래프 정의 시작
builder = StateGraph(ShortsState)

# 노드 등록
builder.add_node("analyse_input_images", analyse_input_images)
builder.add_node("create_scenarios", generate_scenarios)
builder.add_node("user_select_scenario", user_select_scenario)
builder.add_node("generate_scenes", generate_scenes)
builder.add_node("generate_scene_images", generate_scene_images)
builder.add_node("summarize_scenes", summarize_scenes)

builder.add_node("seedance_prompt_generation", seedance_prompt_generation)
builder.add_node("generate_video_series", generate_video_series)
builder.add_node("analyze_final_video", analyze_final_video)
builder.add_node("generate_suno_music_prompt", generate_suno_music_prompt)
builder.add_node("generate_music", generate_music)
builder.add_node("merge_video_with_audio", merge_video_with_audio)

# 노드 연결
builder.set_entry_point("create_scenarios")
builder.add_edge("create_scenarios", "user_select_scenario")
builder.add_edge("user_select_scenario", "analyse_input_images")
builder.add_edge("analyse_input_images", "generate_scenes")
builder.add_edge("generate_scenes", "summarize_scenes")
builder.add_edge("summarize_scenes", "generate_scene_images")
builder.add_edge("generate_scene_images", END)

# 노드 연결 테스트 필요
# builder.add_edge("generate_scene_images", "seedance_prompt_generation")
# builder.add_edge("seedance_prompt_generation", "generate_video_series")
# builder.add_edge("generate_video_series", "analyze_final_video")
# builder.add_edge("analyze_final_video", "generate_suno_music_prompt")
# builder.add_edge("generate_suno_music_prompt", "generate_music")
# builder.add_edge("generate_music", "merge_video_with_audio")
# builder.add_edge("merge_video_with_audio", END)


redis_client = redis.Redis.from_url("redis://localhost:6379")
checkpointer = RedisSaver(redis_client=redis_client, ttl={"default_ttl": 3600})
graph = builder.compile(checkpointer=checkpointer)