import streamlit as st

from database import get_db_session
from database.crud import TestCRUD, QuestionCRUD
from database.models import Attempt
from services.test_service import TestService
from services.pdf_service import generate_test_summary_pdf, generate_attempt_summary_pdf
import segno
from io import BytesIO
from components.sidebar import render_sidebar_login

# Always render sidebar login/account first
render_sidebar_login()

# Check auth and stop if not authenticated
if not st.session_state.get("authenticated"):
    st.error("Please login first")
    st.stop()

st.title("📊 Dashboard")

session = get_db_session()

# Show role-specific content
if st.session_state.role == "teacher":
    def render_teacher_dashboard(session):
        st.subheader("Your Tests")
        tests = TestCRUD.get_teacher_tests(session, st.session_state.user_id)

        if tests:
            for test in tests:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{test.title}** ({test.test_type.upper()})")
                    st.caption(f"Key: `{test.access_key}` | {len(test.questions)} questions")
                with col2:
                    status = "✅ Published" if test.is_published else "📋 Draft"
                    st.write(status)
                with col3:
                    with st.popover("⋯", use_container_width=True):
                        with st.form(f"edit_form_{test.id}"):
                            new_title = st.text_input("Title", value=test.title, max_chars=255)
                            new_desc = st.text_area("Description", value=test.description or "", max_chars=1000)
                            new_type = st.selectbox("Type", ["pre", "post"], index=0 if test.test_type=="pre" else 1)
                            c1, c2 = st.columns(2)
                            upd = c1.form_submit_button("Save")
                            del_btn = c2.form_submit_button("Delete", type="secondary")
                        if upd:
                            try:
                                TestService.update_test_metadata(session, test.id, st.session_state.user_id, new_title, new_desc, new_type)
                                st.success("Updated")
                                st.experimental_rerun()
                            except Exception as e:  # noqa: BLE001
                                st.error(str(e))
                        if del_btn:
                            try:
                                TestService.delete_test(session, test.id, st.session_state.user_id)
                                st.success("Deleted")
                                st.experimental_rerun()
                            except Exception as e:  # noqa: BLE001
                                st.error(str(e))
                # PDF download (teacher)
                qlist = QuestionCRUD.get_test_questions(session, test.id)
                pdf_bytes = generate_test_summary_pdf(test, qlist)
                st.download_button(
                    label="📄 Download Test PDF",
                    data=pdf_bytes,
                    file_name=f"test_{test.id}_summary.pdf",
                    mime="application/pdf",
                    key=f"dl_test_{test.id}",
                )
                # Delete button with confirmation
                colA, colB = st.columns(2)
                with colA:
                    if st.button("🗑️ Delete Test", key=f"del_{test.id}"):
                        st.session_state[f"confirm_delete_{test.id}"] = True
                if st.session_state.get(f"confirm_delete_{test.id}"):
                    st.warning("Are you sure you want to delete this test? This cannot be undone.")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Confirm Delete", key=f"confirm_del_{test.id}"):
                            try:
                                TestService.delete_test(session, test.id, st.session_state.user_id)
                                session.commit()
                                st.success("Deleted")
                                st.rerun()
                            except Exception as e:  # noqa: BLE001
                                session.rollback()
                                st.error(str(e))
                    with c2:
                        if st.button("Cancel", key=f"cancel_del_{test.id}"):
                            st.session_state[f"confirm_delete_{test.id}"] = False

                with st.expander("🔗 Share / QR"):
                    # Build shareable join link: base URL + Take Test page + key param
                    default_base = st.session_state.get("share_base_url", "http://localhost:8502")
                    base_url = st.text_input(
                        "Base URL (adjust if different)", value=default_base, key=f"share_base_{test.id}"
                    )
                    # Path to Take Test multipage
                    path = "/4_%F0%9F%93%9D_Take_Test?key=" + test.access_key
                    full_link = base_url.rstrip("/") + path
                    st.write("Share this link:")
                    st.text_input("Link", value=full_link, key=f"share_link_{test.id}")
                    # Generate QR code
                    try:
                        qr = segno.make(full_link)
                        buf = BytesIO()
                        qr.save(buf, kind="png", scale=6)
                        st.image(buf.getvalue(), caption="Scan to join", use_container_width=False)
                        st.download_button(
                            label="⬇️ Download QR (PNG)",
                            data=buf.getvalue(),
                            file_name=f"test_{test.id}_join_qr.png",
                            mime="image/png",
                            key=f"qr_dl_{test.id}",
                        )
                    except Exception as e:  # noqa: BLE001
                        st.warning(f"QR generation failed: {e}")
        else:
            st.info("No tests created yet. Create one to get started!")

    render_teacher_dashboard(session)
else:
    def render_student_dashboard(session):
        st.subheader("Browse Published Tests")
        try:
            tests = (
                session.query(TestCRUD.model)
                .filter(TestCRUD.model.is_published == 1)
                .order_by(TestCRUD.model.created_at.desc())
                .all()
            )
            if not tests:
                st.info("No published tests yet.")
            for t in tests:
                with st.container(border=True):
                    st.write(f"**{t.title}** (Key: `{t.access_key}`)")
                    join_link = f"/4_%F0%9F%93%9D_Take_Test?key={t.access_key}"
                    cols = st.columns(2)
                    with cols[0]:
                        try:
                            st.page_link(join_link, label="Join ➜")
                        except Exception:
                            st.write("Open the Take Test page and paste the key above.")
                    with cols[1]:
                        st.caption(str(t.created_at))
        except Exception as e:  # noqa: BLE001
            st.error(str(e))

        st.markdown("---")
        st.subheader("Recent Results")
        attempts = (
            session.query(Attempt)
            .filter(Attempt.student_id == st.session_state.user_id)
            .order_by(Attempt.created_at.desc())
            .limit(20)
            .all()
        )

        if attempts:
            for attempt in attempts:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{attempt.test.title}**")
                with col2:
                    st.metric("Score", f"{attempt.score:.1f}%")
                with col3:
                    if attempt.completed_at:
                        st.caption(attempt.completed_at.strftime("%m/%d/%Y"))
                    else:
                        st.caption("In progress")
                # Attempt PDF
                if attempt.completed_at:
                    qlist = QuestionCRUD.get_test_questions(session, attempt.test_id)
                    a_pdf = generate_attempt_summary_pdf(attempt, qlist)
                    st.download_button(
                        label="📄 Download Attempt PDF",
                        data=a_pdf,
                        file_name=f"attempt_{attempt.id}.pdf",
                        mime="application/pdf",
                        key=f"dl_attempt_{attempt.id}",
                    )
        else:
            st.info("No tests taken yet.")

    render_student_dashboard(session)

session.close()
