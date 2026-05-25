import logging
from sqlalchemy import text
from app.db.session import engine
from app.models.db import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    logger.info("Initializing database...")
    try:
        with engine.connect() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
            conn.commit()
        logger.info("Created pgvector extension.")
        
        Base.metadata.create_all(bind=engine)
        logger.info("Created all tables.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

if __name__ == "__main__":
    init_db()
