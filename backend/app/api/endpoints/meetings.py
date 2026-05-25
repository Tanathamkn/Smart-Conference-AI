import os
import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.models.db import Meeting, MeetingSegment, ActionItem, Issue
from app.services.audio_processing import transcribe_audio
from app.services.llm_processing import extract_meeting_info, qa_meeting
from app.services.embedding import generate_embedding

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = "/tmp/audio_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def process_meeting_background(meeting_id: int, file_path: str, db: Session):
    try:
        # 1. Transcribe Audio
        logger.info(f"[Meeting {meeting_id}] Starting transcription of {file_path}...")
        segments, full_text = transcribe_audio(file_path)
        logger.info(f"[Meeting {meeting_id}] Transcription complete. {len(segments)} segments found.")

        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            logger.error(f"[Meeting {meeting_id}] Meeting not found in DB after transcription.")
            return

        meeting.transcript = full_text
        db.commit()

        # 2. Generate Embeddings for Segments
        logger.info(f"[Meeting {meeting_id}] Generating embeddings for {len(segments)} segments...")
        for seg in segments:
            embedding = generate_embedding(seg["text"])
            db_segment = MeetingSegment(
                meeting_id=meeting_id,
                speaker=seg["speaker"],
                start_time=seg["start"],
                end_time=seg["end"],
                text=seg["text"],
                embedding=embedding
            )
            db.add(db_segment)
        db.commit()
        logger.info(f"[Meeting {meeting_id}] Embeddings saved.")

        # 3. Extract Information via LLM
        logger.info(f"[Meeting {meeting_id}] Calling LLM for summary and extraction...")
        extracted_info = extract_meeting_info(full_text)

        meeting.summary = extracted_info.get("summary", "")

        for item in extracted_info.get("action_items", []):
            db_action = ActionItem(
                meeting_id=meeting_id,
                owner=item.get("owner"),
                task_description=item.get("task_description"),
            )
            db.add(db_action)

        for issue in extracted_info.get("issues", []):
            db_issue = Issue(
                meeting_id=meeting_id,
                product=issue.get("product"),
                problem=issue.get("problem"),
                solution=issue.get("solution")
            )
            db.add(db_issue)

        db.commit()
        logger.info(f"[Meeting {meeting_id}] Processing complete!")

    except Exception as e:
        logger.error(f"[Meeting {meeting_id}] Error during processing: {e}", exc_info=True)
    finally:
        # Cleanup audio file
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"[Meeting {meeting_id}] Cleaned up audio file: {file_path}")

@router.post("/meetings/upload")
async def upload_meeting(
    background_tasks: BackgroundTasks,
    title: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    new_meeting = Meeting(title=title)
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)

    background_tasks.add_task(process_meeting_background, new_meeting.id, file_path, Session(bind=db.get_bind()))

    return {"message": "Upload successful, processing started.", "meeting_id": new_meeting.id}

@router.get("/meetings")
def list_meetings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    meetings = db.query(Meeting).offset(skip).limit(limit).all()
    return [{"id": m.id, "title": m.title, "date": m.date, "summary": m.summary} for m in meetings]

@router.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return {
        "id": meeting.id,
        "title": meeting.title,
        "date": meeting.date,
        "transcript": meeting.transcript,
        "summary": meeting.summary,
        "action_items": [{"id": a.id, "owner": a.owner, "task": a.task_description, "status": a.status} for a in meeting.action_items],
        "issues": [{"id": i.id, "product": i.product, "problem": i.problem, "solution": i.solution} for i in meeting.issues]
    }

@router.delete("/meetings/{meeting_id}")
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    db.delete(meeting)
    db.commit()
    logger.info(f"[Meeting {meeting_id}] Deleted successfully.")
    return {"message": "Meeting deleted successfully"}

@router.get("/search")
def search_meetings(query: str, db: Session = Depends(get_db)):
    query_embedding = generate_embedding(query)

    sql = text("""
        SELECT ms.id, ms.meeting_id, ms.text, m.title,
               (ms.embedding <-> :embedding) as distance
        FROM meeting_segments ms
        JOIN meetings m ON ms.meeting_id = m.id
        ORDER BY ms.embedding <-> :embedding
        LIMIT 5
    """)

    results = db.execute(sql, {"embedding": str(query_embedding)}).fetchall()

    segments = []
    context = ""
    for row in results:
        segments.append({
            "segment_id": row[0],
            "meeting_id": row[1],
            "text": row[2],
            "meeting_title": row[3],
            "distance": row[4]
        })
        context += f"Meeting: {row[3]}\nTranscript segment: {row[2]}\n\n"

    answer = qa_meeting(context, query)

    return {
        "answer": answer,
        "relevant_segments": segments
    }
