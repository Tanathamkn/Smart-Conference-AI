import os
from faster_whisper import WhisperModel

# 'large-v3' is strongly recommended for Thai-English mixed audio.
# 'base' can be used to save memory but will have poor Thai accuracy.
# Override via WHISPER_MODEL_SIZE environment variable in docker-compose.yml.
MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "large-v3")

try:
    # Set device to 'cuda' if GPU is available, else 'cpu'
    # compute_type="int8" is good for reducing memory usage
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
except Exception as e:
    print(f"Failed to load whisper model: {e}")
    model = None

def transcribe_audio(file_path: str):
    """
    Transcribes the audio file at the given path and returns segments.
    Explicitly targets Thai and English to prevent misdetection (e.g., as Russian).
    Each segment contains start, end, and text.
    """
    if model is None:
        return [{"start": 0.0, "end": 1.0, "text": "[Whisper Model Failed to Load]"}], "[Whisper Model Failed to Load]"

    segments, info = model.transcribe(
        file_path,
        beam_size=5,
        # Explicitly set language to Thai. Whisper will still handle English words
        # naturally in a mixed Thai-English conversation.
        language="th",
        # Voice Activity Detection filter reduces hallucinations on silent segments
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    transcribed_segments = []
    full_text = []

    for segment in segments:
        transcribed_segments.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
            "speaker": "Unknown"  # Speaker diarization requires Pyannote, leaving as Unknown for now
        })
        full_text.append(segment.text.strip())

    return transcribed_segments, " ".join(full_text)
