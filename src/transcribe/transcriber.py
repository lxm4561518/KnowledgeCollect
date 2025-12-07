from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self, model_size: str = "small"):
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio_path: str) -> str:
        try:
            segments, _ = self.model.transcribe(audio_path, vad_filter=True)
        except TypeError:
             # Fallback for older versions if needed, or newer?
             # Actually if vad=True failed, vad_filter might work.
             # Or maybe just remove it if default is fine.
             segments, _ = self.model.transcribe(audio_path)
             
        parts = []
        for seg in segments:
            parts.append(seg.text)
        return "\n".join(parts)
