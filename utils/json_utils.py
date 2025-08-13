# utils/json_utils.py
import json

def to_json_str(x) -> str:
    try:
        # pydantic 모델이면
        if hasattr(x, "model_dump_json"):
            return x.model_dump_json(ensure_ascii=False)
        # dict/list면
        if isinstance(x, (dict, list)):
            return json.dumps(x, ensure_ascii=False)
        # 이미 문자열이면
        if isinstance(x, str):
            return x
        # 그 외(예: TypedDict 등) 보수적 직렬화
        if hasattr(x, "model_dump"):
            return json.dumps(x.model_dump(), ensure_ascii=False)
        return json.dumps(x, ensure_ascii=False, default=str)
    except Exception:
        return str(x)