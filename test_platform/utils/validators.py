"""Input validation utilities using explicit checks.

Avoids leaking sensitive data and provides clear error messages.
"""
from __future__ import annotations

import re
from typing import Any

from .exceptions import ValidationError

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,50}$")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class InputValidator:
    @staticmethod
    def validate_username(username: str) -> str:
        if not isinstance(username, str):
            raise ValidationError("Username must be a string")
        username = username.strip()
        if not USERNAME_RE.fullmatch(username):
            raise ValidationError("Username must be 3-50 chars, alphanumeric or underscore only")
        return username

    @staticmethod
    def validate_email(email: str) -> str:
        if not isinstance(email, str):
            raise ValidationError("Email must be a string")
        email = email.strip()
        if len(email) > 120:
            raise ValidationError("Email must be at most 120 characters")
        if not EMAIL_RE.fullmatch(email):
            raise ValidationError("Invalid email format")
        return email

    @staticmethod
    def validate_password(password: str) -> str:
        if not isinstance(password, str):
            raise ValidationError("Password must be a string")
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", password):
            raise ValidationError("Password must include at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValidationError("Password must include at least one lowercase letter")
        if not re.search(r"[0-9]", password):
            raise ValidationError("Password must include at least one digit")
        return password

    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        if not isinstance(text, str):
            raise ValidationError("Value must be a string")
        text = text.strip()
        # Remove control characters
        text = re.sub(r"[\x00-\x1F\x7F]", "", text)
        if len(text) > max_length:
            raise ValidationError(f"Text must be at most {max_length} characters")
        return text

    @staticmethod
    def validate_integer(value: Any, min_val: int | None = None, max_val: int | None = None) -> int:
        try:
            ivalue = int(value)
        except (TypeError, ValueError):
            raise ValidationError("Value must be an integer")
        if min_val is not None and ivalue < min_val:
            raise ValidationError(f"Value must be >= {min_val}")
        if max_val is not None and ivalue > max_val:
            raise ValidationError(f"Value must be <= {max_val}")
        return ivalue
