from app.config import settings

class AIAdapter:
    """Provider-neutral seam; no provider is contacted unless explicitly configured."""
    def explain(self, prompt: str) -> str:
        if not settings.ai_enabled or settings.ai_provider == "none":
            return ""
        raise RuntimeError("Configured AI providers are not implemented in this prototype.")
