import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings

class AIAdapter:
    """Provider-neutral seam with an optional Gemini REST implementation."""

    def explain(self, prompt: str) -> str:
        if not settings.ai_enabled or settings.ai_provider == "none":
            return ""
        if not settings.ai_api_key:
            raise RuntimeError("AI is enabled but AI_API_KEY is not configured.")
        if settings.ai_provider.lower() != "gemini":
            raise RuntimeError(f"Unsupported AI provider: {settings.ai_provider}")

        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 160},
        }).encode("utf-8")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.ai_model}:generateContent?key={settings.ai_api_key}"
        )
        request = Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=settings.ai_timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as error:
            raise RuntimeError("Configured AI provider request failed.") from error

        candidates = body.get("candidates") or []
        parts = (candidates[0].get("content", {}).get("parts", []) if candidates else [])
        return " ".join(part.get("text", "").strip() for part in parts if part.get("text")).strip()
