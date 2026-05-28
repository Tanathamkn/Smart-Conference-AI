import os
import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import re

from app.db.session import get_db
from app.models.db import Meeting, MeetingSegment, ActionItem, Issue
from app.services.audio_processing import transcribe_audio
from app.services.llm_processing import extract_meeting_info, qa_meeting, evaluate_best_transcript, expand_search_query
from app.services.embedding import generate_embedding
from app.services.reranking import rerank_segments   # new

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = "/tmp/audio_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_pgvector(val) -> list[float]:
    """Parse pgvector string '[0.1,-0.2,...]' into a float list."""
    return [float(x) for x in re.sub(r"[\[\]\s]", "", str(val)).split(",")]

def _build_enriched_text(meeting_title: str, meeting_date, segment_text: str) -> str:
    """
    Prepend meeting metadata to a chunk before embedding so the vector
    carries topical context, not just the raw words.
    """
    date_str = meeting_date.strftime("%Y-%m-%d") if meeting_date else "unknown date"
    return f"Meeting: {meeting_title} | Date: {date_str}\n\n{segment_text}"


def _mmr(
    query_embedding: list[float],
    candidates: list[dict],
    lambda_: float = 0.5,
    top_k: int = 5,
) -> list[dict]:
    """
    Maximal Marginal Relevance — balance relevance to the query against
    redundancy among already-selected results so one verbose meeting
    cannot dominate the top-k.
    """
    import numpy as np

    def cosine(a, b):
        a, b = np.array(a), np.array(b)
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        return float(np.dot(a, b) / denom) if denom else 0.0

    selected: list[dict] = []
    remaining = list(candidates)

    while len(selected) < top_k and remaining:
        if not selected:
            best = max(remaining, key=lambda c: cosine(query_embedding, c["embedding"]))
        else:
            best = max(
                remaining,
                key=lambda c: (
                    lambda_ * cosine(query_embedding, c["embedding"])
                    - (1 - lambda_) * max(
                        cosine(s["embedding"], c["embedding"]) for s in selected
                    )
                ),
            )
        selected.append(best)
        remaining.remove(best)

    return selected


# ── Background processing ─────────────────────────────────────────────────────

def process_meeting_background(
    meeting_id: int,
    file_path: str,
    db: Session,
    stt_model: str = "large-v3",
    ensemble: bool = False,
):
    """
    Full pipeline:
    1. Transcribe audio (single or ensemble).
    2. Generate *enriched* embeddings — metadata prepended to each chunk
       so the vector search is context-aware from the start.
    3. Extract summary / action items / issues via Typhoon.
    4. Persist everything; clean up audio file.
    """
    try:
        # 1. Transcription
        if ensemble:
            logger.info(f"[Meeting {meeting_id}] ENSEMBLE transcription ({stt_model}) …")
            segments1, text1 = transcribe_audio(file_path, stt_model=stt_model, temperature=0.0)
            segments2, text2 = transcribe_audio(file_path, stt_model=stt_model, temperature=0.2)
            segments3, text3 = transcribe_audio(file_path, stt_model=stt_model, temperature=0.4)
            logger.info(f"[Meeting {meeting_id}] Evaluating best transcript …")
            best_text = evaluate_best_transcript(text1, text2, text3)
            segments, full_text = segments1, best_text
        else:
            logger.info(f"[Meeting {meeting_id}] Transcribing {file_path} with {stt_model} …")
            segments, full_text = transcribe_audio(file_path, stt_model=stt_model, temperature=0.0)

        logger.info(f"[Meeting {meeting_id}] Transcription done — {len(segments)} segments.")

        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            logger.error(f"[Meeting {meeting_id}] Not found in DB.")
            return

        meeting.transcript = full_text
        db.commit()

        # 2. Embeddings — enrich each chunk with meeting metadata before encoding
        logger.info(f"[Meeting {meeting_id}] Generating enriched embeddings …")
        for seg in segments:
            enriched = _build_enriched_text(meeting.title, meeting.date, seg["text"])
            embedding = generate_embedding(enriched)          # ← enriched, not raw text
            db_segment = MeetingSegment(
                meeting_id=meeting_id,
                speaker=seg["speaker"],
                start_time=seg["start"],
                end_time=seg["end"],
                text=seg["text"],                             # store raw text for display
                embedding=embedding,                          # store enriched embedding
            )
            db.add(db_segment)
        db.commit()
        logger.info(f"[Meeting {meeting_id}] Embeddings saved.")

        # 3. LLM extraction
        logger.info(f"[Meeting {meeting_id}] Calling LLM …")
        extracted_info = extract_meeting_info(full_text)
        meeting.summary = extracted_info.get("summary", "")

        for item in extracted_info.get("action_items", []):
            db.add(ActionItem(
                meeting_id=meeting_id,
                owner=item.get("owner"),
                task_description=item.get("task_description"),
            ))

        for issue in extracted_info.get("issues", []):
            db.add(Issue(
                meeting_id=meeting_id,
                product=issue.get("product"),
                problem=issue.get("problem"),
                solution=issue.get("solution"),
            ))

        db.commit()
        logger.info(f"[Meeting {meeting_id}] Processing complete.")

    except Exception as e:
        logger.error(f"[Meeting {meeting_id}] Error: {e}", exc_info=True)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"[Meeting {meeting_id}] Audio file cleaned up.")


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/meetings/upload")
async def upload_meeting(
    background_tasks: BackgroundTasks,
    title: str,
    stt_model: str = "large-v3",
    ensemble: bool = False,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    new_meeting = Meeting(title=title)
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)

    background_tasks.add_task(
        process_meeting_background,
        new_meeting.id,
        file_path,
        Session(bind=db.get_bind()),
        stt_model,
        ensemble,
    )
    return {"message": "Upload successful, processing started.", "meeting_id": new_meeting.id}


@router.get("/meetings")
def list_meetings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    meetings = db.query(Meeting).offset(skip).limit(limit).all()
    return [{"id": m.id, "title": m.title, "date": m.date, "summary": m.summary} for m in meetings]


@router.get("/meetings/stats")
def get_stats(db: Session = Depends(get_db)):
    return {
        "action_items": db.query(ActionItem).count(),
        "issues":       db.query(Issue).count(),
        "meetings":     db.query(Meeting).count(),
    }


@router.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {
        "id":          meeting.id,
        "title":       meeting.title,
        "date":        meeting.date,
        "transcript":  meeting.transcript,
        "summary":     meeting.summary,
        "action_items": [
            {"id": a.id, "owner": a.owner, "task": a.task_description, "status": a.status}
            for a in meeting.action_items
        ],
        "issues": [
            {"id": i.id, "product": i.product, "problem": i.problem, "solution": i.solution}
            for i in meeting.issues
        ],
    }


@router.delete("/meetings/{meeting_id}")
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    db.delete(meeting)
    db.commit()
    logger.info(f"[Meeting {meeting_id}] Deleted.")
    return {"message": "Meeting deleted successfully"}

@router.get("/search")
def search_meetings(
    query: str,
    meeting_id: Optional[int]  = Query(None),
    date_from:  Optional[str]  = Query(None),
    date_to:    Optional[str]  = Query(None),
    top_k:      int            = Query(5, ge=1, le=20),
    mmr:        bool           = Query(True),
    rerank:     bool           = Query(True),
    db: Session = Depends(get_db),
):
    expanded_query  = expand_search_query(query)
    query_embedding = generate_embedding(expanded_query)

    # Format the embedding as a pgvector literal: '[0.1, 0.2, ...]'
    embedding_literal = "[" + ",".join(str(x) for x in query_embedding) + "]"

    filter_clauses = []
    filter_params: dict = {"query_text": expanded_query}

    if meeting_id is not None:
        filter_clauses.append("ms.meeting_id = :meeting_id")
        filter_params["meeting_id"] = meeting_id
    if date_from:
        filter_clauses.append("m.date >= :date_from")
        filter_params["date_from"] = date_from
    if date_to:
        filter_clauses.append("m.date <= :date_to")
        filter_params["date_to"] = date_to

    where = ("WHERE " + " AND ".join(filter_clauses)) if filter_clauses else ""

    # Use CAST() instead of :: to avoid the colon conflict with SQLAlchemy
    # Interpolate the embedding literal directly — it's a float array we
    # built ourselves, not user input, so this is safe
    sql = text(f"""
        SELECT
            ms.id,
            ms.meeting_id,
            ms.text,
            ms.embedding,
            m.title,
            m.date,
            (1 - (ms.embedding <=> CAST('{embedding_literal}' AS vector))) AS dense_score,
            ts_rank(
                to_tsvector('simple', ms.text),
                plainto_tsquery('simple', :query_text)
            ) AS sparse_score,
            (
                0.6 * (1 - (ms.embedding <=> CAST('{embedding_literal}' AS vector)))
              + 0.4 * ts_rank(
                    to_tsvector('simple', ms.text),
                    plainto_tsquery('simple', :query_text)
                )
            ) AS hybrid_score
        FROM meeting_segments ms
        JOIN meetings m ON ms.meeting_id = m.id
        {where}
        ORDER BY hybrid_score DESC
        LIMIT :candidate_limit
    """)

    filter_params["candidate_limit"] = top_k * 4
    rows = db.execute(sql, filter_params).fetchall()

    if not rows:
        return {"answer": "No relevant segments found.", "relevant_segments": [], "expanded_query": expanded_query}

    candidates = [
    {
        "segment_id":    row[0],
        "meeting_id":    row[1],
        "text":          row[2],
        # pgvector returns the embedding as a string '[0.1, 0.2, ...]'
        # json.loads handles both '[1,2,3]' and numpy-style representations
        "embedding":     parse_pgvector(row[3]),
        "meeting_title": row[4],
        "meeting_date":  str(row[5]),
        "dense_score":   float(row[6]),
        "sparse_score":  float(row[7]),
        "hybrid_score":  float(row[8]),
    }
    for row in rows
]

    if mmr and len(candidates) > top_k:
        candidates = _mmr(query_embedding, candidates, lambda_=0.5, top_k=top_k * 2)

    if rerank:
        candidates = rerank_segments(query, candidates, top_k=top_k)
    else:
        candidates = candidates[:top_k]

    context = "\n\n".join(
        f"Meeting: {c['meeting_title']} ({c['meeting_date']})\nExcerpt: {c['text']}"
        for c in candidates
    )
    answer = qa_meeting(context, query)

    for c in candidates:
        c.pop("embedding", None)

    return {
        "answer":            answer,
        "expanded_query":    expanded_query,
        "relevant_segments": candidates,
    }

@router.post("/admin/reembed")
def reembed_all_segments(db: Session = Depends(get_db)):
    """Re-generate embeddings for all segments with bilingual enrichment."""
    segments = db.query(MeetingSegment).all()
    for seg in segments:
        meeting = db.query(Meeting).filter(Meeting.id == seg.meeting_id).first()
        enriched  = _build_enriched_text(meeting.title, meeting.date, seg.text)
        seg.embedding = generate_embedding(enriched)
    db.commit()
    return {"reembedded": len(segments)}