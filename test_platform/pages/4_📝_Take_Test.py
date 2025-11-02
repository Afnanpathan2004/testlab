import streamlit as st

from database import get_db_session
from services.attempt_service import AttemptService
from services.test_service import TestService

# Auth check
if not st.session_state.get("authenticated"):
    st.error("Please login")
    st.stop()

st.title("📝 Take Test")

# Ensure required session keys exist
if "current_test_id" not in st.session_state:
    st.session_state.current_test_id = None
if "current_answers" not in st.session_state:
    st.session_state.current_answers = {}

session = get_db_session()

# Helpers
TEST_INFO_KEY = "current_test_info"


def set_test_info(info: dict) -> None:
    st.session_state[TEST_INFO_KEY] = info


def get_test_info_from_session() -> dict | None:
    return st.session_state.get(TEST_INFO_KEY)


# Deep-link: auto-start if ?key=ACCESSKEY is present and no active test
try:
    qp = st.query_params
    deep_key = None
    if isinstance(qp, dict):
        deep_key = qp.get("key") if isinstance(qp.get("key"), str) else (qp.get("key")[0] if qp.get("key") else None)
    if deep_key and st.session_state.current_test_id is None:
        test = TestService.get_test_by_key(session, deep_key)
        test_info = AttemptService.start_attempt(session, test.id, st.session_state.user_id)
        st.session_state.current_test_id = test_info["test_id"]
        st.session_state.current_answers = {}
        set_test_info(test_info)
        st.success("Test started from link. Good luck!")
except Exception:
    pass

# Step 1: Enter access key
if st.session_state.current_test_id is None:
    with st.form("access_form"):
        # Prefill from query param if available
        default_key = deep_key.upper() if 'deep_key' in locals() and deep_key else ""
        access_key = st.text_input("Test Access Key", value=default_key, placeholder="8-character code").strip().upper()
        student_name = st.text_input("Your Name", value=st.session_state.username)
        submit = st.form_submit_button("Start Test")

        if submit:
            if not access_key or not student_name:
                st.error("Fill all fields")
            else:
                try:
                    test = TestService.get_test_by_key(session, access_key)
                    test_info = AttemptService.start_attempt(session, test.id, st.session_state.user_id)
                    st.session_state.current_test_id = test_info["test_id"]
                    st.session_state.current_answers = {}
                    set_test_info(test_info)
                    st.success("Test started. Good luck!")
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(f"Error: {str(e)}")

# Step 2: Take test
else:
    test_info = get_test_info_from_session()
    if not test_info:
        st.error("Test session expired. Please re-enter the access key.")
        st.session_state.current_test_id = None
        st.stop()

    # Display test header
    st.subheader(test_info['test_title'])

    # Progress bar
    answered = len([a for a in st.session_state.current_answers.values() if a is not None])
    total = test_info['questions_count']
    st.progress(answered / total if total > 0 else 0)
    st.write(f"Progress: {answered}/{total}")

    # Display questions
    for q in test_info['questions']:
        st.markdown(f"**Q{q['id']}: {q['question_text']}**")
        selected = st.radio(
            label=f"Select answer for Q{q['id']}",
            options=[0, 1, 2, 3],
            format_func=lambda i, opts=q['options']: f"{chr(65+i)}) {opts[i]}",
            key=f"q_{q['id']}",
        )
        st.session_state.current_answers[q['id']] = int(selected)
        st.markdown("---")

    # Submit button
    if st.button("✅ Submit Test", use_container_width=True):
        if len(st.session_state.current_answers) != total:
            st.error("Answer all questions")
        else:
            try:
                attempt = AttemptService.submit_attempt(
                    session, test_info['test_id'], st.session_state.user_id, st.session_state.current_answers
                )

                # Store attempt id for results page
                st.session_state.current_attempt_id = attempt.id

                st.success(f"Score: {attempt.score:.1f}%")
                st.balloons()

                st.info("View detailed results on the '📄 Attempt Results' page in the sidebar.")

                # Clear test-taking session state
                st.session_state.current_test_id = None
                st.session_state.current_answers = {}
                if TEST_INFO_KEY in st.session_state:
                    del st.session_state[TEST_INFO_KEY]

            except Exception as e:  # noqa: BLE001
                st.error(f"Error: {str(e)}")

session.close()
