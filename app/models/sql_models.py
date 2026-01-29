from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Text, DECIMAL, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

from app.core.config import settings

engine = create_engine(settings.sqlalchemy_database_uri)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class StatusEnum(str, enum.Enum):
    INIT = "INIT"
    PENDING = "pending"
    PROCESSING = "processing"
    RUNNING = "RUNNING"
    COMPLETED = "completed"
    DONE = "DONE"
    FAILED = "failed"

class TestCaseStatusEnum(str, enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    EXECUTED = "executed"

class TestKnowledgeTypeEnum(str, enum.Enum):
    TEST_POINT = "TestPoint"
    SCENARIO = "Scenario"
    RISK = "Risk"

class CreatorEnum(str, enum.Enum):
    AI = "ai"
    MANUAL = "manual"

# ========== Requirement Tables ==========

class RequirementRaw(Base):
    """存储用户原始需求，完整保留原始信息"""
    __tablename__ = "requirement_raw"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, comment="需求标题")
    full_content = Column(Text, nullable=False, comment="完整需求内容")
    source_type = Column(String(50), comment="来源类型：text/pdf/docx/excel/image")
    source_file = Column(String(255), comment="原始文件名")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    requirement_std = relationship("RequirementStd", back_populates="requirement_raw", uselist=False)

class RequirementStd(Base):
    """标准化需求数据，供下游模块统一使用"""
    __tablename__ = "requirement_std"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    raw_req_id = Column(BigInteger, ForeignKey("requirement_raw.id"), nullable=False, comment="关联原始需求ID")
    summary = Column(Text, comment="需求摘要")
    business_domain = Column(String(100), comment="业务域")
    priority = Column(String(10), comment="优先级 P0/P1/P2/P3")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    requirement_raw = relationship("RequirementRaw", back_populates="requirement_std")
    test_cases = relationship("TestCase", back_populates="requirement_std")

# ========== Test Knowledge Tables ==========

class TestPoint(Base):
    """存储抽象后的测试知识单元"""
    __tablename__ = "test_point"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    content = Column(String(500), nullable=False, comment="测试点内容")
    type = Column(SQLEnum(TestKnowledgeTypeEnum), nullable=False, comment="类型：TestPoint/Scenario/Risk")
    confidence = Column(DECIMAL(3, 2), default=0.5, comment="置信度（0–1）")
    vector_id = Column(String(100), comment="向量库ID")
    graph_id = Column(String(100), comment="图数据库节点ID")
    source = Column(String(50), comment="来源：requirement/defect/case")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    test_cases = relationship("TestCase", back_populates="test_point")
    generation_results = relationship("GenerationResult", back_populates="test_point")

# ========== Test Case Tables ==========

class TestCase(Base):
    """存储测试用例数据"""
    __tablename__ = "test_case"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, comment="用例标题")
    precondition = Column(Text, comment="前置条件")
    steps = Column(Text, nullable=False, comment="测试步骤")
    expected = Column(Text, nullable=False, comment="预期结果")
    related_req_id = Column(BigInteger, ForeignKey("requirement_std.id"), comment="关联需求ID")
    test_point_id = Column(BigInteger, ForeignKey("test_point.id"), comment="关联测试点ID")
    status = Column(SQLEnum(TestCaseStatusEnum), default=TestCaseStatusEnum.DRAFT, comment="状态")
    created_by = Column(SQLEnum(CreatorEnum), comment="创建者：ai/manual")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    requirement_std = relationship("RequirementStd", back_populates="test_cases")
    test_point = relationship("TestPoint", back_populates="test_cases")

# ========== Defect Tables ==========

class Defect(Base):
    """存储缺陷信息"""
    __tablename__ = "defect"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    defect_id = Column(String(100), unique=True, comment="缺陷系统ID")
    title = Column(String(255), nullable=False, comment="缺陷标题")
    phenomenon = Column(Text, comment="问题现象")
    root_cause = Column(Text, comment="根本原因")
    related_req_id = Column(BigInteger, comment="关联需求ID")
    severity = Column(String(20), comment="严重程度")
    status = Column(String(20), comment="状态")
    created_at = Column(DateTime, default=datetime.utcnow)

# ========== Generation Task Tables ==========

class GenerationTask(Base):
    """记录测试用例生成任务的执行状态"""
    __tablename__ = "generation_task"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    raw_req_id = Column(BigInteger, ForeignKey("requirement_raw.id"), comment="关联原始需求ID")
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.INIT, comment="任务状态")
    progress = Column(Integer, default=0, comment="进度百分比")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, comment="完成时间")

    # Relationships
    requirement_raw = relationship("RequirementRaw")
    generation_results = relationship("GenerationResult", back_populates="task")

class GenerationResult(Base):
    """存储生成结果及人工确认状态"""
    __tablename__ = "generation_result"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    task_id = Column(BigInteger, ForeignKey("generation_task.id"), nullable=False, comment="关联任务ID")
    test_point_id = Column(BigInteger, ForeignKey("test_point.id"), comment="测试点ID")
    test_case_content = Column(Text, comment="生成的测试用例内容")
    approved = Column(Boolean, default=False, comment="是否已确认")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task = relationship("GenerationTask", back_populates="generation_results")
    test_point = relationship("TestPoint", back_populates="generation_results")

# ========== Legacy Tables (for backward compatibility) ==========

class Requirement(Base):
    """Legacy requirement table for backward compatibility"""
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(Integer, default=1)
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.PENDING)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    knowledge_bases = relationship("KnowledgeBase", back_populates="requirement")

class KnowledgeBase(Base):
    """Legacy knowledge base table"""
    __tablename__ = "knowledge_bases"

    id = Column(String(255), primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.PENDING)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requirement = relationship("Requirement", back_populates="knowledge_bases")
    tasks = relationship("Task", back_populates="knowledge_base")

class Task(Base):
    """Legacy task table"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(String(255), ForeignKey("knowledge_bases.id"))
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.PENDING)
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
