from __future__ import annotations

import streamlit as st

from auth.authenticator import Authenticator, SessionManager
from database import get_db_session
from components.forms import render_login_form
from utils.logger import setup_logger

logger = setup_logger(__name__)


def render_sidebar_login() -> None:
    """Render a compact login form in the sidebar when not authenticated."""
    with st.sidebar:
        if not st.session_state.get("authenticated"):
            st.markdown("### 🔑 Login")
            data = render_login_form(key="login_form_sidebar")
            if data:
                session = get_db_session()
                try:
                    ok, user = Authenticator.login_user(session, data["username"], data["password"])
                    if not ok or not user:
                        st.error("Invalid credentials")
                    else:
                        SessionManager.login(user.id, user.username, user.role)
                        st.success("Logged in")
                        st.rerun()
                except Exception as exc:  # noqa: BLE001
                    logger.error("Sidebar login error: %s", exc)
                    st.error("Login failed")
                finally:
                    session.close()
            # Link to open the full login/register page
            try:
                st.page_link("app.py", label="Open full login/register page")
            except Exception:
                pass
        else:
            # Authenticated: show user info and logout
            st.markdown("### 👤 Account")
            st.write(f"**User:** {st.session_state.get('username', '-')}")
            role = (st.session_state.get('role') or '').upper()
            if role:
                st.write(f"**Role:** {role}")
            if st.button("🚪 Logout", use_container_width=True, key="sidebar_logout_btn"):
                SessionManager.logout()
                st.rerun()
