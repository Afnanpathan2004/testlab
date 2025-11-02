from __future__ import annotations

import pytest

from utils.validators import InputValidator
from utils.exceptions import ValidationError


def test_validate_username_ok():
    assert InputValidator.validate_username("user_123") == "user_123"


def test_validate_username_bad():
    with pytest.raises(ValidationError):
        InputValidator.validate_username("x")


def test_validate_email_ok():
    assert InputValidator.validate_email("a@b.com") == "a@b.com"


def test_validate_email_bad():
    with pytest.raises(ValidationError):
        InputValidator.validate_email("not-an-email")


def test_validate_password_strength_ok():
    assert InputValidator.validate_password("Strong123") == "Strong123"


def test_validate_password_strength_bad():
    with pytest.raises(ValidationError):
        InputValidator.validate_password("weak")
