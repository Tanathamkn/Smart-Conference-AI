from sentence_transformers import SentenceTransformer

# Load model globally. This will be slow on the first run as it downloads the model.
# BAAI/bge-m3 supports multiple languages and generates 1024-dimensional embeddings.
try:
    model = SentenceTransformer('BAAI/bge-m3')
except Exception as e:
    print(f"Failed to load sentence-transformers model: {e}")
    model = None

def generate_embedding(text: str) -> list[float]:
    """
    Generates a 1024-dimensional embedding for the given text.
    """
    if model is None:
        # Mock embedding if model fails to load (e.g. out of memory)
        return [0.0] * 1024
    
    embedding = model.encode(text)
    return embedding.tolist()

def _build_enriched_text(meeting_title: str, meeting_date, segment_text: str) -> str:
    date_str = meeting_date.strftime("%Y-%m-%d") if meeting_date else "unknown date"
    
    # Ask Typhoon to translate the segment to the opposite language
    # so the stored embedding captures both Thai and English semantics
    translation = translate_for_embedding(segment_text)  # new helper below
    
    return (
        f"Meeting: {meeting_title} | Date: {date_str}\n\n"
        f"{segment_text}\n{translation}"
    )
