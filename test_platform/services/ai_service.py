"""AI question generation using Groq (preferred) or OpenAI as fallback."""
from __future__ import annotations

import json
import re
import time
from typing import Dict, List

from typing import Optional

from groq import Groq
from openai import OpenAI

from config.settings import settings
from utils.exceptions import ValidationError
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AIService:
    @staticmethod
    def generate_questions(
        topic: str,
        syllabus: str,
        num_questions: int = 5,
        difficulty: str = "medium",
        language: str = "english",
        max_retries: int = 3,
    ) -> List[Dict]:
        topic = topic.strip()
        syllabus = syllabus.strip()
        if not topic or not syllabus:
            raise ValidationError("Topic and syllabus are required")
        if difficulty not in {"easy", "medium", "hard"}:
            raise ValidationError("Invalid difficulty. Choose easy, medium, or hard")
        if not (1 <= num_questions <= 20):
            raise ValidationError("num_questions must be between 1 and 20")
        language = language.strip().lower()
        if language not in {"english", "marathi", "hindi"}:
            raise ValidationError("language must be one of: english, marathi, hindi")
        prompt = AIService._create_prompt(topic, syllabus, num_questions, difficulty, language)

        # Prefer Groq if available, else OpenAI
        use_groq = bool(settings.groq_api_key)
        groq_client: Optional[Groq] = Groq(api_key=settings.groq_api_key) if use_groq else None
        openai_client: Optional[OpenAI] = None
        if not use_groq:
            if not settings.openai_api_key:
                raise ValidationError("AI provider not configured. Set GROQ_API_KEY or OPENAI_API_KEY in .env")
            openai_client = OpenAI(api_key=settings.openai_api_key)

        last_err: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info("AI generate request attempt=%s provider=%s topic=%s n=%s diff=%s", attempt, "groq" if use_groq else "openai", topic, num_questions, difficulty)

                if use_groq and groq_client is not None:
                    resp = groq_client.chat.completions.create(
                        model=settings.groq_model,
                        messages=[
                            {"role": "system", "content": "You are an expert assessment designer."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.4,
                        max_tokens=1500,
                    )
                    content = resp.choices[0].message.content or ""
                else:
                    assert openai_client is not None
                    resp = openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an expert assessment designer."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.4,
                        max_tokens=1500,
                    )
                    content = resp.choices[0].message.content or ""
                # Normalize and extract JSON
                content = content.strip()
                if content.startswith("```"):
                    # Remove optional fenced code blocks
                    content = content.strip("`\n ")
                    if content.lower().startswith("json"):
                        content = content[4:].strip()
                # Try direct parse first
                try:
                    data = json.loads(content)
                except Exception:
                    # Fallback: extract first JSON array substring
                    match = re.search(r"\[.*\]", content, flags=re.DOTALL)
                    if not match:
                        raise ValidationError("Provider returned non-JSON content. Please try again.")
                    data = json.loads(match.group(0))
                questions = AIService._validate_questions(data, num_questions)
                logger.info("AI generate success count=%s", len(questions))
                return questions
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                wait = 2 ** (attempt - 1)
                logger.warning("AI generate failed attempt=%s error=%s; retrying in %ss", attempt, exc, wait)
                time.sleep(wait)
        logger.error("AI generation failed after retries: %s", last_err)
        # Surface a concise provider error message if available
        raise ValidationError(f"Failed to generate questions: {last_err}")

    @staticmethod
    def _create_prompt(topic: str, syllabus: str, num_questions: int, difficulty: str, language: str) -> str:
        return (
            "You are an expert assessment designer.\n"
            + "Generate exactly "
            + str(num_questions)
            + " multiple-choice questions on the topic '"
            + topic
            + "' based on the following syllabus/context: \n"
            + syllabus
            + "\n\n"
            + "Requirements: Each question must have a clear stem (min 10 words), exactly 4 options, the index of the correct option (0-3), an explanation, a topic_tag, and difficulty='"
            + difficulty
            + "'. Write ALL content strictly in this language: "
            + language
            + ".\n"
            + "Return ONLY valid JSON (no commentary or backticks): an array of objects with keys: stem, options (array of 4 strings), correct (0-3), explanation, topic_tag, difficulty."
        )

    @staticmethod
    def _validate_questions(questions: object, expected_count: int) -> List[Dict]:
        if not isinstance(questions, list):
            raise ValidationError("AI response must be a JSON list")
        valid: List[Dict] = []
        for i, q in enumerate(questions, start=1):
            try:
                if not isinstance(q, dict):
                    raise ValueError("Item must be an object")
                stem = q.get("stem")
                options = q.get("options")
                correct = q.get("correct")
                explanation = q.get("explanation")
                topic_tag = q.get("topic_tag")
                difficulty = q.get("difficulty")
                if not isinstance(stem, str) or len(stem.strip()) < 10:
                    raise ValueError("Invalid stem")
                if not isinstance(options, list) or len(options) != 4:
                    raise ValueError("Options must be list of 4")
                if len({o.strip() for o in options if isinstance(o, str)}) != 4:
                    raise ValueError("Options must be unique strings")
                if not isinstance(correct, int) or not (0 <= correct <= 3):
                    raise ValueError("Correct must be 0-3 integer")
                if not isinstance(explanation, str) or len(explanation.strip()) < 5:
                    raise ValueError("Invalid explanation")
                if not isinstance(topic_tag, str) or not topic_tag.strip():
                    raise ValueError("Invalid topic_tag")
                if difficulty not in {"easy", "medium", "hard"}:
                    raise ValueError("Invalid difficulty")
                valid.append(
                    {
                        "stem": stem.strip(),
                        "options": [str(o).strip() for o in options],
                        "correct": correct,
                        "explanation": explanation.strip(),
                        "topic_tag": topic_tag.strip(),
                        "difficulty": difficulty,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Invalid AI question idx=%s error=%s", i, exc)
        if len(valid) < max(1, int(0.8 * expected_count)):
            raise ValidationError("Too many invalid questions in AI output")
        return valid
