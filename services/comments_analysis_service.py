import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from nodes.comments_analyzer.emotion_analyzer import analyze_emotions_batch


def analyze_comments(comment_objects: List) -> Dict:
    texts = [comment.content for comment in comment_objects]
    ids = [comment.id for comment in comment_objects]

    result = analyze_emotions_batch(texts, ids)

    return result
