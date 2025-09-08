from typing import List, Dict, Any, Optional
from cog import BasePredictor, Input
import re, json, emoji
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TextClassificationPipeline
from soynlp.normalizer import repeat_normalize
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer

CACHE_DIR = 'weights'

class Predictor(BasePredictor):
    def setup(self) -> None:
        # 모델 로드
        self.sentiment_tokenizer = AutoTokenizer.from_pretrained("Copycats/koelectra-base-v3-generalized-sentiment-analysis", cache_dir = CACHE_DIR, local_files_only = True)
        self.sentiment_model = AutoModelForSequenceClassification.from_pretrained("Copycats/koelectra-base-v3-generalized-sentiment-analysis", cache_dir = CACHE_DIR, local_files_only = True)
        self.sentiment_classifier = TextClassificationPipeline(
            tokenizer = self.sentiment_tokenizer, model = self.sentiment_model
        )
        
        self.sentence_model = SentenceTransformer("jhgan/ko-sroberta-multitask", cache_folder = CACHE_DIR)
        self.keybert_model = KeyBERT(model = self.sentence_model)

 

    def clean_text(self, text: str) -> str:
        pattern = re.compile(r'[^ .,?!/@$%~％·∼()\x00-\x7Fㄱ-ㅣ가-힣]+')
        url_pattern = re.compile(r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)')
        
        text = pattern.sub(' ', text)
        text = emoji.replace_emoji(text, replace='')
        text = url_pattern.sub('', text)
        text = text.strip()
        text = repeat_normalize(text, num_repeats=2)
        
        return text



    def extract_keywords(self, texts: List[str], top_n: int = 10) -> List[str]:
        all_keywords = {}

        for text in texts:
            cleaned_text = self.clean_text(text)

            keywords = self.keybert_model.extract_keywords(
                cleaned_text,
                keyphrase_ngram_range = (1, 1),
                stop_words = None,
                top_n = 5,
                use_mmr = True,
                diversity = 0.5
            )

            for kw, score in keywords:
                if kw in all_keywords:
                    all_keywords[kw] = max(all_keywords[kw], score)
                
                else:
                    all_keywords[kw] = score
        
        sorted_keywords = sorted(all_keywords.items(), key = lambda x: x[1], reverse = True)

        return sorted_keywords[:top_n]



    def predict(self,
        texts: List[str] = Input(description = "분석 텍스트 리스트"),
        ids: Optional[List[int]] = Input(default = None, description = "각 텍스트 ID 리스트")
    ) -> Dict[str, Any]:
        """텍스트 배치 감정 분석"""

        threshold = 0.7

        if ids is None:
            ids = list(range(1, len(texts) + 1))

        results = []
        positive_comments = []
        negative_comments = []
        neutral_comments = []
        
        batch_size = 16

        print(f"입력받은 텍스트 리스트 길이: {len(texts)}")
        print(f"텍스트 리스트: {texts}")
        print()

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            
            for j, (text, text_id) in enumerate(zip(batch_texts, batch_ids)):
                predicted_class = self.sentiment_classifier(self.clean_text(text))
                            
                # 부정(NEGATIVE)/긍정(POSITIVE)/중립(NEUTRAL) 처리
                if int(predicted_class[0].get('label')) == 0 and predicted_class[0].get('score') > threshold:
                    result = 'NEGATIVE'
                    negative_comments.append(text)

                elif int(predicted_class[0].get('label')) == 1 and predicted_class[0].get('score') > threshold:
                    result = 'POSITIVE'
                    positive_comments.append(text)

                else:
                    result = 'NEUTRAL'
                    neutral_comments.append(text)

                print(f"text_id: {text_id} \ntext: {text}\nresult: {result}\n")

                results.append({
                    'id': text_id,
                    'result': result
                })
        
        positive_keywords = self.extract_keywords(positive_comments, top_n = 10) if positive_comments else []
        negative_keywords = self.extract_keywords(negative_comments, top_n = 10) if negative_comments else []
        neutral_keywords = self.extract_keywords(neutral_comments, top_n = 10) if neutral_comments else []

        return {
            "individual_results": results,
            "keywords": {
                "positive": [kw for kw, score in positive_keywords if score > 0.7],
                "negative": [kw for kw, score in negative_keywords if score > 0.7],
                "neutral": [kw for kw, _ in neutral_keywords]
            }
        }
