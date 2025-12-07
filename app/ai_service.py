import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        # Amazon Nova 2 Lite - новая быстрая модель с огромным контекстом (1M токенов)
        self.model = "amazon/nova-2-lite-v1:free"

    async def chat(self, prompt: str, lang: Optional[str] = None) -> str:
        """
        Отправляет запрос к OpenRouter API с моделью Amazon Nova
        """
        if not self.openrouter_api_key:
            logger.warning("No OpenRouter API key found, using fallback")
            return self._stub_response(prompt)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://visit-aqmola.kz",
                        "X-Title": "Visit Aqmola"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Ты - виртуальный туристический гид по Акмолинской области Казахстана. Помогай туристам с информацией о достопримечательностях, маршрутах, жилье и развлечениях. Основные достопримечательности: Национальный парк Бурабай (озера Боровое, Щучье), Кокшетау, гора Жеке-Батыр, скала Окжетпес. Отвечай на русском языке простым текстом БЕЗ markdown форматирования (без символов #, **, *, _, и т.д.). Используй только обычный текст с переносами строк."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text[:200]}")
                    return self._stub_response(prompt)
                
                data = response.json()
                
                if data.get("choices") and data["choices"][0].get("message"):
                    content = data["choices"][0]["message"]["content"]
                    return content
                
                logger.warning("No valid response in OpenRouter data")
                return self._stub_response(prompt)
                
        except Exception as e:
            logger.error(f"AI Service exception: {str(e)}")
            return self._stub_response(prompt)

    def _stub_response(self, prompt: str) -> str:
        """Fallback ответ если API недоступен"""
        if "бурабай" in prompt.lower():
            return "Национальный парк Бурабай - жемчужина Казахстана! Рекомендую посетить озёра Боровое и Щучье. Лучшее время для посещения - июнь-сентябрь."
        elif "кокшетау" in prompt.lower():
            return "Кокшетау - административный центр области. Здесь стоит посетить музей истории области и парк Победы."
        elif "жилье" in prompt.lower() or "отель" in prompt.lower():
            return "В области есть различные варианты жилья: санатории в Бурабае, отели в Кокшетау, гостевые дома."
        elif "маршрут" in prompt.lower():
            return "Рекомендованный маршрут: День 1 - Кокшетау; День 2-3 - Бурабай (озера Боровое и Щучье)."
        else:
            return "Я могу помочь с информацией о достопримечательностях Акмолинской области. Спросите о Бурабае, Кокшетау, маршрутах или жилье!"


# Singleton
ai_service = AIService()

