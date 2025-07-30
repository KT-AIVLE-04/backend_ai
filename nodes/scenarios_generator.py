# nodes/scenario_generator.py
import re
import requests
from schemas.agent_schema import AgentRequest, AgentResponse
from states.agent_state import State
from config.settings import settings


def generate_scenarios(state: State, api_key=settings.perplexity_api_key) -> State:
    prompt = (
        f"{state.store_name} ({state.store_address}) 매장의 {state.category} 업종에서 "
        f"{state.platform} 플랫폼에 맞는 최신 마케팅 트렌드에 기반한 영상 시나리오를 간단하게 3가지 알려줘."
        f"추가로 다음과 같은 사용자의 요구사항도 우선적으로 고려해서 만들어줘: {state.scenario_prompt} "
        "각 시나리오는 다음과 같은 형식으로만 제공되어야 해: "
        "**제목:** [시나리오 제목]\n"
        "**내용:** [시나리오 내용]\n"
        "예를 들면 이런식으로 작성되어야해"
         "**제목:** 감성 무드 샷\n"
         "**내용:** 트렌디한 배경음악과 함께 제품의 개성과 분위기를 감성적으로 강조하는 숏폼\n"
        "제목은 짧고 임팩트 있게, 내용은 목적이 뚜렷하고 구체적인 한두 문장으로 작성해줘."
         "각 시나리오의 '내용'은 각각 80자 이상 100자 이내로 해줘."
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "제공된 형식에 맞춰 정확한 마케팅 트렌드 기반 영상 시나리오 3가지를 생성해줘. 추가적인 설명이나 다른 텍스트는 일체 포함하지 마세요."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    response = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")

    # Parse the response to extract scenarios
    scenarios = []
    # This regex looks for "**제목:**" followed by anything non-newline, then "**내용:**" followed by anything until the next "**제목:**" or the end of the string.
    scenario_pattern = re.compile(r"\*\*제목:\*\*\s*(.*?)\n\*\*내용:\*\*\s*(.*?)(?=\n\*\*제목:\*\*|$)", re.DOTALL)
    matches = scenario_pattern.findall(answer)

    # Use a counter for sequential IDs
    scenario_counter = 1
    for match in matches:
        title = match[0].strip()
        content = match[1].strip()
        # Assign sequential ID and convert to string
        scenario_id = str(scenario_counter)
        scenarios.append({"id": scenario_id, "title": title, "content": content})
        scenario_counter += 1 # Increment the counter

    return state.model_copy(update={
      "scenarios": scenarios,
    })