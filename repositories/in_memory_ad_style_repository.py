from typing import List
from repositories.ad_style_repository import AdStyleRepository

# 임시 구현 -> 추후에 업종별 광고 스타일 트렌드 가져오는 방식 변경하면 수정 예정
class InMemoryAdStyleRepository(AdStyleRepository):
    def __init__(self):
        self._data = {
  "음식점": [
    "푸드 포르노(음식의 비주얼 극대화, 클로즈업 촬영)",
    "메이킹 영상(조리 과정, 재료 손질, 완성 과정 강조)",
    "고객 체험 및 리뷰 숏폼(짧은 실제 후기 영상)"
  ],
  "카페": [
    "제품 제조·제공 과정 숏폼(커피, 음료, 디저트 만드는 실제 모습)",
    "고객 체험·시음 후기 영상",
    "매장 인테리어·분위기 클로즈업(직접 촬영 가능)"
  ],
  "패션": [
    "비포 앤 애프터 스타일링 숏폼(착용 전후 비교)",
    "모델 워킹 및 착용 영상(실제 모델 촬영 또는 이미지 활용)",
    "실제 소비자·인플루언서 착용 리뷰 숏폼"
  ],
  "뷰티": [
    "제품 사용법 데모(실제 사용 장면·손에 바르는 모습을 짧게 촬영)",
    "사용 전후 변화 비교(사진·영상 활용, 효과 강조)",
    "성분·기능 설명(제품 주요 특징을 간략 비주얼로 제시)"
  ],
  "테크": [
    "제품 핵심 기능·강점 데모 숏폼(직접 사용, 버튼 클릭, UI·UX 강조)",
    "실사용자 또는 전문가 리뷰 숏폼(단편 피드백, 추천 영상)",
    "비교·성능 테스트 숏폼(경쟁 제품과 직접 비교, 속도·결과 등 강조)"
  ]
}

    def get_top3_ad_styles_by_business_type(self, business_type: str) -> List[str]:
 
        if business_type not in self._data.keys():
            raise ValueError("잘못된 업종입니다.")

        return self._data.get(business_type, [])