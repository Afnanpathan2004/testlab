import streamlit as st
import pandas as pd

from config.settings import settings
from database import get_db_session
from database.crud import TestCRUD, UserCRUD, QuestionCRUD, AttemptCRUD
from database.models import User, Test, Question, Attempt
from utils.security import allow_action

ADMIN_STATE_KEY = "is_admin"


def _ensure_admin_state():
    if ADMIN_STATE_KEY not in st.session_state:
        st.session_state[ADMIN_STATE_KEY] = False


_ensure_admin_state()

st.set_page_config(page_title="Admin Panel", page_icon="🛡️", layout="wide")

st.title("🛡️ Admin Panel")

# Gate with password if not already validated
if not st.session_state[ADMIN_STATE_KEY]:
    with st.form("admin_login_form"):
        st.info("Admin access required")
        pwd = st.text_input("Admin Password", type="password")
        submit = st.form_submit_button("Enter")
        if submit:
            if not allow_action("admin_login", limit_per_minute=10):
                st.error("Too many attempts. Please wait a minute.")
            elif pwd == settings.admin_password:
                st.session_state[ADMIN_STATE_KEY] = True
                st.success("Admin access granted")
                st.rerun()
            else:
                st.error("Invalid admin password")
    st.stop()

# Admin content
with st.sidebar:
    if st.button("🔒 Exit Admin", use_container_width=True):
        st.session_state[ADMIN_STATE_KEY] = False
        st.rerun()

session = get_db_session()

st.subheader("Overview")
col1, col2, col3, col4 = st.columns(4)
try:
    users_count = session.query(User).count()
    tests_count = session.query(Test).count()
    questions_count = session.query(Question).count()
    attempts_count = session.query(Attempt).count()
    col1.metric("Users", users_count)
    col2.metric("Tests", tests_count)
    col3.metric("Questions", questions_count)
    col4.metric("Attempts", attempts_count)
except Exception as e:  # noqa: BLE001
    st.error(f"Failed to load overview: {e}")

st.markdown("---")

# Tabs for data views
tab_users, tab_tests, tab_questions, tab_attempts = st.tabs(["Users", "Tests", "Questions", "Attempts"]) 

with tab_users:
    st.caption("All users")
    try:
        df = pd.read_sql_query("SELECT id, username, email, role, is_active, created_at FROM users ORDER BY id", session.bind)
        st.dataframe(df, use_container_width=True)
    except Exception as e:  # noqa: BLE001
        st.error(str(e))

with tab_tests:
    st.caption("All tests")
    try:
        df = pd.read_sql_query(
            "SELECT id, title, teacher_id, test_type, access_key, is_published, created_at FROM tests ORDER BY id",
            session.bind,
        )
        st.dataframe(df, use_container_width=True)
        st.markdown("### Quick Actions")
        with st.form("test_actions_form"):
            test_id = st.number_input("Test ID", min_value=1, step=1)
            action = st.selectbox("Action", ["Publish", "Unpublish", "Delete"], index=0)
            submit = st.form_submit_button("Apply")
            if submit:
                try:
                    if action == "Publish":
                        TestCRUD.update(session, int(test_id), {"is_published": 1})
                        st.success("Published")
                    elif action == "Unpublish":
                        TestCRUD.update(session, int(test_id), {"is_published": 0})
                        st.success("Unpublished")
                    else:
                        ok = TestCRUD.delete(session, int(test_id))
                        st.success("Deleted" if ok else "Not found")
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(str(e))
    except Exception as e:  # noqa: BLE001
        st.error(str(e))

with tab_questions:
    st.caption("All questions (first 500)")
    try:
        df = pd.read_sql_query(
            'SELECT id, test_id, difficulty, topic_tag, "order" AS position, created_at FROM questions ORDER BY id LIMIT 500',
            session.bind,
        )
        st.dataframe(df, use_container_width=True)
        with st.form("question_delete_form"):
            qid = st.number_input("Question ID to delete", min_value=1, step=1)
            submit = st.form_submit_button("Delete")
            if submit:
                try:
                    ok = QuestionCRUD.delete(session, int(qid))
                    st.success("Deleted" if ok else "Not found")
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(str(e))
    except Exception as e:  # noqa: BLE001
        st.error(str(e))

with tab_attempts:
    st.caption("All attempts (first 500)")
    try:
        df = pd.read_sql_query(
            "SELECT id, test_id, student_id, score, is_submitted, completed_at FROM attempts ORDER BY id DESC LIMIT 500",
            session.bind,
        )
        st.dataframe(df, use_container_width=True)
    except Exception as e:  # noqa: BLE001
        st.error(str(e))

session.close()
