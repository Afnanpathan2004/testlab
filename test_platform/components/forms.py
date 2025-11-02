"""Reusable Streamlit form components.

All forms return dict with collected data or None if not submitted/invalid.
"""
from __future__ import annotations

import streamlit as st


def render_test_form() -> dict | None:
    with st.form("create_test_form"):
        title = st.text_input("Title", max_chars=255)
        description = st.text_area("Description (optional)", max_chars=1000)
        test_type = st.selectbox("Test Type", ["pre", "post"], index=0)
        submitted = st.form_submit_button("Create Test", use_container_width=True)
        if submitted:
            if not title or len(title.strip()) < 5:
                st.error("Title must be at least 5 characters")
                return None
            return {
                "title": title.strip(),
                "description": description.strip() if description else None,
                "test_type": test_type,
            }
    return None


def render_question_form() -> dict | None:
    with st.form("add_question_form"):
        question_text = st.text_area("Question", help="Enter the question text", height=120)
        col1, col2 = st.columns(2)
        with col1:
            opt_a = st.text_input("Option A")
            opt_b = st.text_input("Option B")
        with col2:
            opt_c = st.text_input("Option C")
            opt_d = st.text_input("Option D")
        correct_answer = st.selectbox("Correct Answer", [0, 1, 2, 3], format_func=lambda i: ["A", "B", "C", "D"][i])
        difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
        topic_tag = st.text_input("Topic Tag", placeholder="e.g., loops, functions")
        explanation = st.text_area("Explanation", help="<= 1000 chars", height=100)
        submitted = st.form_submit_button("Add Question", use_container_width=True)
        if submitted:
            options = [opt_a.strip(), opt_b.strip(), opt_c.strip(), opt_d.strip()]
            if not question_text or len(question_text.strip()) < 10:
                st.error("Question must be at least 10 characters")
                return None
            if any(not o for o in options):
                st.error("All four options are required")
                return None
            if len(set(options)) != 4:
                st.error("Options must be unique")
                return None
            if not topic_tag:
                st.error("Topic tag is required")
                return None
            if not explanation or len(explanation.strip()) < 5:
                st.error("Explanation must be at least 5 characters")
                return None
            return {
                "question_text": question_text.strip(),
                "options": options,
                "correct_answer": int(correct_answer),
                "difficulty": difficulty,
                "topic_tag": topic_tag.strip(),
                "explanation": explanation.strip(),
            }
    return None


def render_login_form(key: str = "login_form") -> dict | None:
    with st.form(key):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)
        if submitted:
            if not username or not password:
                st.error("Enter username and password")
                return None
            return {"username": username.strip(), "password": password}
    return None


essential_roles = ["teacher", "student"]


def render_register_form() -> dict | None:
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", essential_roles, index=1)
        submitted = st.form_submit_button("Register", use_container_width=True)
        if submitted:
            if not username or not email or not password:
                st.error("Please fill all fields")
                return None
            return {"username": username.strip(), "email": email.strip(), "password": password, "role": role}
    return None
