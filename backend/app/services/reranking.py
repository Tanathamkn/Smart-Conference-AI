"""
app/services/reranking.py

Cross-encoder re-ranking pass. Runs after the pgvector retrieval stage
to apply a much more accurate relevance signal before returning results
to the user.

Model: cross-encoder/ms-marco-MiniLM-L-6-v2
  - Small (~22 MB), fast on CPU
  - Trained on MS MARCO passage ranking
  - Works well for Thai/English mixed queries because it scores
    semantic coherence rather than token overlap
"""

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_cross_encoder():
    """Load once and cache for the lifetime of the process."""
    from sentence_transformers import CrossEncoder
    logger.info("[Reranker] Loading cross-encoder/ms-marco-MiniLM-L-6-v2 …")
    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    logger.info("[Reranker] Cross-encoder ready.")
    return model


def rerank_segments(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """
    Score every (query, chunk) pair with a cross-encoder and return the
    top_k candidates sorted by that score.

    The cross-encoder sees the query AND the text together (unlike the
    bi-encoder used for retrieval), so it can resolve ambiguity that
    cosine similarity cannot — e.g. the word "budget" appearing in both
    a sales meeting and an IT procurement meeting will score differently
    when the query is "Q3 marketing budget vs Q3 IT procurement budget".

    Parameters
    ----------
    query      : the original user query (not the expanded version —
                 we want to rank against what the user actually asked)
    candidates : list of segment dicts from the retrieval stage,
                 each must have at least a "text" key
    top_k      : how many to return after re-ranking

    Returns
    -------
    List of the top_k candidate dicts, sorted best-first, with a new
    "rerank_score" key added for transparency / frontend display.
    """
    if not candidates:
        return candidates

    try:
        model = _load_cross_encoder()
        pairs  = [(query, c["text"]) for c in candidates]
        scores = model.predict(pairs)          # returns numpy array

        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)

        reranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
        return reranked[:top_k]

    except Exception as e:
        # Re-ranking is a best-effort enhancement; fall back gracefully
        logger.warning(f"[Reranker] Failed ({e}), returning unranked candidates.")
        return candidates[:top_k]