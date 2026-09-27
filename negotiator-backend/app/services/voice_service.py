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
        import shutil
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            logger.info(f"ffmpeg found at: {ffmpeg_path}")
        else:
            # av==18 bundles its own ffmpeg libraries, so a missing system
            # ffmpeg binary usually isn't fatal — but it removes one layer
            # of fallback if the bundled decoder chokes on a particular
            # browser-produced webm/opus stream. Logging it so it's easy
            # to rule in/out later without guessing.
            logger.warning("System ffmpeg not found on PATH (av's bundled ffmpeg will still be used).")
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
            try:
                text = VoiceService._run_transcribe(model, tmp_path, language)
            except ValueError:
                raise
            except Exception as first_error:
                # Браузеры (особенно Chrome/MediaRecorder) отдают webm-блоб
                # без корректного duration/SeekHead — иногда это ломает
                # прямое декодирование внутри faster-whisper. Пробуем
                # перепаковать файл через av в чистый WAV и повторить —
                # это отдельный, более терпимый путь декодирования.
                logger.warning(
                    "Direct transcribe failed (%s: %s), retrying via WAV re-encode",
                    type(first_error).__name__, first_error,
                )
                wav_path = VoiceService._remux_to_wav(tmp_path)
                try:
                    text = VoiceService._run_transcribe(model, wav_path, language)
                finally:
                    if os.path.exists(wav_path):
                        os.remove(wav_path)

            if not text:
                raise ValueError("Could not recognize speech")
            logger.info(f"[VOICE] Recognized: {text[:100]}")
            return text
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @staticmethod
    def _run_transcribe(model: WhisperModel, path: str, language: str) -> str:
        segments, _ = model.transcribe(
            path,
            language=language,
            beam_size=5,
            vad_filter=True,
        )
        return " ".join(seg.text.strip() for seg in segments).strip()

    @staticmethod
    def _remux_to_wav(src_path: str) -> str:
        """Decode any container av can open and write out mono 16kHz PCM WAV.

        This is a more forgiving decode path than handing the raw browser
        blob straight to faster-whisper: av here reads frame-by-frame
        (tolerating a missing/broken duration header), resamples explicitly
        to the format the WAV encoder expects, and writes a plain,
        well-formed file that any downstream decoder handles fine.
        """
        import av

        def _as_list(frames_or_frame):
            # Different PyAV versions return either a list of frames or a
            # single frame/None from resample() — normalize to a list.
            if frames_or_frame is None:
                return []
            if isinstance(frames_or_frame, (list, tuple)):
                return list(frames_or_frame)
            return [frames_or_frame]

        fd, wav_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        input_container = av.open(src_path)
        try:
            in_stream = input_container.streams.audio[0]
            resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)

            output_container = av.open(wav_path, mode="w", format="wav")
            try:
                out_stream = output_container.add_stream("pcm_s16le", rate=16000)
                out_stream.layout = "mono"

                for frame in input_container.decode(in_stream):
                    for rframe in _as_list(resampler.resample(frame)):
                        for packet in out_stream.encode(rframe):
                            output_container.mux(packet)
                # Flush any samples buffered inside the resampler, then the encoder.
                for rframe in _as_list(resampler.resample(None)):
                    for packet in out_stream.encode(rframe):
                        output_container.mux(packet)
                for packet in out_stream.encode(None):
                    output_container.mux(packet)
            finally:
                output_container.close()
        finally:
            input_container.close()

        return wav_path