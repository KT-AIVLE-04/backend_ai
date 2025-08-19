# core/sns_post_graph.py
from langgraph.graph import StateGraph, START, END
from states.sns_post_state import SNSPostState
from nodes.sns_post.content_analyzer import content_analyzer
from nodes.sns_post.trend_analyzer import trend_analyzer
from nodes.sns_post.post_generator import post_generator
from nodes.sns_post.hashtag_generator import hashtag_generator
from typing import List, Optional, Any

def sns_post_workflow() -> Any:
    
    # StateGraph 생성
    workflow = StateGraph(SNSPostState)
    
    # 노드 추가
    workflow.add_node("content_analyzer", content_analyzer)
    workflow.add_node("trend_analyzer", trend_analyzer)
    workflow.add_node("post_generator", post_generator)
    workflow.add_node("hashtag_generator", hashtag_generator)
    
    # 엣지 연결 (순차 실행)
    workflow.add_edge(START, "content_analyzer")
    workflow.add_edge("content_analyzer", "trend_analyzer")
    workflow.add_edge("trend_analyzer", "post_generator")
    workflow.add_edge("post_generator", "hashtag_generator")
    workflow.add_edge("hashtag_generator", END)
    
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