import os
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import tempfile
from faster_whisper import WhisperModel


class VoiceService:
    _model = None

    @classmethod
    def _get_model(cls) -> WhisperModel:
        if cls._model is None:
            # "base" — быстрая и лёгкая (~150 МБ), хорошо для русского
            # Можно поменять на "small" или "medium" для лучшего качества
            cls._model = WhisperModel(
                "medium",
                device="cpu",          # "cuda" если есть NVIDIA GPU
                compute_type="int8"    # "float16" для GPU, "int8" для CPU
            )
        return cls._model

    @staticmethod
    async def speech_to_text(audio_bytes: bytes, language: str = "ru") -> str:
        # Сохраняем аудио во временный файл
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            model = VoiceService._get_model()
            segments, _ = model.transcribe(
                tmp_path,
                language=language,
                beam_size=5,
                vad_filter=True  # убирает тишину, ускоряет работу
            )
            # Собираем все сегменты в один текст
            text = " ".join(seg.text.strip() for seg in segments).strip()
            print(f"[VOICE] Recognized: {text}")
            return text
        finally:
            # Удаляем временный файл в любом случае
            if os.path.exists(tmp_path):
                os.remove(tmp_path)