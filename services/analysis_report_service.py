from typing import Dict, Any
from nodes.comments_analyzer.analysis_report import AnalysisReport
from nodes.comments_analyzer.generate_korean_md_report import generate_korean_markdown_report
from schemas.report_analysis_schema import PostAnalysisRequest, PostAnalysisResponse, PostAnalysisMarkdownReport


def generate_final_report(request: PostAnalysisRequest) -> PostAnalysisMarkdownReport:
    service = AnalysisReport()
          
    report_data, classified_industry = service.generate_analysis_report(request)

    print(f"보고서 생성 입력 데이터: {report_data}")
    
    analysis_response = PostAnalysisResponse(**report_data)

    markdown_report = generate_korean_markdown_report(analysis_response.dict(), classified_industry, request)
    
    return PostAnalysisMarkdownReport(markdown_report = markdown_report)
