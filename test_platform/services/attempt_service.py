"""Business logic for test attempts and results."""
from __future__ import annotations

from statistics import mean
from typing import Dict, List

from sqlalchemy.orm import Session

from database.crud import AttemptCRUD, QuestionCRUD, TestCRUD
from database.models import Attempt, Question, Test
from utils.exceptions import ValidationError
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AttemptService:
    @staticmethod
    def start_attempt(session: Session, test_id: int, student_id: int) -> Dict:
        test = TestCRUD.get_by_id(session, test_id)
        if not test:
            raise ValidationError("Test not found")
        if not test.is_published:
            raise ValidationError("Test is not published")
        questions = QuestionCRUD.get_test_questions(session, test.id)
        payload = {
            "test_id": test.id,
            "test_title": test.title,
            "test_type": test.test_type,
            "questions_count": len(questions),
            "questions": [
                {
                    "id": q.id,
                    "question_text": q.question_text,
                    "options": q.options,
                    "topic_tag": q.topic_tag,
                    "difficulty": q.difficulty,
                }
                for q in questions
            ],
        }
        logger.info("Attempt started student_id=%s test_id=%s", student_id, test_id)
        return payload

    @staticmethod
    def submit_attempt(session: Session, test_id: int, student_id: int, answers: Dict[int, int]) -> Attempt:
        questions = QuestionCRUD.get_test_questions(session, test_id)
        qids = {q.id for q in questions}
        # Validate all questions answered
        if not questions:
            raise ValidationError("No questions in test")
        if set(answers.keys()) != qids:
            raise ValidationError("All questions must be answered")
        for v in answers.values():
            if not isinstance(v, int) or v < 0 or v > 3:
                raise ValidationError("Invalid answer value; must be 0-3")
        attempt = AttemptCRUD.create(session, test_id, student_id, answers)
        return attempt

    @staticmethod
    def get_attempt_results(session: Session, attempt_id: int, student_id: int) -> Dict:
        attempt = AttemptCRUD.get_by_id(session, attempt_id)
        if not attempt:
            raise ValidationError("Attempt not found")
        if attempt.student_id != student_id:
            raise ValidationError("Unauthorized to view this attempt")
        questions = QuestionCRUD.get_test_questions(session, attempt.test_id)
        details: List[Dict] = []
        raw_answers = attempt.answers or {}
        answers = {int(k): int(v) for k, v in raw_answers.items() if str(k).isdigit()}
        for q in questions:
            student_answer = answers.get(q.id)
            details.append(
                {
                    "question_id": q.id,
                    "question_text": q.question_text,
                    "options": q.options,
                    "student_answer": student_answer,
                    "correct_answer": q.correct_answer,
                    "is_correct": student_answer == q.correct_answer,
                    "explanation": q.explanation,
                    "topic": q.topic_tag,
                }
            )
        return {
            "attempt_id": attempt.id,
            "score": attempt.score,
            "completed_at": attempt.completed_at,
            "time_taken": attempt.time_taken,
            "detailed_results": details,
        }

    @staticmethod
    def get_student_attempts(session: Session, student_id: int) -> List[Attempt]:
        return AttemptCRUD.get_student_attempts(session, student_id)

    @staticmethod
    def calculate_improvement(
        session: Session, student_id: int, test_id_pre: int, test_id_post: int
    ) -> Dict:
        pre_attempts = [a for a in AttemptCRUD.get_student_attempts(session, student_id) if a.test_id == test_id_pre]
        post_attempts = [a for a in AttemptCRUD.get_student_attempts(session, student_id) if a.test_id == test_id_post]
        pre_score = mean([a.score for a in pre_attempts]) if pre_attempts else 0.0
        post_score = mean([a.score for a in post_attempts]) if post_attempts else 0.0
        improvement_abs = post_score - pre_score
        improvement_pct = (improvement_abs / pre_score * 100.0) if pre_score > 0 else 0.0
        return {
            "pre_score": pre_score,
            "post_score": post_score,
            "improvement_pct": improvement_pct,
            "improvement_abs": improvement_abs,
        }
