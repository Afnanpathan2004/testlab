"""Business logic for tests and questions."""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from auth.authenticator import Authenticator
from database.crud import QuestionCRUD, TestCRUD
from database.models import Question, Test
from utils.exceptions import ValidationError
from utils.logger import setup_logger
from utils.validators import InputValidator

logger = setup_logger(__name__)


class TestService:
    @staticmethod
    def create_test(
        session: Session,
        teacher_id: int,
        title: str,
        description: str | None,
        test_type: str,
    ) -> Test:
        title = InputValidator.sanitize_string(title, max_length=255)
        description = InputValidator.sanitize_string(description or "", max_length=1000) if description else None
        if test_type not in {"pre", "post"}:
            raise ValidationError("test_type must be 'pre' or 'post'")
        access_key = Authenticator.generate_access_key(8)
        test = TestCRUD.create(
            session,
            {
                "title": title,
                "description": description,
                "test_type": test_type,
                "access_key": access_key,
                "is_published": 0,
            },
            teacher_id=teacher_id,
        )
        logger.info("Test created teacher_id=%s title=%s", teacher_id, title)
        return test

    @staticmethod
    def add_question(
        session: Session,
        test_id: int,
        question_text: str,
        options: list[str],
        correct_answer: int,
        explanation: str,
        topic_tag: str,
        difficulty: str,
        order: int,
    ) -> Question:
        question_text = InputValidator.sanitize_string(question_text, max_length=2000)
        explanation = InputValidator.sanitize_string(explanation, max_length=1000)
        topic_tag = InputValidator.sanitize_string(topic_tag, max_length=120)
        if difficulty not in {"easy", "medium", "hard"}:
            raise ValidationError("difficulty must be 'easy', 'medium', or 'hard'")
        if not isinstance(options, list) or len(options) != 4:
            raise ValidationError("Exactly 4 options are required")
        options = [InputValidator.sanitize_string(o, max_length=255) for o in options]
        if len(set(options)) != 4:
            raise ValidationError("Options must be unique")
        if not isinstance(correct_answer, int) or not (0 <= correct_answer <= 3):
            raise ValidationError("correct_answer must be an integer between 0 and 3")
        order = InputValidator.validate_integer(order, min_val=0)

        q = QuestionCRUD.create(
            session,
            {
                "question_text": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "explanation": explanation,
                "topic_tag": topic_tag,
                "difficulty": difficulty,
                "order": order,
            },
            test_id=test_id,
        )
        logger.info("Question added test_id=%s qid=%s", test_id, q.id)
        return q

    @staticmethod
    def get_test_by_key(session: Session, access_key: str) -> Test:
        if not access_key:
            raise ValidationError("Access key is required")
        key = access_key.strip().upper()
        test = TestCRUD.get_by_access_key(session, key)
        if not test:
            raise ValidationError("Test not found for provided access key")
        if not test.is_published:
            raise ValidationError("Test is not published yet")
        return test

    @staticmethod
    def publish_test(session: Session, test_id: int, teacher_id: int) -> Test:
        test = TestCRUD.get_by_id(session, test_id)
        if not test:
            raise ValidationError("Test not found")
        if test.teacher_id != teacher_id:
            raise ValidationError("You do not have permission to publish this test")
        updated = TestCRUD.update(session, test_id, {"is_published": 1})
        logger.info("Test published id=%s", test_id)
        return updated

    @staticmethod
    def get_teacher_tests(session: Session, teacher_id: int) -> List[Test]:
        tests = TestCRUD.get_teacher_tests(session, teacher_id)
        return tests

    @staticmethod
    def update_test_metadata(
        session: Session,
        test_id: int,
        teacher_id: int,
        title: str | None = None,
        description: str | None = None,
        test_type: str | None = None,
    ) -> Test:
        test = TestCRUD.get_by_id(session, test_id)
        if not test:
            raise ValidationError("Test not found")
        if test.teacher_id != teacher_id:
            raise ValidationError("You do not have permission to edit this test")
        updates: dict = {}
        if title is not None:
            updates["title"] = InputValidator.sanitize_string(title, max_length=255)
        if description is not None:
            updates["description"] = InputValidator.sanitize_string(description, max_length=1000)
        if test_type is not None:
            if test_type not in {"pre", "post"}:
                raise ValidationError("test_type must be 'pre' or 'post'")
            updates["test_type"] = test_type
        if not updates:
            return test
        updated = TestCRUD.update(session, test_id, updates)
        logger.info("Test metadata updated id=%s", test_id)
        return updated

    @staticmethod
    def delete_test(session: Session, test_id: int, teacher_id: int) -> bool:
        test = TestCRUD.get_by_id(session, test_id)
        if not test:
            raise ValidationError("Test not found")
        if test.teacher_id != teacher_id:
            raise ValidationError("You do not have permission to delete this test")
        ok = TestCRUD.delete(session, test_id)
        logger.info("Test deleted id=%s", test_id)
        return ok
