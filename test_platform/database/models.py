"""SQLAlchemy ORM models for the Test Platform."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Float,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class User(Base):
    """Application user: teacher or student."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "teacher" | "student"
    is_active: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    tests: Mapped[List["Test"]] = relationship(
        back_populates="teacher", cascade="all, delete-orphan", passive_deletes=True
    )
    attempts: Mapped[List["Attempt"]] = relationship(back_populates="student", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - repr
        return f"<User id={self.id} username={self.username} role={self.role}>"


class Test(Base):
    """A pre or post test created by a teacher."""

    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    test_type: Mapped[str] = mapped_column(String(10), nullable=False)  # "pre" | "post"
    access_key: Mapped[str] = mapped_column(String(12), unique=True, index=True, nullable=False)
    is_published: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    teacher: Mapped[User] = relationship(back_populates="tests")
    questions: Mapped[List["Question"]] = relationship(
        back_populates="test", cascade="all, delete-orphan", order_by="Question.order"
    )
    attempts: Mapped[List["Attempt"]] = relationship(back_populates="test", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Test id={self.id} title={self.title!r} type={self.test_type} published={self.is_published}>"


class Question(Base):
    """A multiple-choice question belonging to a test."""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    test_id: Mapped[int] = mapped_column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), index=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[List[str]] = mapped_column(JSON, nullable=False)  # exactly 4 options
    correct_answer: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-3 index
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    topic_tag: Mapped[Optional[str]] = mapped_column(String(120), index=True, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False)  # easy|medium|hard
    order: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    test: Mapped[Test] = relationship(back_populates="questions")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Question id={self.id} test_id={self.test_id} order={self.order}>"


class Attempt(Base):
    """A student's attempt for a test."""

    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    test_id: Mapped[int] = mapped_column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    answers: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    time_taken: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # seconds
    is_submitted: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    test: Mapped[Test] = relationship(back_populates="attempts")
    student: Mapped[User] = relationship(back_populates="attempts")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Attempt id={self.id} test_id={self.test_id} student_id={self.student_id} score={self.score}>"


# Additional indexes for frequent queries
Index("ix_tests_teacher_created", Test.teacher_id, Test.created_at.desc())
Index("ix_questions_test_order", Question.test_id, Question.order)
Index("ix_attempts_student_completed", Attempt.student_id, Attempt.completed_at.desc())
