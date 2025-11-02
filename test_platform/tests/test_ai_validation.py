from __future__ import annotations

import pytest

from services.ai_service import AIService
from utils.exceptions import ValidationError


def test_validate_questions_happy_path():
    data = [
        {
            "stem": "What is Python? (ten chars)",
            "options": ["Snake", "Language", "Car", "City"],
            "correct": 1,
            "explanation": "It is a programming language.",
            "topic_tag": "intro",
            "difficulty": "easy",
        }
        for _ in range(5)
    ]
    out = AIService._validate_questions(data, expected_count=5)
    assert isinstance(out, list)
    assert len(out) >= 4  # 80% threshold


def test_validate_questions_invalid_raises():
    data = [
        {
            "stem": "short",
            "options": ["A", "A", "C", "D"],
            "correct": 5,
            "explanation": "ok",
            "topic_tag": "",
            "difficulty": "invalid",
        }
        for _ in range(5)
    ]
    with pytest.raises(ValidationError):
        AIService._validate_questions(data, expected_count=5)
