from config.settings import settings
import replicate
from typing import List, Dict, Any

# 출처: https://huggingface.co/Copycats/koelectra-base-v3-generalized-sentiment-analysis
# 출처: https://huggingface.co/jhgan/ko-sroberta-multitask

def analyze_emotions_batch(texts: List[str], ids: List[int] = None) -> Dict[str, Any]:
    replicate_client = replicate.Client(api_token = settings.replicate_api_key)

    output = replicate_client.run(
        "choiminji-020102/ko-comments-emotion-analyzer:03ee810894a2120c443e65b7ec822dedbd72adcc40cc5109ddfee65de42da387",
        input = {
            "texts": texts,
            "ids": ids
        }
    )

    return output