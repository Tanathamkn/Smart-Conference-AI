import os
import torch
from faster_whisper import WhisperModel

try:
    from transformers import pipeline
except ImportError:
    pipeline = None

_faster_whisper_models = {}
_transformers_models = {}

def get_faster_whisper_model(model_size: str):
    if model_size not in _faster_whisper_models:
        try:
            print(f"Loading Faster Whisper model: {model_size}")
            # Set device to 'cuda' if GPU is available, else 'cpu'
            # compute_type="int8" is good for reducing memory usage
            _faster_whisper_models[model_size] = WhisperModel(model_size, device="cuda", compute_type="float16")
        except Exception as e:
            print(f"Failed to load Faster Whisper model {model_size}: {e}")
            return None
    return _faster_whisper_models[model_size]

def get_thonburian_model():
    if pipeline is None:
        print("Transformers library not installed. Cannot load Thonburian Whisper.")
        return None
    model_id = "biodatlab/whisper-th-medium-combined"
    if model_id not in _transformers_models:
        try:
            print(f"Loading Thonburian Whisper model: {model_id}")

            device = "cuda" if torch.cuda.is_available() else "cpu"

            torch_dtype = torch.float16 if device == "cuda" else torch.float32

            _transformers_models[model_id] = pipeline(
                "automatic-speech-recognition", 
                model=model_id,
                device=device,
                torch_dtype=torch_dtype,
                chunk_length_s=30
            )
            print(f"Thonburian Whisper model loaded successfully on [{device.upper()}]")
        except Exception as e:
            print(f"Failed to load Thonburian model: {e}")
            return None
    return _transformers_models[model_id]

DEFAULT_MODEL = os.getenv("WHISPER_MODEL_SIZE", "faster-whisper-large-v3")

def transcribe_audio(file_path: str, stt_model: str = None, temperature: float = 0.0):
    """
    Transcribes the audio file at the given path and returns segments.
    Explicitly targets Thai and English.
    Each segment contains start, end, and text.
    """
    stt_model = stt_model if stt_model else DEFAULT_MODEL
    
    transcribed_segments = []
    full_text = []

    if stt_model == "thonburian":
        model = get_thonburian_model()
        if model is None:
            return [{"start": 0.0, "end": 1.0, "text": "[Thonburian Whisper Failed to Load - Please 'pip install transformers' if not installed]"}], "[Error Loading Model]"
        
        try:
            # Use faster-whisper's decode_audio (which uses PyAV) 
            # to handle mp3/m4a files without needing an external ffmpeg executable
            from faster_whisper.audio import decode_audio
            audio_array = decode_audio(file_path)
            
            generate_kwargs = {}
            if temperature > 0.0:
                generate_kwargs = {"temperature": temperature, "do_sample": True}
                
            result = model(audio_array, return_timestamps=True, generate_kwargs=generate_kwargs)
            chunks = result.get("chunks", [{"text": result.get("text", ""), "timestamp": (0.0, 1.0)}])
        except Exception as e:
            print(f"Error processing audio in Thonburian model: {e}")
            return [{"start": 0.0, "end": 1.0, "text": f"[Error Processing Audio: {str(e)}]"}], "[Error Processing Audio]"
        
        for chunk in chunks:
            timestamp = chunk.get("timestamp")
            if isinstance(timestamp, tuple) and len(timestamp) == 2:
                start, end = timestamp
            else:
                start, end = 0.0, 1.0
                
            if start is None: start = 0.0
            if end is None: end = 1.0
            
            text = chunk.get("text", "").strip()
            transcribed_segments.append({
                "start": start,
                "end": end,
                "text": text,
                "speaker": "Unknown"
            })
            full_text.append(text)
            
        return transcribed_segments, " ".join(full_text)
        
    else:
        fw_model_size = stt_model.replace("faster-whisper-", "") if "faster-whisper-" in stt_model else stt_model
        
        # Map specific names to their HuggingFace repositories if needed
        if fw_model_size == "turbo":
            fw_model_size = "deepdml/faster-whisper-large-v3-turbo-ct2"
            
        model = get_faster_whisper_model(fw_model_size)

        if model is None:
            return [{"start": 0.0, "end": 1.0, "text": f"[Faster Whisper Model {fw_model_size} Failed to Load]"}], f"[Error Loading Model]"

        segments, info = model.transcribe(
            file_path,
            beam_size=5 if temperature == 0.0 else 1,
            temperature=temperature,
            language="th",
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        for segment in segments:
            transcribed_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "speaker": "Unknown"
            })
            full_text.append(segment.text.strip())

        return transcribed_segments, " ".join(full_text)
