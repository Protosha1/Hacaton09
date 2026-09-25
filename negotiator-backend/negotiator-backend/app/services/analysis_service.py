# app/services/analysis_service.py
import json
import re
import httpx
from app.core.config import settings


class AnalysisService:
    """
    Analyzes a completed negotiation session using an LLM.
    Returns a structured report with scores and suggestions.
    """

    DEFAULT_MODEL = "qwen3.6-plus"

    SYSTEM_PROMPT = """
You are an expert business negotiation coach. Analyze the completed negotiation and return STRICT JSON.

Return ONLY valid JSON (no markdown, no code fences) in this exact format:

{
  "goal_achieved": "yes" | "no" | "partial",
  "argumentation_score": 0-100,
  "objection_handling_score": 0-100,
  "overall_score": 0-100,
  "spin_score": 0-100,
  "batna_score": 0-100,
  "emotion_control_score": 0-100,
  "strengths": ["...", "...", "..."],
  "weaknesses": ["...", "...", "..."],
  "suggestions": ["...", "...", "..."],
  "full_report": "A short paragraph (3-5 sentences)."
}

Scoring criteria:
- argumentation_score: quality of justification, use of data, value framing.
- objection_handling_score: response to pushback, staying calm, countering.
- spin_score: use of SPIN methodology (Situation, Problem, Implication, Need-payoff questions).
- batna_score: awareness and use of BATNA (Best Alternative to Negotiated Agreement); knowing when to walk away; Harvard method (interests over positions).
- emotion_control_score: managing own emotions, staying professional under pressure, avoiding reactive replies.
- overall_score: weighted average of the above plus goal achievement.

Rules:
- Be honest and constructive.
- Reference specific moments from the dialogue.
- Keep each item in strengths/weaknesses/suggestions concise (1 sentence).
- full_report: 3-5 sentences.
- The dialogue may be in Russian, English, or mixed. Analyze regardless of language.
- Write the response fields (strengths, weaknesses, suggestions, full_report) in the same language as the majority of the dialogue.
- Return ONLY valid JSON.
"""

    @staticmethod
    async def analyze_session(
        session_data: dict,
        messages: list[dict]
    ) -> dict:
        """
        session_data: {role, goal, opponent, opponent_goal}
        messages: [{"sender": "user"|"ai", "text": "..."}]
        Returns: parsed JSON report
        """

        # Build the dialogue as plain text
        dialogue_lines = []
        for m in messages:
            who = "USER" if m["sender"] == "user" else "OPPONENT"
            dialogue_lines.append(f"{who}: {m['text']}")
        dialogue_text = "\n".join(dialogue_lines)

        user_prompt = f"""
NEGOTIATION CONTEXT:
- User role: {session_data.get('role')}
- User goal: {session_data.get('goal')}
- Opponent role: {session_data.get('opponent')}
- Opponent goal: {session_data.get('opponent_goal', 'unknown')}

DIALOGUE:
{dialogue_text}

Now analyze the user's performance and return the JSON report.
"""

        # Call Qwen
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{settings.LLM_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": AnalysisService.DEFAULT_MODEL,
                    "messages": [
                        {"role": "system", "content": AnalysisService.SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                }
            )

        if response.status_code != 200:
            raise Exception(f"LLM error: {response.status_code} - {response.text}")

        raw = response.json()["choices"][0]["message"]["content"]
        parsed = AnalysisService._parse_json(raw)
        return parsed

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """Extract JSON from LLM output even if wrapped in code fences."""
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise