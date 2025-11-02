import streamlit as st

from database import get_db_session
from database.crud import QuestionCRUD
from database.models import Test
from services.test_service import TestService
from components.forms import render_test_form, render_question_form

# Auth check
if not st.session_state.get("authenticated"):
    st.error("Please login")
    st.stop()

if st.session_state.role != "teacher":
    st.error("Only teachers can create tests")
    st.stop()

st.title("✏️ Create Test")

# Initialize session state
if "current_test_id" not in st.session_state:
    st.session_state.current_test_id = None

session = get_db_session()

# Two-step process: Create test, then add questions
if st.session_state.current_test_id is None:
    # Step 1: Create test
    test_data = render_test_form()
    if test_data:
        try:
            test = TestService.create_test(
                session,
                st.session_state.user_id,
                test_data['title'],
                test_data['description'],
                test_data['test_type']
            )
            st.session_state.current_test_id = test.id
            st.success(f"Test created! Access Key: `{test.access_key}`")
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(f"Error: {str(e)}")
else:
    # Step 2: Add questions
    test = session.query(Test).filter(Test.id == st.session_state.current_test_id).first()
    if not test:
        st.error("Test not found. It may have been deleted.")
        st.session_state.current_test_id = None
        st.stop()

    st.write(f"**Test:** {test.title}")

    # Show existing questions
    questions = QuestionCRUD.get_test_questions(session, test.id)

    if questions:
        st.subheader(f"Questions: {len(questions)}")
        for i, q in enumerate(questions):
            with st.expander(f"Q{i+1}: {q.question_text[:50]}..."):
                st.write(q.question_text)
                for j, opt in enumerate(q.options):
                    marker = "✓" if j == q.correct_answer else "○"
                    st.write(f"{marker} {chr(65+j)}) {opt}")
                st.caption(f"Difficulty: {q.difficulty} | Topic: {q.topic_tag}")

    # Add new question
    st.subheader("Add Question")
    question_data = render_question_form()
    if question_data:
        try:
            TestService.add_question(
                session,
                test.id,
                question_data['question_text'],
                question_data['options'],
                question_data['correct_answer'],
                question_data['explanation'],
                question_data['topic_tag'],
                question_data['difficulty'],
                len(questions)
            )
            st.success("Question added!")
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(f"Error: {str(e)}")

    # Publish button
    st.markdown("---")
    if st.button("📤 Publish Test", use_container_width=True):
        if len(questions) < 1:
            st.error("Add at least 1 question")
        else:
            try:
                TestService.publish_test(session, test.id, st.session_state.user_id)
                st.success("Test published!")
                st.session_state.current_test_id = None
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"Error: {str(e)}")

session.close()
