import httpx
from app.core.config import settings


class LLMService:
    DEFAULT_MODEL = "qwen3.6-plus"

    @staticmethod
    async def generate_response(prompt: str, context: dict = None) -> str:
        messages = []

        if context and context.get("system_prompt"):
            messages.append({
                "role": "system",
                "content": context["system_prompt"]
            })

        if context and context.get("history"):
            messages.extend(context["history"])

        messages.append({"role": "user", "content": prompt})

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
                }
            )

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            return f"⚠️ Qwen error: {response.status_code} - {response.text}"