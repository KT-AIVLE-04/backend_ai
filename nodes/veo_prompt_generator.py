# nodes/veo_prompt_generator.py
from openai import OpenAI
from states.agent_state import State
from config.settings import settings


client = OpenAI(api_key=settings.openai_api_key)

# - system 프롬프트
veo_system_prompt = """
You are a viral marketing expert who crafts cinematic and dynamic video prompts for Veo3.
For each scene, describe camera angles, lighting, motion, and mood to guide Veo3 video generation with realistic and cinematic direction.
"""

# - 사용자 프롬프트
def build_veo_prompt(scene: str, summary: str) -> str:
    return f"""
    Scene: {scene}
    Scene Description: {summary}

    You are generating a detailed prompt for Veo3 video generation model. Include:
    - Camera type, angle, lens, and shot movement
    - Subject appearance, emotion, and action
    - Background, environment, and time of day
    - Mood, tone, visual style
    - Lighting details and possible dynamic effects

    ⚠️ Important rules:
    1. Never change the brand name. Do not translate or alter it.
    2. All Korean text (signs, product labels, etc.) must be shown in high-resolution native Korean fonts. Never allow broken letters, ㅁ, ??, or garbled characters.
    3. Human fingers and body proportions must be natural and correct.
    4. Items (cake, coffee, etc.) should look realistic, photorealistic only.
    5. Do not include any celebrities, trademarks, or false information.
    6. The background should reflect a real, modern Korea not fantasy or exaggerated environments.
    7. All visible text or subtitles must be in native Korean (no English, no romanization).

    Please write a fluent, cinematic English paragraph that can be input into a generative model.
    Make sure the entire output is under 300 characters (including spaces and punctuation). Focus on concise but vivid descriptions suitable for generative models.
    """

# - 프롬프트 생성 함수
def generate_all_veo_prompts(state: State) -> State:
    # print('\n🏳️ 노드4 결과\n', state)
    veo_prompts = []

    for scene_id, scene_data in state.cenes.items():
        scene = scene_data["장면 제목"]
        summary = scene_data["장면 설명"]

        veo_user_prompt = build_veo_prompt(scene, summary)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": veo_system_prompt},
                {"role": "user", "content": veo_user_prompt}
            ],
            temperature=0.85,
            max_tokens=100
        )

        prompt_text = response.choices[0].message.content.strip()
        veo_prompts.append({
            "scene_id": scene_id,
            "prompt": prompt_text
        })

    return state.model_copy(update={
        "veo_prompts": veo_prompts
    })