import openai
from typing import List, Dict
import os
import time

class SentimentAnalyzer:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.model = "gpt-3.5-turbo"

    def analyze_sentiment(self, text: str) -> Dict:
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Analyze the sentiment of this comment and respond with only one word: POSITIVE, NEGATIVE, or NEUTRAL"},
                    {"role": "user", "content": text}
                ],
                temperature=0.3
            )
            sentiment = response.choices[0].message['content'].strip().upper()
            confidence = response.choices[0].finish_reason == "stop"
            return {"sentiment": sentiment, "confidence": 1.0 if confidence else 0.5}
        except Exception as e:
            return {"sentiment": "NEUTRAL", "confidence": 0.0}

    def batch_analyze(self, comments: List[Dict], batch_size: int = 20) -> List[Dict]:
        for i in range(0, len(comments), batch_size):
            batch = comments[i:i + batch_size]
            for comment in batch:
                result = self.analyze_sentiment(comment['text'])
                comment.update(result)
                time.sleep(0.5)  # Rate limiting
        return comments
