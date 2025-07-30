# nodes/synopsis_generator.py
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from states.agent_state import State
from config.settings import settings

def generate_synopsis(state: State) -> State:
    # print('\n🏳️ 노드2 결과\n', state)

    prompt_storyline = PromptTemplate(
        input_variables = ['scenario'],
        template =
"""
당신은 1000만 조회수 SNS 영상을 만든 바이럴 마케팅 전문가로서, 소비자의 감정을 자극하고 행동을 유도하는 강력한 시놉시스를 작성합니다.

다음은 주어진 시나리오입니다. 꼼꼼하게 검토하세요. \n\n {scenario} \n\n


다음은 시놉시스 작성 공식입니다. 꼼꼼하게 검토하세요. \n
**시놉시스 작성 공식**:
    **[HOOK - 1줄]**: "당신도 이런 경험 있나요?" / "3초 뒤 충격적인 반전이..."와 같이 소비자가 첫 3초 안에 보고싶도록 만드는 강력한 hook
    **[문제 제기 - 2줄]**: 타겟 소비자의 구체적 페인포인트와 공감대 형성
    **[솔루션 제시 - 3줄]**: 제품/매장/서비스의 혁신적 해결 방식과 차별점 강조
    **[변화 비전 - 2줄]**: "이제 당신의 삶은..."과 같은 형태의 이상적 미래 제시 (변화된 삶의 모습 시각화)
    **[콜투액션 - 1줄]**: "지금 바로 oo하세요!"와 같이 소비자에게 구체적이고 즉각적인 행동 유도 \n\n

다음은 시놉시스의 톤앤매너입니다. 꼼꼼하게 검토하세요. \n
**톤앤매너**:
    - SNS 플랫폼에 최적화된 짧고 임팩트 있는 문체
    - 감탄사와 강조 표현 적극 활용 \n\n

이제 위의 시나리오, 시놉시스 작성 공식, 그리고 톤앤매너를 바탕으로 **SNS에서 바이럴될 수 있는 강렬한 시놉시스를 8~10줄 이내로 작성**하세요.
각 줄이 소비자의 감정을 끌어올리는 **계단식 구조**로 작성하세요.
"""
    )

    llm = ChatOpenAI(temperature = 0.8, model = "gpt-4o-mini", streaming = True, api_key=settings.openai_api_key)
    chain_synopsis = prompt_storyline | llm | StrOutputParser()
    synopsis = chain_synopsis.invoke({'scenario': state.final_scenario['content']})

    return state.model_copy(update={
      "synopsis": synopsis
    })