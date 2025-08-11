# nodes/flux_prompt_generator.py
from openai import OpenAI
from states.agent_state import State
from config.settings import settings


client = OpenAI(api_key=settings.openai_api_key)

# - system 프롬프트
flux_system_prompt = """
You are a storyboard expert for ad production who generates cinematic and highly detailed image prompts for Flux. Based on the given summary, create a visually compelling scene that reflects the marketing strategy. Focus on mood, subject placement, and emotion to guide Flux image generation.
"""

# - 사용자 프롬프트
def build_flux_prompt(scene: str, summary: str) -> str:
    return f"""
    Scene: {scene}
    Scene Description: {summary}

    You are generating a detailed prompt for Flux image generation model. Include:
    - Camera type, lens, and angle
    - Subject appearance, emotion, and pose
    - Background elements, setting, and time of day
    - Visual style, mood, and composition
    - Lighting type and atmosphere

    ⚠️ Important rules:
    1. Never change the brand name. Do not translate or alter it.
    2. All Korean text (signs, product labels, etc.) must be in native Korean fonts. Never allow broken letters, ㅁ, ??, or garbled characters.
    3. Human body proportions and fingers must look natural.
    4. All items must be photorealistic.
    5. No celebrities, trademarks, or false elements.
    6. The setting should reflect real, modern Korea.
    7. All text in the image must be native Korean (no English or romanization).

    Write a cinematic English paragraph for a still image, under 300 characters. Be vivid and specific, but concise and generative-model friendly.

    """

# - 프롬프트 생성 함수
def generate_all_flux_prompts(state: State) -> State:
    flux_prompts = []

    for scene_id, scene_data in state.scenes.items():
        scene = scene_data["장면 제목"]
        summary = scene_data["장면 설명"]

        flux_user_prompt = build_flux_prompt(scene, summary)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": flux_system_prompt},
                {"role": "user", "content": flux_user_prompt}
            ],
            temperature=0.85,
            max_tokens=100
        )

        prompt_text = response.choices[0].message.content.strip()
        flux_prompts.append({
            "scene_id": scene_id,
            "prompt": prompt_text
        })

    return state.model_copy(update={
        "flux_prompts": flux_prompts
    })