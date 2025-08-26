from config.settings import settings
import anthropic
import json

def generate_korean_markdown_report(report_data: dict, analysis_data) -> str:
    """한국어 markdown 보고서 변환"""

    client = anthropic.Anthropic(api_key = settings.claude_api_key)
    
    system_prompt = """
    당신은 디지털 마케팅 보고서 작성 전문가입니다. 
    20년 이상의 경력을 보유한 SNS 마케팅 컨설턴트로서, 복잡한 데이터 분석 결과를 
    경영진과 실무진 모두가 이해할 수 있는 명확하고 인사이트가 있는 보고서로 작성합니다.
    
    보고서 작성 원칙:
    1. 데이터 기반의 객관적 서술과 전문가적 통찰의 균형
    2. 시각적 계층 구조를 활용한 가독성 높은 문서 구성
    3. 즉시 실행 가능한 구체적인 액션 아이템 제시
    4. 전문 용어는 필요시 간단한 설명 추가
    5. 핵심 메시지를 강조하되 과도한 수식어 지양
    
    마크다운 문법을 정확히 사용하여 웹과 문서에서 모두 아름답게 표현되는 보고서를 작성하세요.
    반드시 순수한 마크다운 텍스트 문자열로만 응답하세요. JSON이나 다른 형식으로 감싸지 마세요.
    """
    
    prompt = f"""
    다음 SNS 게시글 성과 분석 JSON 데이터를 기반으로 전문적인 한국어 마크다운 보고서를 작성해주세요.
    
    원본 게시글 정보:
    - 제목: {analysis_data.title}
    - URL: {analysis_data.url}
    - 플랫폼: YouTube
    - 업종: {analysis_data.industry}
    - 게시일: {analysis_data.publish_at}
    
    분석 결과 JSON:
    ```json
    {json.dumps(report_data, ensure_ascii = False, indent = 2)}
    ```
    
    다음 구조로 정교하고 전문적인 한국어 마크다운 보고서를 작성해주세요.
    중요: 순수한 마크다운 텍스트만 출력하고, ```markdown 블록이나 다른 래핑 없이 바로 마크다운 내용을 작성하세요.
    

    # 📊 SNS 게시글 성과 분석 보고서
    
    ## 📋 개요 (Executive Summary)
    - 핵심 성과 지표를 한눈에 볼 수 있는 대시보드 형태
    - 전체 성과 점수와 등급을 시각적으로 표현
    - 3줄 요약으로 핵심 인사이트 제시
    
    ## 🎯 성과 평가
    ### 종합 성과
    - 성과 점수와 등급을 강조
    - 벤치마크 대비 위치 설명
    
    ### 콘텐츠 효과성 분석
    - 제목 영향력, 콘텐츠 참여도 등을 표나 리스트로 정리
    - 각 지표별 개선 포인트 명시
    
    ## 📈 상세 분석
    ### 참여 지표 분석
    - 주요 비율 지표들을 시각적으로 표현 (이모지, 프로그레스바 느낌)
    - 업계 평균 대비 비교
    
    ### 감정 분석
    - 긍정/부정/중립 비율을 시각화
    - 주요 감정 키워드와 논의 품질
    
    ### SWOT 분석
    - 4사분면 표 형태로 구성
    - 각 항목별 구체적 설명 추가
    
    ## 💡 핵심 인사이트
    - 발견된 패턴, 이상 징후, 트렌드를 번호 매긴 리스트로
    - 각 인사이트별 신뢰도와 비즈니스 영향도 표시
    - ⚠️ 중요 인사이트는 강조 표시
    
    ## 🎬 콘텐츠 개선 제안
    - 우선순위별로 정렬된 추천 사항
    - 각 제안별 기대 ROI와 실행 난이도를 태그로 표시
    - 구체적인 개선 전/후 예시 제공
    
    ## 🚀 실행 전략
    ### ⏱️ 단계별 실행 계획
    #### 즉시 실행 (24시간 이내)
    - [ ] 체크박스 형태의 액션 아이템
    
    #### 단기 전략 (7일)
    - 구체적 KPI 목표와 예산 배분
    
    #### 중기 전략 (30일)
    - 주간 콘텐츠 캘린더 표
    - A/B 테스트 계획
    
    #### 장기 전략 (90일)
    - 로드맵 형태로 마일스톤 제시
    
    ## 📌 우선순위 액션 아이템
    크리티컬/높음/중간/낮음으로 구분된 표 형태:
    | 우선순위 | 액션 | 담당자 | 기한 | 성공 지표 |
    
    ## 🔍 다음 단계
    - 후속 분석이 필요한 영역
    - 모니터링해야 할 지표
    - 정기 리뷰 일정
    
    보고서 작성 시 주의사항:
    1. 모든 수치는 적절히 포맷팅 (천 단위 쉼표, 퍼센트 등)
    2. 중요 수치는 **굵게** 표시
    3. 긍정적 지표는 🟢, 부정적 지표는 🔴, 중립은 🟡로 표시
    4. 표, 리스트, 인용구 등 다양한 마크다운 요소 활용
    5. 섹션 간 적절한 공백으로 가독성 확보
    6. 기술적 용어는 이해하기 쉽게 설명
    7. > 인용구를 활용한 핵심 메시지 강조
    8. 코드 블록 ```을 활용한 구체적 예시 제공
    
    반드시 실무에서 바로 사용할 수 있는 전문적이고 아름다운 마크다운 보고서를 작성해주세요.
    이모지를 적절히 사용하되 과하지 않게 균형을 맞춰주세요.
    """
    
    try:
        response = client.messages.create(
            model = "claude-sonnet-4-20250514",
            max_tokens = 6500,
            temperature = 0.2,
            system = system_prompt,
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        markdown_report = response.content[0].text.strip()

        if markdown_report.startswith("```markdown"):
            markdown_report = markdown_report.replace("```markdown", "").replace("```", "").strip()
        
        elif markdown_report.startswith("```"):
            markdown_report = markdown_report.replace("```", "").strip()
        
        # 마크다운 포맷 검증
        if not markdown_report.startswith("#"):
            markdown_report = "# 📊 SNS 게시글 성과 분석 보고서\n\n" + markdown_report
        
        if not isinstance(markdown_report, str):
            markdown_report = str(markdown_report)
        
        return markdown_report
        
    except Exception as e:
        return generate_fallback_markdown_report(report_data, analysis_data)



def generate_fallback_markdown_report(report_data: dict, analysis_data) -> str:
    """
    Claude API 호출 실패 시 기본 markdown 보고서 템플릿
    """
    performance_score = report_data.get("performance_score", 0)
    performance_grade = report_data.get("performance_grade", "N/A")
    
    # 등급별 이모지
    grade_emoji = {
        "S": "🏆", "A": "🥇", "B": "🥈", 
        "C": "🥉", "D": "⚠️", "N/A": "❓"
    }
    
    markdown = f"""# 📊 SNS 게시글 성과 분석 보고서

    ## 📋 개요

    ### 게시글 정보
    - **제목**: {analysis_data.title}
    - **URL**: {analysis_data.url}
    - **플랫폼**: YouTube
    - **업종**: {analysis_data.industry}
    - **게시일**: {analysis_data.publish_at}

    ### 종합 성과
    > **성과 점수**: {performance_score:.1f}/100점 {grade_emoji.get(performance_grade, "")}
    > **성과 등급**: {performance_grade}등급

    ---

    ## 🎯 콘텐츠 효과성

    ### 주요 지표
    | 지표 | 점수 | 평가 |
    |------|------|------|
    | 제목 영향력 | {report_data.get('content_effectiveness', {}).get('title_impact_score', 0):.1f} | {get_score_label(report_data.get('content_effectiveness', {}).get('title_impact_score', 0))} |
    | 콘텐츠 참여도 | {report_data.get('content_effectiveness', {}).get('content_engagement_score', 0):.1f} | {get_score_label(report_data.get('content_effectiveness', {}).get('content_engagement_score', 0))} |
    | 메시지 명확성 | - | {report_data.get('content_effectiveness', {}).get('message_clarity', 'N/A')} |
    | CTA 효과성 | - | {report_data.get('content_effectiveness', {}).get('cta_effectiveness', 'N/A')} |

    ### 개선 필요 영역
    """
        
    # 개선 영역 추가
    for area in report_data.get('content_effectiveness', {}).get('improvement_areas', []):
        markdown += f"- {area}\n"
    
    # 상세 분석 섹션
    markdown += f"""

    ---

    ## 📈 상세 분석

    ### 참여 지표
    - **참여율**: {report_data.get('detailed_analysis', {}).get('engagement_metrics', {}).get('engagement_rate', 0):.2%}
    - **좋아요/조회수 비율**: {report_data.get('detailed_analysis', {}).get('engagement_metrics', {}).get('like_to_view_ratio', 0):.3f}
    - **댓글/좋아요 비율**: {report_data.get('detailed_analysis', {}).get('engagement_metrics', {}).get('comment_to_like_ratio', 0):.3f}

    ### 감정 분석
    - **감정 점수**: {report_data.get('detailed_analysis', {}).get('sentiment_analysis', {}).get('sentiment_score', 0):.1f}/100
    - **논란 지수**: {report_data.get('detailed_analysis', {}).get('sentiment_analysis', {}).get('controversy_index', 0):.1f}/100
    - **감정 강도**: {report_data.get('detailed_analysis', {}).get('sentiment_analysis', {}).get('emotional_intensity', 'N/A')}
    - **토론 품질**: {report_data.get('detailed_analysis', {}).get('sentiment_analysis', {}).get('discussion_quality', 'N/A')}

    ---

    ## 💡 핵심 인사이트
    """
        
        # 인사이트 추가
    for i, insight in enumerate(report_data.get('insights', []), 1):
        confidence_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}
        
        markdown += f"""
        ### {i}. {insight.get('type', '').upper()} 분석
        - **발견 사항**: {insight.get('finding', '')}
        - **신뢰도**: {confidence_emoji.get(insight.get('confidence', ''), '')} {insight.get('confidence', '')}
        - **비즈니스 영향**: {insight.get('business_impact', '')}
        """
        
    # 추천사항 섹션
    markdown += """

    ---

    ## 🎬 콘텐츠 개선 제안
    """
        
    for rec in report_data.get('content_recommendations', [])[:3]:
        markdown += f"""
        ### 우선순위 {rec.get('priority', 0)} - {rec.get('content_type', '').upper()}
        - **개선된 제목**: {rec.get('title', '')}
        - **설명**: {rec.get('description', '')}
        - **목표 지표**: {rec.get('target_metric', '')}
        - **예상 개선율**: {rec.get('expected_improvement', '')}
        - **예상 ROI**: {rec.get('estimated_roi', 0):.1f}
        """
        
    # 액션 아이템
    markdown += """

    ---

    ## 📌 우선순위 액션 아이템

    | 우선순위 | 액션 | 기한 | 성공 지표 |
    |----------|------|------|-----------|
    """
        
    for action in report_data.get('action_items', [])[:5]:
        priority_emoji = {
            "critical": "🔴", "high": "🟠", 
            "medium": "🟡", "low": "🟢"
        }
        markdown += f"| {priority_emoji.get(action.get('priority', ''), '')} {action.get('priority', '')} | {action.get('action', '')} | {action.get('timeline', '')} | {action.get('success_metric', '')} |\n"
    
    markdown += """

    ---

    > 💡 **다음 단계**: 위 분석 결과를 바탕으로 콘텐츠 전략을 수정하고, 7일 후 성과를 재측정하세요.
    """
    
    return markdown



def get_score_label(score: float) -> str:
    """점수를 라벨로 변환"""
    if score >= 80:
        return "🟢 우수"
    
    elif score >= 60:
        return "🟡 양호"
    
    elif score >= 40:
        return "🟠 보통"
    
    else:
        return "🔴 개선필요"
