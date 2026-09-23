# app/services/llm_service.py
import httpx

from app.core.config import settings


class LLMError(Exception):
    """Raised when the LLM API returns a non-200 response or is unreachable."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"LLM error {status_code}: {message}")


class LLMService:
    DEFAULT_MODEL = "qwen3.6-plus"

    @staticmethod
    async def generate_response(prompt: str, context: dict = None) -> str:
        messages = []

        if context and context.get("system_prompt"):
            messages.append({
                "role": "system",
                "content": context["system_prompt"],
            })

        if context and context.get("history"):
            messages.extend(context["history"])

        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{settings.LLM_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": LLMService.DEFAULT_MODEL,
                        "messages": messages,
                    },
                )
        except httpx.HTTPError as e:
            raise LLMError(0, f"HTTP error: {e}")

        if response.status_code != 200:
            raise LLMError(response.status_code, response.text[:500])

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as e:
            raise LLMError(200, f"Malformed response: {e}")