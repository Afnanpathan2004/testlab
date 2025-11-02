import streamlit as st
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Test Platform",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import after page config
from config.settings import settings  # noqa: E402
from database import get_db_session  # noqa: E402
from auth.authenticator import Authenticator, SessionManager  # noqa: E402
from utils.logger import setup_logger  # noqa: E402
from components.forms import render_login_form, render_register_form  # noqa: E402
from utils.security import allow_action  # noqa: E402
from utils.exceptions import ValidationError, AuthenticationError  # noqa: E402
from components.sidebar import render_sidebar_login  # noqa: E402

logger = setup_logger(__name__)


def main() -> None:
    # Initialize session
    SessionManager.initialize_session()

    # Check authentication
    # Offer sidebar login always when not authenticated
    render_sidebar_login()
    if not st.session_state.authenticated:
        render_auth_page()
    else:
        render_main_app()


def render_auth_page() -> None:
    st.title("🔐 Test Assessment Platform")

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

    with tab1:
        render_login_tab()

    with tab2:
        render_register_tab()


def render_login_tab() -> None:
    data = render_login_form()
    if not data:
        return
    session = get_db_session()
    try:
        if not allow_action("login", limit_per_minute=10):
            st.error("Too many login attempts. Please wait a minute and try again.")
            return
        ok, user = Authenticator.login_user(session, data["username"], data["password"])
        if not ok or not user:
            st.error("Invalid credentials")
            return
        SessionManager.login(user.id, user.username, user.role)
        st.success("Logged in successfully")
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        logger.error("Login error: %s", exc)
        st.error("Login failed. Please try again.")
    finally:
        session.close()


def render_register_tab() -> None:
    data = render_register_form()
    if not data:
        return
    session = get_db_session()
    try:
        if not allow_action("register", limit_per_minute=5):
            st.error("Too many registrations from this session. Please wait and try again.")
            return
        user = Authenticator.register_user(
            session, data["username"], data["email"], data["password"], data["role"]
        )
        st.success("Registration successful. Please login.")
    except ValidationError as ve:
        st.error(str(ve))
    except Exception as exc:  # noqa: BLE001
        logger.error("Registration error: %s", exc)
        st.error("Registration failed. Please check inputs and try again.")
    finally:
        session.close()


def render_main_app() -> None:
    # Sidebar with user info and logout
    with st.sidebar:
        st.write(f"**User:** {st.session_state.username}")
        st.write(f"**Role:** {st.session_state.role.upper()}")
        st.markdown("---")

        if st.button("🚪 Logout", use_container_width=True):
            SessionManager.logout()
            st.rerun()

    # Main title and stats
    st.title(f"Welcome, {st.session_state.username}! 👋")
    st.write("Use the sidebar pages to navigate.")


if __name__ == "__main__":
    main()
