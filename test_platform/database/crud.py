"""CRUD operations with logging and error handling."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .models import User, Test, Question, Attempt
from utils.logger import setup_logger
from utils.exceptions import DatabaseError

logger = setup_logger(__name__)


class UserCRUD:
    """User CRUD operations."""

    @staticmethod
    def create(session: Session, user_data: Dict) -> User:
        try:
            user = User(**user_data)
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info("User created: %s", user.username)
            return user
        except SQLAlchemyError as exc:
            session.rollback()
            logger.error("User create failed: %s", exc)
            raise DatabaseError("Failed to create user")

    @staticmethod
    def get_by_username(session: Session, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        return session.execute(stmt).scalars().first()

    @staticmethod
    def get_by_email(session: Session, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return session.execute(stmt).scalars().first()

    @staticmethod
    def get_by_id(session: Session, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        return session.execute(stmt).scalars().first()


class TestCRUD:
    """Test CRUD operations."""

    @staticmethod
    def create(session: Session, test_data: Dict, teacher_id: int) -> Test:
        try:
            obj = Test(teacher_id=teacher_id, **test_data)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            logger.info("Test created id=%s title=%s", obj.id, obj.title)
            return obj
        except SQLAlchemyError as exc:
            session.rollback()
            logger.error("Test create failed: %s", exc)
            raise DatabaseError("Failed to create test")

    @staticmethod
    def get_by_id(session: Session, test_id: int) -> Optional[Test]:
        stmt = select(Test).where(Test.id == test_id)
        return session.execute(stmt).scalars().first()

    @staticmethod
    def get_by_access_key(session: Session, access_key: str) -> Optional[Test]:
        stmt = select(Test).where(Test.access_key == access_key)
        return session.execute(stmt).scalars().first()

    @staticmethod
    def get_teacher_tests(session: Session, teacher_id: int) -> List[Test]:
        stmt = select(Test).where(Test.teacher_id == teacher_id).order_by(Test.created_at.desc())
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def update(session: Session, test_id: int, updates_dict: Dict) -> Test:
        try:
            stmt = (
                update(Test)
                .where(Test.id == test_id)
                .values(**updates_dict)
                .execution_options(synchronize_session="fetch")
            )
            session.execute(stmt)
            session.commit()
            obj = TestCRUD.get_by_id(session, test_id)
            if not obj:
                raise DatabaseError("Test not found after update")
            logger.info("Test updated id=%s", test_id)
            return obj
        except SQLAlchemyError as exc:
            session.rollback()
            logger.error("Test update failed: %s", exc)
            raise DatabaseError("Failed to update test")

    @staticmethod
    def delete(session: Session, test_id: int) -> bool:
        try:
            stmt = delete(Test).where(Test.id == test_id)
            res = session.execute(stmt)
            session.commit()
            success = res.rowcount and res.rowcount > 0
            logger.info("Test deleted id=%s success=%s", test_id, success)
            return bool(success)
        except SQLAlchemyError as exc:
            session.rollback()
            logger.error("Test delete failed: %s", exc)
            raise DatabaseError("Failed to delete test")


class QuestionCRUD:
    """Question CRUD operations."""

    @staticmethod
    def create(session: Session, question_data: Dict, test_id: int) -> Question:
        try:
            obj = Question(test_id=test_id, **question_data)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            logger.info("Question created id=%s test_id=%s", obj.id, test_id)
            return obj
        except SQLAlchemyError as exc:
            session.rollback()
            logger.error("Question create failed: %s", exc)
            raise DatabaseError("Failed to create question")

    @staticmethod
    def get_by_id(session: Session, question_id: int) -> Optional[Question]:
        stmt = select(Question).where(Question.id == question_id)
        return session.execute(stmt).scalars().first()

    @staticmethod
    def get_test_questions(session: Session, test_id: int) -> List[Question]:
        stmt = select(Question).where(Question.test_id == test_id).order_by(Question.order.asc())
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def delete(session: Session, question_id: int) -> bool:
        try:
            stmt = delete(Question).where(Question.id == question_id)
            res = session.execute(stmt)
            session.commit()
            success = res.rowcount and res.rowcount > 0
            logger.info("Question deleted id=%s success=%s", question_id, success)
            return bool(success)
        except SQLAlchemyError as exc:
            session.rollback()
            logger.error("Question delete failed: %s", exc)
            raise DatabaseError("Failed to delete question")


class AttemptCRUD:
    """Attempt CRUD with scoring calculation."""

    @staticmethod
    def create(session: Session, test_id: int, student_id: int, answers_dict: Dict[int, int]) -> Attempt:
        try:
            # Calculate score
            questions = QuestionCRUD.get_test_questions(session, test_id)
            total = len(questions)
            if total == 0:
                score = 0.0
            else:
                correct = 0
                for q in questions:
                    sel = answers_dict.get(q.id)
                    if isinstance(sel, int) and 0 <= sel <= 3 and sel == q.correct_answer:
                        correct += 1
                score = (correct / total) * 100.0

            # Normalize keys to strings for JSON storage
            answers_norm: Dict[str, int] = {str(k): int(v) for k, v in (answers_dict or {}).items()}

            obj = Attempt(
                test_id=test_id,
                student_id=student_id,
                answers=answers_norm,
                score=score,
                is_submitted=1,
                completed_at=datetime.utcnow(),
            )
            session.add(obj)
            session.commit()
            session.refresh(obj)
            logger.info("Attempt created id=%s score=%.2f", obj.id, obj.score)
            return obj
        except SQLAlchemyError as exc:
            session.rollback()
            logger.error("Attempt create failed: %s", exc)
            raise DatabaseError("Failed to create attempt")

    @staticmethod
    def get_by_id(session: Session, attempt_id: int) -> Optional[Attempt]:
        stmt = select(Attempt).where(Attempt.id == attempt_id)
        return session.execute(stmt).scalars().first()

    @staticmethod
    def get_student_attempts(session: Session, student_id: int) -> List[Attempt]:
        stmt = select(Attempt).where(Attempt.student_id == student_id).order_by(Attempt.completed_at.desc())
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def get_test_attempts(session: Session, test_id: int) -> List[Attempt]:
        stmt = select(Attempt).where(Attempt.test_id == test_id).order_by(Attempt.completed_at.desc())
        return list(session.execute(stmt).scalars().all())
