import os
from typing import Optional


class AIService:
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "stub").lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # Lazy init for providers
        self._openai_client = None

    def _ensure_openai(self):
        if self._openai_client is not None:
            return
        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:
            raise RuntimeError(f"OpenAI SDK not available: {e}")
        self._openai_client = OpenAI(api_key=self.openai_api_key)

    def chat(self, prompt: str, lang: Optional[str] = None) -> str:
        # Normalize language
        lang = (lang or "RU").upper()
        context = None
        # Читаем флаг RAG динамически, чтобы можно было менять на лету (тесты/конфиг)
        if os.getenv("AI_USE_RAG", "0") == "1":
            try:
                from rag_service import rag_service  # lazy import to avoid cycles
                context = rag_service.get_context(prompt)
            except Exception:
                context = None

        if self.provider == "openai":
            try:
                self._ensure_openai()
                # Minimal chat completion
                user_content = f"[{lang}] {prompt}"
                if context:
                    user_content += f"\n\nКонтекст:\n{context}"

                completion = self._openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a travel assistant for Aqmola region. "
                                "Respond briefly in the requested language (RU/KZ/EN)."
                            ),
                        },
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.3,
                    max_tokens=300,
                )
                return completion.choices[0].message.content or ""
            except Exception as e:
                # Fallback to stub on failure
                return f"[stub-fallback] Получен запрос: '{prompt[:200]}'"

        # Default stub behavior
        base = (
            "Это заглушка AI-ассистента. "
            f"Я получил ваш запрос: '{prompt[:200]}'. "
            "Полная функциональность будет активна после настройки ключей."
        )
        if context:
            base += " Добавлен контекст RAG (заглушка)."
        return base


# Singleton-like accessor
ai_service = AIService()
