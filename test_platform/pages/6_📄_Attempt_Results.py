import streamlit as st

from database import get_db_session
from services.attempt_service import AttemptService
from database.crud import QuestionCRUD, AttemptCRUD
from services.pdf_service import generate_attempt_summary_pdf

# Auth check
if not st.session_state.get("authenticated"):
    st.error("Please login")
    st.stop()

st.title("📄 Attempt Results")

session = get_db_session()

attempt_id = st.session_state.get("current_attempt_id")
if attempt_id is None:
    st.info("No attempt selected.")
    session.close()
    st.stop()

try:
    # Verify ownership inside service call
    results = AttemptService.get_attempt_results(session, attempt_id, st.session_state.user_id)
    st.subheader(f"Score: {results['score']:.1f}%")
    if results.get("completed_at"):
        st.caption(f"Completed: {results['completed_at']}")

    # PDF download
    attempt = AttemptCRUD.get_by_id(session, attempt_id)
    qlist = QuestionCRUD.get_test_questions(session, attempt.test_id)
    pdf_bytes = generate_attempt_summary_pdf(attempt, qlist)
    st.download_button(
        label="📄 Download PDF",
        data=pdf_bytes,
        file_name=f"attempt_{attempt_id}.pdf",
        mime="application/pdf",
    )

    st.markdown("---")
    st.subheader("Detailed Results")
    for item in results["detailed_results"]:
        with st.expander(f"Q{item['question_id']}: {'✅' if item['is_correct'] else '❌'}"):
            st.write(item["question_text"])
            for i, opt in enumerate(item["options"]):
                marker = "✓" if i == item["correct_answer"] else ("→" if i == item.get("student_answer") else " ")
                st.write(f"{marker} {chr(65+i)}) {opt}")
            st.caption(f"Topic: {item['topic']} | Explanation: {item['explanation']}")

except Exception as e:  # noqa: BLE001
    st.error(str(e))
finally:
    session.close()
