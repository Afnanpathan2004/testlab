from __future__ import annotations

from database.crud import AttemptCRUD, QuestionCRUD
from database.models import Test, User, Question


def test_attempt_scoring_full_marks(db_session):
    # Arrange: user, test, 2 questions
    teacher = User(username="teach", email="t@e.com", password_hash="x", role="teacher", is_active=1)
    student = User(username="stud", email="s@e.com", password_hash="x", role="student", is_active=1)
    db_session.add_all([teacher, student])
    db_session.commit()

    test = Test(title="Sample", description="", teacher_id=teacher.id, test_type="pre", access_key="ABCDEFGH", is_published=1)
    db_session.add(test)
    db_session.commit()

    q1 = Question(test_id=test.id, question_text="Q1 text long enough", options=["a","b","c","d"], correct_answer=1, explanation="ex", topic_tag="t", difficulty="easy", order=0)
    q2 = Question(test_id=test.id, question_text="Q2 text long enough", options=["a","b","c","d"], correct_answer=2, explanation="ex", topic_tag="t", difficulty="easy", order=1)
    db_session.add_all([q1, q2])
    db_session.commit()

    answers = {q1.id: 1, q2.id: 2}

    # Act
    attempt = AttemptCRUD.create(db_session, test.id, student.id, answers)

    # Assert
    assert round(attempt.score, 1) == 100.0


def test_attempt_scoring_half(db_session):
    teacher = User(username="teach2", email="t2@e.com", password_hash="x", role="teacher", is_active=1)
    student = User(username="stud2", email="s2@e.com", password_hash="x", role="student", is_active=1)
    db_session.add_all([teacher, student])
    db_session.commit()

    test = Test(title="Sample2", description="", teacher_id=teacher.id, test_type="pre", access_key="ABCDEFG2", is_published=1)
    db_session.add(test)
    db_session.commit()

    q1 = Question(test_id=test.id, question_text="Q1 text long enough", options=["a","b","c","d"], correct_answer=1, explanation="ex", topic_tag="t", difficulty="easy", order=0)
    q2 = Question(test_id=test.id, question_text="Q2 text long enough", options=["a","b","c","d"], correct_answer=2, explanation="ex", topic_tag="t", difficulty="easy", order=1)
    db_session.add_all([q1, q2])
    db_session.commit()

    answers = {q1.id: 1, q2.id: 0}

    attempt = AttemptCRUD.create(db_session, test.id, student.id, answers)

    assert round(attempt.score, 1) == 50.0
