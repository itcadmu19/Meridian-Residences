"""
Renders a generated AgreementDocument's `content` as a PDF - secondary/
optional per the feature spec. Mirrors lease_agreement_pdf.py's reportlab
setup exactly; PostgreSQL (the `content` column) stays the source of
truth, this is generated on demand and nothing new is stored.
"""

from __future__ import annotations

from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

BRAND_COLOR = colors.HexColor("#2f5233")
MUTED_COLOR = colors.HexColor("#6d716a")


def generate_agreement_document_pdf(document, lease) -> bytes:
    unit = lease.unit

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "MeridianTitle", parent=styles["Title"], textColor=BRAND_COLOR, fontSize=20, spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        "MeridianSubtitle", parent=styles["Normal"], textColor=MUTED_COLOR, fontSize=10, spaceAfter=14
    )
    body_style = ParagraphStyle("MeridianBody", parent=styles["Normal"], fontSize=10, leading=15, spaceAfter=10)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        title=f"Lease Agreement Draft - {unit.unit_number}",
    )

    story = [
        Paragraph("MERIDIAN RESIDENCES", title_style),
        Paragraph(f"Lease Agreement · Unit {unit.unit_number} · Version {document.version}", subtitle_style),
        HRFlowable(width="100%", thickness=1, color=BRAND_COLOR, spaceAfter=14),
    ]

    for paragraph in document.content.split("\n\n"):
        text = escape(paragraph.strip()).replace("\n", "<br/>")
        if text:
            story.append(Paragraph(text, body_style))
            story.append(Spacer(1, 4))

    doc.build(story)
    return buffer.getvalue()
