"""PDF generation utilities using ReportLab.

Generates lightweight PDFs for attempts and test summaries.
"""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Dict, List

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors

from database.models import Attempt, Question, Test


def generate_attempt_summary_pdf(attempt: Attempt, questions: List[Question]) -> bytes:
    """Return a PDF (bytes) summarizing a student's attempt.

    Includes score, completion time, and a table of question outcomes.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    elems: List = []

    title = Paragraph("Attempt Summary", styles["Title"])
    meta = Paragraph(
        f"<b>Attempt ID:</b> {attempt.id} &nbsp;&nbsp; <b>Score:</b> {attempt.score:.1f}%"
        f" &nbsp;&nbsp; <b>Completed:</b> {attempt.completed_at.strftime('%Y-%m-%d %H:%M') if attempt.completed_at else '-'}",
        styles["Normal"],
    )

    elems.extend([title, Spacer(1, 0.4 * cm), meta, Spacer(1, 0.6 * cm)])

    data = [["Q#", "Correct", "Your Answer", "Correct Answer", "Topic", "Difficulty"]]
    answers = {int(k): int(v) for k, v in (attempt.answers or {}).items() if str(k).isdigit()}
    for idx, q in enumerate(questions, start=1):
        sa = answers.get(q.id, None)
        is_correct = sa == q.correct_answer
        data.append(
            [
                str(idx),
                "✅" if is_correct else "❌",
                f"{chr(65 + sa) if sa is not None else '-'}",
                f"{chr(65 + q.correct_answer)}",
                q.topic_tag or "-",
                q.difficulty,
            ]
        )

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0F2F6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )

    elems.append(table)

    doc.build(elems)
    return buf.getvalue()


def generate_test_summary_pdf(test: Test, questions: List[Question]) -> bytes:
    """Return a PDF (bytes) summarizing a test meta and its questions (no answers)."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    y = height - 2 * cm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, y, "Test Summary")
    y -= 1 * cm

    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, y, f"Title: {test.title}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Type: {test.test_type.upper()}  |  Access Key: {test.access_key}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Created: {test.created_at.strftime('%Y-%m-%d %H:%M')}")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Questions:")
    y -= 0.6 * cm

    c.setFont("Helvetica", 10)
    for idx, q in enumerate(questions, start=1):
        if y < 3 * cm:
            c.showPage()
            y = height - 2 * cm
            c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y, f"{idx}. {q.question_text[:90]}")
        y -= 0.4 * cm
        for i, opt in enumerate(q.options):
            c.drawString(2.5 * cm, y, f"{chr(65+i)}) {opt}")
            y -= 0.35 * cm
        y -= 0.2 * cm

    c.showPage()
    c.save()
    return buf.getvalue()
