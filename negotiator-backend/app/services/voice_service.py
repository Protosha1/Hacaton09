# app/services/voice_service.py
import asyncio
import logging
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor

os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from faster_whisper import WhisperModel


logger = logging.getLogger(__name__)

MAX_AUDIO_BYTES = 10_000_000  # 10 MB


class VoiceService:
    _model = None
    _executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="whisper")

    @classmethod
    def _get_model(cls) -> WhisperModel:
        if cls._model is None:
            # "small" — fast (~500 MB), good enough for Russian/English.
            cls._model = WhisperModel(
                "small",
                device="cpu",
                compute_type="int8",
            )
        return cls._model

    @classmethod
    def warmup(cls) -> None:
        """Load model at startup. Call from FastAPI lifespan."""
        try:
            cls._get_model()
            logger.info("Whisper model loaded")
        except Exception as e:
            logger.warning(f"Whisper warmup failed: {e}")

    @staticmethod
    async def speech_to_text(audio_bytes: bytes, language: str = "ru") -> str:
        if not audio_bytes:
            raise ValueError("Empty audio")
        if len(audio_bytes) > MAX_AUDIO_BYTES:
            raise ValueError(
                f"Audio too large ({len(audio_bytes)} bytes, max {MAX_AUDIO_BYTES})"
            )

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            VoiceService._executor,
            VoiceService._transcribe_sync,
            audio_bytes,
            language,
        )

    @staticmethod
    def _transcribe_sync(audio_bytes: bytes, language: str) -> str:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            model = VoiceService._get_model()
            segments, _ = model.transcribe(
                tmp_path,
                language=language,
                beam_size=5,
                vad_filter=True,
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            if not text:
                raise ValueError("Could not recognize speech")
            logger.info(f"[VOICE] Recognized: {text[:100]}")
            return text
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)