import os
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from pgvector.sqlalchemy import Vector
import enum
from datetime import datetime

Base = declarative_base()

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)

    segments = relationship("MeetingSegment", back_populates="meeting", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="meeting", cascade="all, delete-orphan")

class MeetingSegment(Base):
    __tablename__ = "meeting_segments"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    speaker = Column(String, nullable=True)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)
    
    # Ensure this matches the embedding dimension of your model (e.g., 1024 for bge-m3)
    embedding = Column(Vector(1024), nullable=True) 

    meeting = relationship("Meeting", back_populates="segments")

class ActionItemStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    owner = Column(String, nullable=True)
    task_description = Column(Text, nullable=False)
    due_date = Column(DateTime, nullable=True)
    status = Column(SQLEnum(ActionItemStatus), default=ActionItemStatus.PENDING)

    meeting = relationship("Meeting", back_populates="action_items")

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    product = Column(String, nullable=True)
    problem = Column(Text, nullable=False)
    solution = Column(Text, nullable=True)

    meeting = relationship("Meeting", back_populates="issues")

# To be used by session maker
# engine = create_engine(os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/smartconf"))
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)