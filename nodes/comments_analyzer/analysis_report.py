from config.settings import settings
import os
import re
import anthropic
from typing import Dict, Optional, Any
import json
from schemas.report_analysis_schema import PostAnalysisRequest

class AnalysisReport:
    def generate_analysis_report(self, analysis_data: PostAnalysisRequest) -> Dict[str, Any]:
        """게시글 성과 분석 리포트"""

        client = anthropic.Anthropic(api_key = settings.claude_api_key)

        system_prompt = """
        You are an elite SNS marketing analyst with 15+ years of experience in digital marketing, data science, and consumer psychology. 
        You specialize in: 

        1. Quantitative Analysis: Statistical modeling, engagement metrics, conversion optimization
        2. Qualitative Insights: Sentiment analysis, behavioral patterns, cultural trends
        3. Strategic Planning: Growth hacking, content strategy, viral marketing mechanics
        4. Industry Expertise: Deep knowledge across B2C/B2B, e-commerce, retail, SaaS, F&B sectors

        Your analysis methodology combines:
        - Harvard Business School frameworks (SWOT, Porter's Five Forces)
        - Silicon Valley growth metrics (CAC, LTV, K-factor)
        - Behavioral economics principles (loss aversion, social proof, scarcity)
        - Platform-specific algorithms (Instagram Reels, Facebook EdgeRank, YouTube retention)

        You provide actionable insights that directly impact ROI, with specific KPIs and success metrics.

        Always respond in structured and valid JSON format with precise data types.
        """

        total_comments = analysis_data.metrics.comment_count if analysis_data.metrics.comment_count > 0 else 1

        prompt = f"""
        Analyze the following SNS post performance data with academic rigor and practical applicability.
        
        POST CONTENT
        - Title: {analysis_data.title}
        - Content: {analysis_data.description}
        - Content Length: {len(analysis_data.description)} characters
        - Hashtags Used: {', '.join(analysis_data.tags) if analysis_data.tags else 'None'}
        - Posted Date: {analysis_data.publish_at}

        POST METRICS
        - Platform: YouTube
        - View Count: {analysis_data.metrics.view_count:,} views
        - Like Count: {analysis_data.metrics.like_count:,} likes
        - Comments Count: {analysis_data.metrics.comment_count:,} comments


        SENTIMENT ANALYSIS
        - Total Comments Count: {analysis_data.metrics.comment_count:,} comments
        - Positive Comments Count: {analysis_data.emotion_data.positive_count:,} comments ({((analysis_data.emotion_data.positive_count / total_comments) * 100):.1f}%)
        - Negative Comments Count: {analysis_data.emotion_data.negative_count:,} comments ({((analysis_data.emotion_data.negative_count / total_comments) * 100):.1f}%)
        - Neutral Comments Count: {analysis_data.emotion_data.neutral_count:,} comments ({((analysis_data.emotion_data.neutral_count / total_comments) * 100):.1f}%)
        - Positive Keywords: {', '.join(analysis_data.emotion_data.positive_keywords[:12])}
        - Negative Keywords: {', '.join(analysis_data.emotion_data.negative_keywords[:12])}
        - Neutral Keywords: {', '.join(analysis_data.emotion_data.neutral_keywords[:12])}


        BUSINESS CONTEXT
        - Industry: {analysis_data.industry}

        
        CONTENT-PERFORMANCE CORRELATION ANALYSIS REQUIRED:
        1. Analyze how the title effectiveness impacts view count
        2. Identify which content elements drove positive/negative reactions
        3. Evaluate message-market fit based on the content and audience response
        4. Assess if the content tone aligns with the brand and platform

        Provide comprehensive analysis following this EXACT JSON structure:

        ```json
        {{
            "performance_score": <float between 0-100, 1 decimal>,
            "performance_grade": <"S"|"A"|"B"|"C"|"D">,
            
            "content_effectiveness": {{
                "title_impact_score": <float 0-100, how well title drove views>,
                "content_engagement_score": <float 0-100, how well content drove engagement>,
                "message_clarity": <"excellent"|"good"|"fair"|"poor">,
                "cta_effectiveness": <"strong"|"moderate"|"weak"|"absent">,
                "content_sentiment_alignment": <float, correlation between content tone and comment sentiment>,
                "viral_elements_present": [<list of viral elements found in content>],
                "improvement_areas": [<specific content improvements needed>]
            }},
            
            "detailed_analysis": {{
                "engagement_metrics": {{
                    "engagement_rate": <float>,
                    "like_to_view_ratio": <float>,
                    "comment_to_like_ratio": <float>,
                    "virality_coefficient": <float>,
                    "estimated_reach_multiplier": <float>
                }},
                "sentiment_analysis": {{
                    "sentiment_score": <float 0-100>,
                    "controversy_index": <float 0-100>,
                    "emotional_intensity": <"high"|"medium"|"low">,
                    "discussion_quality": <"constructive"|"mixed"|"toxic">,
                    "content_triggered_emotions": [<list of emotions the content triggered based on comments>]
                }},
                "swot_analysis": {{
                    "strengths": [<3-5 specific points including content strengths>],
                    "weaknesses": [<3-5 specific points including content weaknesses>],
                    "opportunities": [<3-5 specific points based on content performance>],
                    "threats": [<3-5 specific points>]
                }},
                "competitive_position": {{
                    "market_position": <"leader"|"challenger"|"follower"|"nicher">,
                    "differentiation_score": <float 0-100>,
                    "brand_perception": <string based on content and reactions>,
                    "content_uniqueness": <float 0-100>
                }}
            }},
        
            "insights": [
                {{
                    "type": <"pattern"|"anomaly"|"trend"|"correlation">,
                    "finding": <string, must reference specific content elements>,
                    "confidence": <"high"|"medium"|"low">,
                    "business_impact": <string>,
                    "statistical_significance": <float>
                }}
            ],
            
            "content_recommendations": [
                {{
                    "priority": <1-10>,
                    "content_type": <"reel"|"carousel"|"story"|"live"|"post">,
                    "title": <improved title based on current performance>,
                    "description": <specific content improvements based on analysis>,
                    "target_metric": <string>,
                    "expected_improvement": <percentage>,
                    "production_effort": <"low"|"medium"|"high">,
                    "estimated_roi": <float>,
                    "content_elements_to_retain": [<successful elements from current content>],
                    "content_elements_to_change": [<elements that need improvement>]
                }}
            ],
            
            "strategy": {{
                "immediate_24h": {{
                    "actions": [<list including content optimization actions>],
                    "expected_outcome": <string>,
                    "resources_needed": <string>
                }},
                "short_term_7d": {{
                    "actions": [<list>],
                    "kpi_targets": {{<metric:target pairs>}},
                    "budget_allocation": <string>
                }},
                "medium_term_30d": {{
                    "content_calendar": [<weekly themes based on successful content elements>],
                    "growth_tactics": [<specific tactics>],
                    "testing_framework": {{
                        "hypothesis": <string about content performance>,
                        "variables": [<list of content variables to test>],
                        "success_criteria": <string>
                    }}
                }},
                "long_term_90d": {{
                    "strategic_objectives": [<list>],
                    "milestone_metrics": {{<metric:target pairs>}},
                    "pivot_indicators": [<list>],
                    "content_evolution_roadmap": [<how content should evolve>]
                }}
            }},
            
            "action_items": [
                {{
                    "priority": <"critical"|"high"|"medium"|"low">,
                    "timeline": <"immediate"|"24h"|"7d"|"30d">,
                    "action": <string, specific content-related action>,
                    "owner": <string>,
                    "success_metric": <string>,
                    "dependencies": [<list>]
                }}
            ]
        }}
        """
        

        try:
            response = client.messages.create(
                model = "claude-sonnet-4-20250514",
                max_tokens = 4500,
                temperature = 0.3,
                system = system_prompt,
                messages = [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            result = self.parse_response(response.content[0].text.strip())
            

            report_data = {
                "performance_score": result.get("performance_score", 0),
                "performance_grade": result.get("performance_grade", "N/A"),
                "content_effectiveness": result.get("content_effectiveness", {}),
                "detailed_analysis": result.get("detailed_analysis", {}),
                "insights": result.get("insights", []),
                "content_recommendations": result.get("content_recommendations", []),
                "strategy": result.get("strategy", {}),
                "action_items": result.get("action_items", []),
            }

            return report_data
            
        except Exception as e:
            raise Exception(f"성과 분석 실패: {e}")



    def parse_response(self, text: str) -> Dict:
        try:
            json_match = re.search(r'```json\n(.*?)\n```', text, re.DOTALL)
            
            if json_match:
                return json.loads(json_match.group(1))
            
            # 파싱
            return json.loads(text)
            
        except json.JSONDecodeError:
            raise Exception("JSON 파싱 실패")
