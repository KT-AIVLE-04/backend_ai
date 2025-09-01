# Backend AI API

LangGraph 기반의 AI 마케팅 에이전트 시스템입니다. 숏폼 영상 생성, SNS 게시글 생성, 댓글 분석, 성과 리포트 생성 기능을 제공합니다.

## 🚀 주요 기능

### 1. 숏폼 영상 생성 (`/api/shorts/agent`)
- **시나리오 생성**: 매장 정보와 요구사항을 기반으로 3개의 시나리오 생성
- **영상 제작**: 선택된 시나리오로 장면별 이미지 및 동영상 생성
- **음악 생성**: Suno API를 활용한 배경음악 자동 생성
- **최종 합성**: 영상과 음악을 결합하여 완성된 숏폼 영상 제작

### 2. SNS 게시글 생성 (`/sns-post/agent`)
- **콘텐츠 분석**: 이미지/텍스트 콘텐츠 자동 분석
- **트렌드 분석**: 최신 SNS 트렌드 및 키워드 분석
- **게시글 생성**: 플랫폼별 최적화된 게시글 작성
- **해시태그 생성**: 효과적인 해시태그 자동 생성

### 3. 댓글 분석 (`/api/comments`)
- **감정 분석**: 댓글의 긍정/부정/중립 감정 분석
- **키워드 추출**: 감정별 핵심 키워드 추출

### 4. 성과 분석 리포트 (`/api/analysis`)
- **종합 성과 분석**: 게시글 성과 종합 분석
- **마크다운 리포트**: 실행 가능한 인사이트가 포함된 전문 리포트 생성


## 🛠️ 설치 및 실행

### 1. 환경 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가:

```env
# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Anthropic Claude API  
ANTHROPIC_API_KEY=your_claude_api_key

# Perplexity API (트렌드 분석용)
PERPLEXITY_API_KEY=your_perplexity_api_key

# Replicate API (이미지/영상 생성용)
REPLICATE_API_TOKEN=your_replicate_token

# Suno API (음악 생성용)
SUNO_API_KEY=your_suno_api_key

# AWS S3 (파일 저장용)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=your_aws_region

# Redis (LangGraph 체크포인트용)
REDIS_URL=redis://localhost:6379
```

### 2. 가상환경 생성 및 활성화

```bash
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. Redis 서버 실행

```bash
# Docker 사용 시
docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest

# 또는 로컬 설치된 Redis
redis-server
```

### 5. FastAPI 서버 실행

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

서버가 정상 실행되면 다음 URL에서 확인 가능합니다:
- API 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## 📖 API 사용법

### 1. 숏폼 영상 생성

#### 1-1. 시나리오 생성
```bash
curl -X POST "http://localhost:8000/api/shorts/agent/scenarios" \
  -H "Content-Type: application/json" \
  -d '{
    "store_name": "카페 모모",
    "business_type": "카페",
    "brand_concept": ["모던", "심플", "따뜻한"],
    "platform": "Instagram",
    "ad_type": "제품홍보",
    "target_audience": "2030 직장인",
    "scenario_prompt": "새로 출시한 시그니처 음료를 강조하는 영상"
  }'
```

#### 1-2. 영상 생성 (시나리오 선택 후)
```bash
curl -X POST "http://localhost:8000/api/shorts/agent/videos" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "받은_세션_ID",
    "title": "선택된 시나리오 제목",
    "content": "선택된 시나리오 내용",
    "ad_duration": 15,
    "image_list": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ]
  }'
```

### 2. SNS 게시글 생성

#### 2-1. 전체 생성 (게시글 + 해시태그)
```bash
curl -X POST "http://localhost:8000/sns-post/agent/post" \
  -H "Content-Type: application/json" \
  -d '{
    "content_data": "/path/to/image.jpg",
    "user_keywords": ["맛집", "카페"],
    "sns_platform": "instagram",
    "business_type": "카페",
    "location": "서울시 강남구"
  }'
```

#### 2-2. 해시태그만 생성
```bash
curl -X POST "http://localhost:8000/sns-post/agent/tag" \
  -H "Content-Type: application/json" \
  -d '{
    "post_title": "오늘의 시그니처 음료",
    "post_content": "새로운 맛을 경험해보세요!",
    "user_keywords": ["카페", "음료"],
    "sns_platform": "instagram",
    "business_type": "카페",
    "location": "서울시 강남구"
  }'
```

### 3. 댓글 분석 (감정 분석 및 키워드 추출)

```bash
curl -X POST "http://localhost:8000/api/comments/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "comments": [
      {
        "id": 1,
        "content": "정말 맛있어요! 추천합니다"
      },
      {
        "id": 2,
        "content": "가격이 좀 비싸네요"
      },
      {
        "id": 3,
        "content": "배고파요"
      }
    ]
  }'
```

### 4. 성과 분석 리포트

```bash
curl -X POST "http://localhost:8000/api/analysis/report" \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": {
      "post_id": 123,
      "view_count": 10000,
      "like_count": 500,
      "comment_count": 50
    },
    "emotion_data": {
      "positive_count": 30,
      "negative_count": 10,
      "neutral_count": 10,
      "positive_keywords": ["맛있다", "좋다", "추천"],
      "negative_keywords": ["비싸다", "별로"],
      "neutral_keywords": ["그냥", "보통"]
    },
    "title": "시그니처 음료 출시",
    "description": "새로운 시그니처 음료를 소개합니다",
    "url": "https://example.com/post/123",
    "tags": ["카페", "음료", "신제품"],
    "publish_at": "2024-01-15"
  }'
```

## 🧪 테스트

### 기본 테스트
```bash
# Health Check
curl http://localhost:8000/health

# API 문서 접속
curl http://localhost:8000/docs
```

## 📁 프로젝트 구조

```
├── main.py                          # FastAPI 애플리케이션 진입점
├── core/                            # LangGraph 워크플로우 정의
│   ├── shorts_graph.py             # 숏폼 영상 생성 그래프
│   └── sns_post_graph.py           # SNS 게시글 생성 그래프
├── nodes/                          # LangGraph 노드 구현
│   ├── shorts/                     # 숏폼 관련 노드
│   ├── sns_post/                   # SNS 게시글 관련 노드
│   └── comments_analyzer/          # 댓글 분석 관련 노드
├── states/                         # 상태 정의 (Pydantic 모델)
├── schemas/                        # API 요청/응답 스키마
├── services/                       # 비즈니스 로직
├── routers/                        # FastAPI 라우터
├── repositories/                   # 데이터 접근 계층
├── utils/                          # 유틸리티 함수
└── requirements.txt                # 패키지 의존성
```

## ⚙️ 주요 설정

### LangGraph 체크포인트
- Redis를 사용하여 워크플로우 상태 저장
- 세션 기반 상태 관리로 중단/재개 가능

### 파일 저장
- 로컬: `./videos/`, `./audio/`, `./final/` 폴더
- 클라우드: AWS S3 버킷

### API 제한
- OpenAI: GPT-4o, GPT-4o-mini 모델 사용
- Claude: Sonnet 4 모델 사용  
- Replicate: Seedance, Flux 모델 사용
- Suno: V4.5+ 음악 생성 모델 사용

## 🚨 주의사항

1. **API 키 보안**: `.env` 파일을 반드시 `.gitignore`에 추가
2. **리소스 관리**: 영상 생성 시 디스크 공간 충분히 확보
3. **Redis 연결**: LangGraph 체크포인트를 위해 Redis 필수
4. **API 제한**: 각 외부 API의 사용량 제한 확인
5. **파일 권한**: 영상/음성 파일 저장을 위한 쓰기 권한 필요

## 📞 지원

- 이슈 리포트: GitHub Issues
- API 문서: `/docs` 엔드포인트
