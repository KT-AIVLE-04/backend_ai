from config.settings import settings
import replicate
from typing import List, Dict, Any

# 출처: https://huggingface.co/Copycats/koelectra-base-v3-generalized-sentiment-analysis
# 출처: https://huggingface.co/jhgan/ko-sroberta-multitask

# Replicate 모델 주소: https://replicate.com/choiminji-020102/ko-comments-emotion-analyzer
def analyze_emotions_batch(texts: List[str], ids: List[int] = None) -> Dict[str, Any]:
    replicate_client = replicate.Client(api_token = settings.replicate_api_key)

    output = replicate_client.run(
        "choiminji-020102/ko-comments-emotion-analyzer:55f49ebbdc50dd9565906847fb96d0621a19e1122536df254d995d61437b0d1f",
        
        input = {
            "texts": texts,
            "ids": ids
        }
    )

    return output