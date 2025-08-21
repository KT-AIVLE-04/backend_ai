import subprocess
import sys
import re
import json
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TextClassificationPipeline
import emoji
from soynlp.normalizer import repeat_normalize
from typing import List, Dict
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer


sentiment_tokenizer = None
sentiment_model = None
sentiment_classifier = None

keybert_model = None


def get_sentiment_classifier():
    """감정 분석 모델 캐싱"""
    global sentiment_tokenizer, sentiment_model, sentiment_classifier
    
    if sentiment_classifier is None:
        print("감정 분석 모델 로딩 중...")
        
        sentiment_tokenizer = AutoTokenizer.from_pretrained("Copycats/koelectra-base-v3-generalized-sentiment-analysis")
        sentiment_model = AutoModelForSequenceClassification.from_pretrained("Copycats/koelectra-base-v3-generalized-sentiment-analysis")
        sentiment_classifier = TextClassificationPipeline(tokenizer = sentiment_tokenizer, model = sentiment_model)
        
        print("감정 분석 모델 로딩 완료\n")
    
    return sentiment_classifier


def get_keybert_model():
    """KeyBERT 모델 캐싱"""
    global keybert_model
    
    if keybert_model is None:
        print("KeyBERT 모델 로딩 중...")

        sentence_model = SentenceTransformer("jhgan/ko-sroberta-multitask")
        keybert_model = KeyBERT(model = sentence_model)
        
        print("KeyBERT 모델 로딩 완료\n")
    
    return keybert_model


def clean_text(text: str) -> str:
    """댓글 텍스트 전처리"""
    # 출처: https://huggingface.co/beomi/KcELECTRA-base-v2022

    pattern = re.compile(f'[^ .,?!/@$%~％·∼()\x00-\x7Fㄱ-ㅣ가-힣]+')
    url_pattern = re.compile(r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)')

    text = pattern.sub(' ', text)
    text = emoji.replace_emoji(text, replace = '')
    text = url_pattern.sub('', text)
    text = text.strip()
    text = repeat_normalize(text, num_repeats = 2)
    
    return text



def extract_keywords(texts: List[str], top_n: int = 10) -> List[str]:
    """텍스트에서 주요 키워드 추출"""

    kw_model = get_keybert_model()

    all_keywords = {}

    for text in texts:
        cleaned_text = clean_text(text)

        keywords = kw_model.extract_keywords(
            cleaned_text,
            keyphrase_ngram_range = (1, 2),
            stop_words = None,
            top_n = 5,
            use_mmr = True,
            diversity = 0.3
        )

        for kw, score in keywords:
                if kw in all_keywords:
                    all_keywords[kw] = max(all_keywords[kw], score)  # Max score value 사용
                
                else:
                    all_keywords[kw] = score
    
    sorted_keywords = sorted(all_keywords.items(), key = lambda x: x[1], reverse = True)

    return sorted_keywords[:top_n]



def analyze_emotions_batch(texts: List[str], ids: List[int] = None) -> List[Dict]:
    """텍스트 배치 감정 분석"""
    
    thresh = 0.7

    # 모델 로드
    sentiment_classifier = get_sentiment_classifier()
    
    if ids is None:
        ids = list(range(1, len(texts) + 1))
    
    results = []
    positive_comments = []
    negative_comments = []
    
    # 배치 처리
    batch_size = 16

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_ids = ids[i:i + batch_size]
        
        for j, (text, text_id) in enumerate(zip(batch_texts, batch_ids)):
            predicted_class = sentiment_classifier(clean_text(text))
                        
            # 부정(NEGATIVE)/긍정(POSITIVE)/중립(NEUTRAL) 처리
            if int(predicted_class[0].get('label')) == 0 and predicted_class[0].get('score') > thresh:
                result = 'NEGATIVE'
                negative_comments.append(text)

            elif int(predicted_class[0].get('label')) == 1 and predicted_class[0].get('score') > thresh:
                result = 'POSITIVE'
                positive_comments.append(text)

            else:
                result = 'NEUTRAL'


            results.append({
                'id': text_id,
                'result': result
            })
    
    positive_keywords = extract_keywords(positive_comments, top_n = 10) if positive_comments else []
    negative_keywords = extract_keywords(negative_comments, top_n = 10) if negative_comments else []

    # commands = [
    #         "rm -rf ~/.cache/huggingface/hub",
    #         "rm -rf ~/.cache/huggingface/datasets"
    # ]

    # for cmd in commands:
    #     try:
    #         subprocess.run(cmd, shell = True, check = True)
    #         print(f"BERT 모델 cache 삭제: {cmd}")
            
    #     except subprocess.CalledProcessError as e:
    #         print(f"BERT 모델 cache 삭제 실패: {cmd} - {e}")

    return {
        'individual_results': results,
        'keywords': {
            'positive': [kw for kw, score in positive_keywords if score > 0.7],
            'negative': [kw for kw, score in negative_keywords if score > 0.7]
        }
    }
