# AI 기반 숏폼 마케팅 에이전트
LangGraph 기반의 워크플로우로 동작하는 FastAPI 백엔드 서버입니다.  

&nbsp;
## 기능 요약
- 🎬 초기 시나리오 생성 (3개)
- ✍️ 사용자 피드백 기반 시나리오 수정
- 📖 시놉시스 생성
- 🎥 장면 구성 및 연출 요소 설계
- 🖼️ Flux / Veo용 이미지/영상 프롬프트 생성

&nbsp;
## 실행 방법

1. **환경 설정**
    `.env` 파일을 프로젝트 루트에 생성 -> 아래 내용 추가
    ```env
    OPENAI_API_KEY=your_key
    PERPLEXITY_API_KEY=your_key
    ```
    
2. **가상환경 생성 및 활성화**
    ```bash
    python3 -m venv chaos
    source chaos/bin/activate    # Windows: venv\Scripts\activate
    ```

3. **필수 패키지 설치**
    ```bash
    pip install -r requirements.txt
    ```

4. **FastAPI 서버 실행**
    ```bash
    uvicorn main:app --reload
    ```

5. **API 테스트 (예시)**
- Endpoint: POST /agent/invoke
- URL: http://localhost:8000/agent/invoke
- Headers: Content-Type: application/json
- Body (JSON):
    ```json
    {
      "store_name": "chaos 카페",
      "store_address": "경기도 하남시",
      "category": "카페",
      "platform": "Instagram",
      "scenario_prompt": "Z세대를 겨냥한 공감형 영상",
      "edit_request": [
        {
          "selected_id": "2",
          "feedback": "옥수수 시그니처 메뉴를 강조해줘."
        }
      ],
      "confirmed": true
    }
    ```

&nbsp;
## API 문서

- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc

&nbsp;
## 개발/확장 가이드

- 노드 추가/수정 (`nodes/`)
  - 기능별 노드는 `nodes/`에 파일로 분리
  - 함수 형태는 `(state: State) -> State` 유지

- StateGraph 정의 (`core/agent_graph.py`)
  - add_node, add_edge, add_conditional_edges로 노드 연결
  - 새로운 노드 추가 시 이곳에서 흐름 연결 

- State 정의 (`states/agent_state.py`)
  - 노드 간 공유되는 데이터는 State 클래스(Pydantic 모델)에 정의

- API 요청/응답 스키마 (`schemas/agent_schema.py`)
  - 프론트와 데이터 구조 맞출 때 수정

- 서비스 로직 (`services/agent_service.py`)
  - LangGraph 실행 및 State 초기화 처리
  - `routers/agent_router.py`에서 호출

- 의존성 관리
  - 패키지 추가 시 `requirements.txt`에 반영

&nbsp;
## 사용 기술 스택

- FastAPI – 백엔드 API 서버
- LangGraph / LangChain – 멀티스텝 워크플로우 구성
- OpenAI GPT / Perplexity – 콘텐츠 및 프롬프트 생성
- Pydantic – 상태 및 요청/응답 스키마 정의
