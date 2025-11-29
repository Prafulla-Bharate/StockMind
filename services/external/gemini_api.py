import google.generativeai as genai
from django.conf import settings
import logging
from textblob import TextBlob
import asyncio
import aiohttp
import json
import time

logger = logging.getLogger(__name__)

class GeminiSentimentAnalyzer:
    """Sentiment analysis using Google Gemini API"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')


    def analyze_article(self, title, description):
        """Analyze sentiment of a news article (sync wrapper)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._analyze_article_async(title, description)
            )
        except Exception as e:
            logger.error(f"Error in analyze_article: {e}")
            return self._fallback_analysis(title, description)
    
    async def _analyze_article_async(self, title, description):
        """Async sentiment analysis with retries and JSON response"""

        # Strict, JSON-only prompt
        prompt = {
            "role": "user",
            "content": f"""
Analyze the following stock-related news and return ONLY a valid JSON.

Title: {title}
Description: {description}

Return JSON in this structure:
{{
  "sentiment": "positive/neutral/negative",
  "score": number between -1 and 1,
  "analysis": "2-3 sentence explanation"
}}

Output ONLY JSON. No extra text.
"""
        }

        retries = 3
        delay = 1

        for attempt in range(retries):
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt
                )

                raw_text = response.text.strip()

                # Try to load JSON
                result = json.loads(raw_text)
                return result

            except Exception as e:
                logger.warning(f"Gemini attempt {attempt+1} failed: {e}")
                if attempt == retries - 1:
                    return self._fallback_analysis(title, description)
                time.sleep(delay)
                delay *= 2  # exponential backoff
    
    
    def _fallback_analysis(self, title, description):
        """Fallback sentiment analysis using TextBlob"""
        text = f"{title} {description}"
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # Range: [-1, 1]
        
        if polarity > 0.1:
            sentiment = 'positive'
        elif polarity < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': polarity,
            'analysis': f"Sentiment evaluated using TextBlob fallback (polarity={polarity:.2f})."
        }
