from sqlalchemy import create_engine, Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

from app.core.config import settings

engine = create_engine(settings.sqlalchemy_database_uri)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class StatusEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(Integer, default=1)
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    knowledge_bases = relationship("KnowledgeBase", back_populates="requirement")
    test_cases = relationship("TestCase", back_populates="requirement")

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(String(255), primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requirement = relationship("Requirement", back_populates="knowledge_bases")
    tasks = relationship("Task", back_populates="knowledge_base")

class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    description = Column(Text, nullable=False)
    expected_result = Column(Text)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requirement = relationship("Requirement", back_populates="test_cases")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(String(255), ForeignKey("knowledge_bases.id"))
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    knowledge_base = relationship("KnowledgeBase", back_populates="tasks")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
