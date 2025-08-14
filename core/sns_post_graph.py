# core/sns_post_graph.py
from langgraph.graph import StateGraph, START, END
from states.sns_post_state import SNSPostState
from nodes.sns_post.content_analyzer import analyze_content
from nodes.sns_post.trend_analyzer import analyze_trend
from nodes.sns_post.post_generator import generate_post
from nodes.sns_post.hashtag_generator import generate_hashtags
from typing import List, Optional, Any

def sns_post_workflow() -> Any:
    
    # StateGraph 생성
    workflow = StateGraph(SNSPostState)
    
    # 노드 추가
    workflow.add_node("analyze_content", analyze_content)
    workflow.add_node("analyze_trend", analyze_trend)
    workflow.add_node("generate_post", generate_post)
    workflow.add_node("generate_hashtags", generate_hashtags)
    
    # 엣지 연결 (순차 실행)
    workflow.add_edge(START, "analyze_content")
    workflow.add_edge("analyze_content", "analyze_trend")
    workflow.add_edge("analyze_trend", "generate_post")
    workflow.add_edge("generate_post", "generate_hashtags")
    workflow.add_edge("generate_hashtags", END)
    
    # 워크플로우 컴파일
    app = workflow.compile()
    
    return app


def run_sns_post_generation(
    content_data: str,
    user_keywords: List[str],
    sns_platform: str,
    business_type: str,
    location: Optional[str] = None
) -> SNSPostState:
    
    # 워크플로우 생성
    app = sns_post_workflow()
    
    # 초기 상태 생성
    initial_state = SNSPostState(
        content_data=content_data,
        sns_platform=sns_platform,
        business_type=business_type,
        user_keywords=user_keywords,
        location=location
    )
    
    # 워크플로우 실행
    try:
        print("[WORKFLOW] SNS 게시글 생성 워크플로우 시작")
        
        # 워크플로우 실행
        final_state_dict = app.invoke(initial_state)
        
        # AddableValuesDict를 SNSPostState로 변환
        final_state = SNSPostState(**final_state_dict)
        
        print("[WORKFLOW] 워크플로우 완료!")
        if final_state.generated_post:
            print(f"   - 제목: {final_state.generated_post.title}")
            print(f"   - 본문: {final_state.generated_post.content}")
            print(f"   - 해시태그: {final_state.hashtags}")
        
        return final_state
        
    except Exception as e:
        print(f"[WORKFLOW] 워크플로우 실행 오류: {e}")
        return initial_state