"""Authentication and session management services."""
from __future__ import annotations

import secrets
import string
from datetime import datetime
from typing import Optional, Tuple

import bcrypt
import streamlit as st
from sqlalchemy.orm import Session

from database.crud import UserCRUD
from database.models import User
from utils.exceptions import AuthenticationError, ValidationError
from utils.logger import setup_logger
from utils.validators import InputValidator

logger = setup_logger(__name__)


class Authenticator:
    @staticmethod
    def hash_password(password: str) -> str:
        InputValidator.validate_password(password)
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hash_value: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hash_value.encode("utf-8"))
        except Exception:
            return False

    @staticmethod
    def generate_access_key(length: int = 8) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def register_user(session: Session, username: str, email: str, password: str, role: str) -> User:
        username = InputValidator.validate_username(username)
        email = InputValidator.validate_email(email)
        InputValidator.validate_password(password)
        if role not in {"teacher", "student"}:
            raise ValidationError("Role must be 'teacher' or 'student'")

        if UserCRUD.get_by_username(session, username):
            raise ValidationError("Username already exists")
        if UserCRUD.get_by_email(session, email):
            raise ValidationError("Email already exists")

        pwd_hash = Authenticator.hash_password(password)
        user = UserCRUD.create(
            session,
            {
                "username": username,
                "email": email,
                "password_hash": pwd_hash,
                "role": role,
                "is_active": 1,
            },
        )
        logger.info("User registered username=%s role=%s", username, role)
        return user

    @staticmethod
    def login_user(session: Session, username: str, password: str) -> Tuple[bool, Optional[User]]:
        user = UserCRUD.get_by_username(session, username)
        if not user:
            logger.warning("Login failed: user not found username=%s", username)
            return False, None
        if not user.is_active:
            logger.warning("Login failed: inactive user username=%s", username)
            return False, None
        if not Authenticator.verify_password(password, user.password_hash):
            logger.warning("Login failed: invalid password username=%s", username)
            return False, None
        logger.info("Login success username=%s", username)
        return True, user


class SessionManager:
    @staticmethod
    def initialize_session() -> None:
        defaults = {
            "authenticated": False,
            "user_id": None,
            "username": None,
            "role": None,
            "login_time": None,
            "current_test_id": None,
            "current_answers": {},
            "current_attempt_id": None,
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

    @staticmethod
    def login(user_id: int, username: str, role: str) -> None:
        st.session_state.authenticated = True
        st.session_state.user_id = user_id
        st.session_state.username = username
        st.session_state.role = role
        st.session_state.login_time = datetime.now()
        logger.info("User logged in username=%s role=%s", username, role)

    @staticmethod
    def logout() -> None:
        keep = {"authenticated": False}
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        for k, v in keep.items():
            st.session_state[k] = v
        logger.info("User logged out")

    @staticmethod
    def is_authenticated() -> bool:
        return bool(st.session_state.get("authenticated", False))
