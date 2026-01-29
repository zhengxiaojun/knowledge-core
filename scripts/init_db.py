import asyncio
from sqlalchemy import (
    String,
    Text,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    func,
)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.core.config import settings


class Base(DeclarativeBase):
    pass


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    business_domain: Mapped[str | None] = mapped_column(String(128), nullable=True)
    priority: Mapped[int | None] = mapped_column(nullable=True)
    full_content: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now())


class TestKnowledge(Base):
    __tablename__ = "test_knowledge"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(32))
    graph_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now())


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    requirement_id: Mapped[str | None] = mapped_column(ForeignKey("requirements.id"), nullable=True)
    test_case_title: Mapped[str] = mapped_column(String(255))
    test_case_content: Mapped[str] = mapped_column(Text)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now())


async def init():
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL 未配置")
    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("数据库初始化完成")


if __name__ == "__main__":
    asyncio.run(init())
