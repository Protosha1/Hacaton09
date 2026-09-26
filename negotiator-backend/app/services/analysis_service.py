# app/services/analysis_service.py
import json
import re

import httpx
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Literal

from app.core.config import settings
from app.services.retry import retry_async


class TranscriptAnnotationModel(BaseModel):
    index: int
    original: str
    type: Literal["strong", "neutral", "weak"]
    category: str = "other"
    why: str = ""
    suggestion: Optional[str] = None


class AnalysisResultModel(BaseModel):
    goal_achieved: Literal["yes", "no", "partial"] = "no"
    argumentation_score: int = Field(default=0, ge=0, le=100)
    objection_handling_score: int = Field(default=0, ge=0, le=100)
    overall_score: int = Field(default=0, ge=0, le=100)
    spin_score: int = Field(default=0, ge=0, le=100)
    batna_score: int = Field(default=0, ge=0, le=100)
    emotion_control_score: int = Field(default=0, ge=0, le=100)
    spin_analysis: Optional[str] = None
    batna_analysis: Optional[str] = None
    transcript_annotations: List[TranscriptAnnotationModel] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    full_report: str = ""


class AnalysisService:
    """
    Analyzes a completed negotiation session using an LLM.
    Returns a structured report with scores, text blocks, and annotations.
    """

    DEFAULT_MODEL = "qwen3.6-plus"

    SYSTEM_PROMPT = (
        "You are an expert business negotiation coach. "
        "Analyze the completed negotiation and return STRICT JSON.\n"
        "\n"
        "Return ONLY valid JSON (no markdown, no code fences) in this exact format:\n"
        "\n"
        "{\n"
        '  "goal_achieved": "yes" | "no" | "partial",\n'
        '  "argumentation_score": 0-100,\n'
        '  "objection_handling_score": 0-100,\n'
        '  "overall_score": 0-100,\n'
        '  "spin_score": 0-100,\n'
        '  "batna_score": 0-100,\n'
        '  "emotion_control_score": 0-100,\n'
        '  "spin_analysis": "2-4 sentences analyzing how the user applied SPIN (Situation, Problem, Implication, Need-payoff questions).",\n'
        '  "batna_analysis": "2-4 sentences analyzing the user\'s BATNA awareness and use of the Harvard method (interests over positions, objective criteria).",\n'
        '  "transcript_annotations": [\n'
        "    {\n"
        '      "index": 0,\n'
        '      "original": "Exact text the user said, copied verbatim from the dialogue.",\n'
        '      "type": "strong" | "neutral" | "weak",\n'
        '      "category": "opening" | "question" | "argument" | "concession" | "objection_handling" | "emotional" | "directive" | "other",\n'
        '      "why": "One sentence explaining why this is rated strong/neutral/weak.",\n'
        '      "suggestion": "A stronger alternative phrasing, or null if type is \'strong\'."\n'
        "    }\n"
        "  ],\n"
        '  "strengths": ["...", "...", "..."],\n'
        '  "weaknesses": ["...", "...", "..."],\n'
        '  "suggestions": ["...", "...", "..."],\n'
        '  "full_report": "A short paragraph (3-5 sentences)."\n'
        "}\n"
        "\n"
        "Rules for transcript_annotations:\n"
        "- index refers to the position of the USER message in the dialogue (0 = first user message, 1 = second, etc.)\n"
        "- Only annotate USER messages, never the opponent's.\n"
        "- Copy 'original' verbatim - do not paraphrase.\n"
        "- 'suggestion' MUST be null when type is 'strong'.\n"
        "- Include an entry for every user message, up to a maximum of 20.\n"
        "\n"
        "Scoring criteria:\n"
        "- argumentation_score: quality of justification, use of data, value framing.\n"
        "- objection_handling_score: response to pushback, staying calm, countering.\n"
        "- spin_score: use of SPIN methodology.\n"
        "- batna_score: awareness and use of BATNA; Harvard method (interests over positions).\n"
        "- emotion_control_score: managing own emotions, staying professional under pressure.\n"
        "- overall_score: weighted average plus goal achievement.\n"
        "\n"
        "Rules:\n"
        "- Be honest and constructive.\n"
        "- Reference specific moments from the dialogue.\n"
        "- Keep each item in strengths/weaknesses/suggestions concise (1 sentence).\n"
        "- full_report: 3-5 sentences.\n"
        "- The dialogue may be in Russian, English, or mixed. Analyze regardless of language.\n"
        "- Write the response fields (strengths, weaknesses, suggestions, full_report, spin_analysis, batna_analysis, why, suggestion) in the same language as the majority of the dialogue.\n"
        "- Return ONLY valid JSON.\n"
    )

    @staticmethod
    async def analyze_session(session_data: dict, messages: list[dict]) -> dict:
        dialogue_lines = []
        for m in messages:
            who = "USER" if m["sender"] == "user" else "OPPONENT"
            dialogue_lines.append(f"{who}: {m['text']}")
        dialogue_text = "\n".join(dialogue_lines)

        user_prompt = (
            "NEGOTIATION CONTEXT:\n"
            f"- User role: {session_data.get('role')}\n"
            f"- User goal: {session_data.get('goal')}\n"
            f"- Opponent role: {session_data.get('opponent')}\n"
            f"- Opponent goal: {session_data.get('opponent_goal', 'unknown')}\n"
            "\n"
            "DIALOGUE:\n"
            f"{dialogue_text}\n"
            "\n"
            "Now analyze the user's performance and return the JSON report.\n"
        )

        async def _call() -> httpx.Response:
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
                    },
                )
                if 500 <= response.status_code < 600:
                    raise httpx.HTTPStatusError(
                        f"server error {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                return response

        try:
            response = await retry_async(_call, label="LLM analysis")
        except httpx.HTTPError as e:
            raise Exception(f"LLM analysis failed after retries: {e}")

        if response.status_code != 200:
            raise Exception(f"LLM error: {response.status_code} - {response.text[:500]}")

        raw = response.json()["choices"][0]["message"]["content"]
        parsed = AnalysisService._parse_json(raw)
        return parsed

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """Extract JSON from LLM output even if wrapped in code fences, then validate."""
        cleaned = re.sub(
            r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE
        )
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                raise
            data = json.loads(match.group(0))

        try:
            model = AnalysisResultModel.model_validate(data)
        except ValidationError as e:
            raise Exception(f"LLM returned malformed analysis JSON: {e}")

        return model.model_dump()