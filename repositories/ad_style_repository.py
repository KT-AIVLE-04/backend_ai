from typing import List, Dict

#  업종별 광고 스타일 데이터 접근 인터페이스
class AdStyleRepository:
    def get_top3_ad_styles_by_business_type(self, business_type: str) -> List[str]:
        raise NotImplementedError
    