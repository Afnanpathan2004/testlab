import streamlit as st

from database import get_db_session
from services.ai_service import AIService
from services.test_service import TestService
from utils.security import allow_action
import streamlit as st

# Auth and teacher check
if not st.session_state.get("authenticated"):
    st.error("Please login")
    st.stop()

if st.session_state.role != "teacher":
    st.error("Only teachers can generate questions")
    st.stop()

st.title("🤖 AI Question Generator")

# Initialize state for saved test and generated questions
if "saved_test_for_publish" not in st.session_state:
    st.session_state.saved_test_for_publish = None
if "generated_questions" not in st.session_state:
    st.session_state.generated_questions = None
if "generated_test_title" not in st.session_state:
    st.session_state.generated_test_title = None

# Form for generation
with st.form("ai_generate"):
    topic = st.text_input("Topic", placeholder="e.g., Python Functions")
    syllabus = st.text_area("Syllabus/Content", placeholder="Describe content scope...")
    num_questions = st.slider("Number of Questions", 1, 20, 5)
    difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
    language = st.selectbox("Language", ["english", "marathi", "hindi"], index=0)
    test_title = st.text_input("Test Title")

    submit = st.form_submit_button("🚀 Generate", use_container_width=True)

if submit:
    if not all([topic, syllabus, test_title]):
        st.error("Fill all required fields")
    else:
        if not allow_action("ai_generate", limit_per_minute=10):
            st.error("Too many generate requests. Please wait and try again.")
        else:
            with st.spinner("Generating questions..."):
                try:
                    questions = AIService.generate_questions(topic, syllabus, int(num_questions), difficulty, language)
                    
                    # Store in session state
                    st.session_state.generated_questions = questions
                    st.session_state.generated_test_title = test_title
                    st.success(f"✅ Generated {len(questions)} questions!")
                    st.rerun()

                except Exception as e:  # noqa: BLE001
                    st.error(f"Generation failed: {str(e)}")

# Display generated questions and save button (outside form)
if st.session_state.generated_questions:
    st.markdown("---")
    st.subheader("Generated Questions")
    
    questions = st.session_state.generated_questions
    test_title = st.session_state.generated_test_title
    
    # Display questions
    for i, q in enumerate(questions):
        with st.expander(f"Q{i+1}: {q['stem'][:60]}...", expanded=False):
            st.write(q['stem'])
            st.write("**Options:**")
            for j, opt in enumerate(q['options']):
                marker = "✓" if j == q['correct'] else "○"
                st.write(f"{marker} {chr(65+j)}) {opt}")
            st.write(f"**Explanation:** {q['explanation']}")
            st.write(f"**Difficulty:** {q['difficulty']}")
    
    # Save button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save as Test", type="primary", use_container_width=True):
            if not allow_action("ai_save_test", limit_per_minute=5):
                st.error("Rate limit reached. Please wait before saving again.")
            else:
                session = get_db_session()
                try:
                    # Create test as PRE (single-test workflow)
                    test = TestService.create_test(
                        session, st.session_state.user_id, test_title, "", "pre"
                    )
                    st.caption(f"Created test id={test.id} key={test.access_key}")

                    # Add questions with diagnostics
                    added = 0
                    for i, q in enumerate(questions):
                        try:
                            TestService.add_question(
                                session,
                                test.id,
                                q['stem'],
                                q['options'],
                                q['correct'],
                                q['explanation'],
                                q['topic_tag'],
                                q['difficulty'],
                                i,
                            )
                            added += 1
                        except Exception as qe:  # noqa: BLE001
                            session.rollback()
                            st.error(
                                "Failed to add question #{idx}: {err}\nSnippet: {snip}".format(
                                    idx=i + 1,
                                    err=f"{type(qe).__name__}: {qe}",
                                    snip=str({k: q.get(k) for k in ['stem','options','correct','topic_tag','difficulty']})[:400],
                                )
                            )
                            st.stop()

                    # Ensure persistence
                    session.commit()
                    st.success(f"✅ Test saved! Questions added: {added}. Access Key: `{test.access_key}`")
                    
                    # Store in session state for publish step
                    st.session_state.saved_test_for_publish = {
                        "id": test.id,
                        "key": test.access_key,
                        "title": test_title
                    }
                    # Clear generated questions
                    st.session_state.generated_questions = None
                    st.session_state.generated_test_title = None
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    import traceback
                    session.rollback()
                    st.error(f"Error while saving test: {type(e).__name__}: {e}")
                    st.exception(traceback.format_exc())
                finally:
                    session.close()
    
    with col2:
        if st.button("🔄 Generate New", use_container_width=True):
            st.session_state.generated_questions = None
            st.session_state.generated_test_title = None
            st.rerun()

# Show publish button if test was saved
if st.session_state.saved_test_for_publish:
    st.markdown("---")
    saved = st.session_state.saved_test_for_publish
    st.success(f"✅ Test '{saved['title']}' is saved (Key: `{saved['key']}`)")
    st.info("📢 Publish it to make it visible to students on the Dashboard.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Publish and go to Dashboard", type="primary", use_container_width=True):
            session = get_db_session()
            try:
                TestService.publish_test(session, saved["id"], st.session_state.user_id)
                session.commit()
                st.session_state.saved_test_for_publish = None  # Clear
                st.success("Published!")
                st.switch_page("pages/1_📊_Dashboard.py")
            except Exception as e:  # noqa: BLE001
                import traceback
                session.rollback()
                st.error(f"Publish failed: {e}")
                st.exception(traceback.format_exc())
            finally:
                session.close()
    
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.saved_test_for_publish = None
            st.rerun()
