# states/agent_state.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

from schemas.shorts_schema import InputImageInfo, Scene, Scenario

class ShortsState(BaseModel):
    # 초기에 필요한 필드들
    # 매장 정보
    store_name: str
    business_type: str

    # 브랜드 컨셉
    brand_concept: List[str]

    # 광고 정보
    platform: str
    ad_type: str
    target_audience: str
    
    # 사용자의 시나리오 요구사항
    scenario_prompt: str

    # 나중에 채워질 필드들
    image_list: List[InputImageInfo] = Field(default_factory = list)
    ad_duration: int = 15 # default
    scenarios: List[Scenario] = Field(default_factory = list)  # {"title", "content"}
    final_scenario: Optional[Scenario] = None  # {"title", "content"}
    
    # Seedance Prompt Generator에 필요한 입력 데이터
    scenes: List[Scene] = Field(default_factory = list)
    scenes_image_list: List[str] = Field(default_factory = list)
    scene_summary: str = ""
    
    # Seedance Prompt Generator
    seedance_results: List[Dict[str, Any]] = Field(default_factory = list, description = "Seedance 프롬프트 최종 결과 정보")
    seedance_validation: Optional[Dict[str, Any]] = Field(default = None, description = "Seedance 최종 검증 정보")

    # Seedance Video Generator
    video_urls: List[str] = Field(default_factory = list, description = "생성된 비디오 URL")
    video_files: List[str] = Field(default_factory = list, description = "다운로드 비디오 경로")
    output_dir: str = Field(default = "./videos", description = "다운로드 비디오 저장 폴더")
    final_video_path: Optional[str] = Field(default = None, description = "최종 비디오 (오디오X) 경로")

    # Generated Video Analysis
    video_analysis: Optional[Dict[str, Any]] = Field(default = None, description = "생성 비디오 분석 결과")
 
    # Suno(Music) Prompt Generator
    music_prompt: Optional[Dict[str, Any]] = Field(default = None, description = "음악 생성 프롬프트")
    music_alternatives: List[Dict[str, Any]] = Field(default_factory = list, description = "대체 프롬프트 2개")

    # Suno Music Generator
    music_urls: List[str] = Field(default_factory = list, description = "생성 음악 URL")
    music_files: List[str] = Field(default_factory = list, description = "음악 파일 경로")
    music_output_dir: str = Field(default = "./audio", description = "오디오 파일 저장 폴더")

    # Final Video With Audio
    final_video_audio_dir: str = Field(default = "./final", description = "최종 비디오(오디오 포함) 저장 폴더")
    final_video_audio_filename: str = Field(default = "final_video.mp4", description = "최종 비디오(오디오 포함) 파일명")
    final_video_audio_path: Optional[str] = Field(default = None, description = "최종 비디오(오디오 포함) 저장 경로")
