# nodes/scenario_editor.py
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from states.shorts_state import ShortsState
from config.settings import settings


def edit_scenario(state: ShortsState) -> ShortsState:

    if not state.edit_request:
        print("[edit_scenario] edit_request 없음 → 처리 생략")
        return state
    
    latest_request = state.edit_request[-1]
    selected_id = latest_request.get("selected_id", None)
    feedback = latest_request.get("feedback", "").strip()

    if not selected_id:
        raise ValueError("selected_id가 제공되지 않았습니다.")

    selected_scenario = next((s for s in state.scenarios if s["id"] == selected_id), None)
    if not selected_scenario:
        raise ValueError(f"ID가 {selected_id}인 시나리오를 찾을 수 없습니다.")

    scenario_text = f"[{selected_scenario['id']}] {selected_scenario['title']}: {selected_scenario['content']}"

    full_feedback_history = "\n".join(
        f"- {req.get('feedback', '').strip()}"
        for req in state.edit_request if req.get("feedback")
    )

    prompt = PromptTemplate(
        input_variables=["scenario_text", "full_feedback_history", "feedback"],
        template=
"""
당신은 숏폼 광고 영상(쇼츠) 기획을 위한 콘텐츠 시나리오 에디터입니다.
사용자가 선택한 아래 시나리오와 피드백을 기반으로, 영상화 가능한 구체적인 장면 중심 시나리오를 1개 작성해주세요.

---

**[수정 대상 시나리오]**
{scenario_text}

**[이전 피드백 이력]**
{full_feedback_history}

**[최신 피드백]**
{feedback}

---

**[작성 기준]**

- 이 시나리오는 쇼츠 영상화의 기반이 됩니다. 반드시 **시각적으로 직관적인 장면 단위**로 작성해야 합니다.
- 다음의 다섯 요소를 모두 고려해 작성하세요:
  - **누가** (등장인물 및 감정)
  - **언제** (시간적 배경: 아침, 점심, 밤 등)
  - **어디서** (매장·공간의 특징 포함)
  - **무엇을** (행동: 주문, 리액션 등)
  - **어떻게** (반전, 유머, 밈 등 극적 요소 포함)

- “감성적인 분위기”, “행복한 순간”처럼 **모호하고 추상적인 표현은 절대 사용하지 마세요.**
- **짧고 강렬한 시각적 연출**이 가능한 상황으로 구성하고, 해당 카페/매장의 특색을 드러낼 것.
- **유행 밈**, **반전 요소**, **극적인 리액션**을 적극 활용해 Z세대 시청자의 이목을 끌 수 있도록 하세요.

---

**[출력 형식]**
title: (수정된 시나리오 제목)
content: (100자 이내의 구체적인 장면 설명)

※ 오직 위 형식에 맞춰 시나리오 1개만 출력해주세요. 추가 설명은 금지합니다.
"""
    )

    llm = ChatOpenAI(temperature=0.8, model="gpt-4o-mini", streaming=False, api_key=settings.openai_api_key)
    chain_scenario = prompt | llm | StrOutputParser()
    raw_output = chain_scenario.invoke({
        "scenario_text": scenario_text,
        "full_feedback_history": full_feedback_history,
        "feedback": feedback
    }).strip()

    lines = raw_output.splitlines()
    title_line = next((l for l in lines if l.lower().startswith("title:")), "").strip()
    desc_line = next((l for l in lines if l.lower().startswith("content:")), "").strip()

    final_scenario = {
        "id": selected_id,
        "title": title_line.replace("title:", "").strip(),
        "content": desc_line.replace("content:", "").strip(),
    }

    updated_scenarios = []
    for s in state.scenarios:
        if s["id"] == selected_id:
            updated_scenarios.append(final_scenario)
        else:
            updated_scenarios.append(s)


    chatbot_answer = f"""
피드백을 반영해서 시나리오를 다음과 같이 수정했습니다.

제목 - {final_scenario['title']}
시나리오 - {final_scenario['content']}

마음에 드시나요? 더 다듬을 부분 있으면 말씀해주세요.
""".strip()

    return state.model_copy(update={
      "final_scenario": final_scenario,
      "chatbot_answer": chatbot_answer,
      "scenarios": updated_scenarios
    })
