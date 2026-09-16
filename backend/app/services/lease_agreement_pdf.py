"""
Renders a real, per-lease, personalized lease agreement PDF.

This replaces the earlier "one shared static file" approach: the download
is now generated on demand from the actual lease/guest/unit/property data,
so it reads as a genuine document rather than a placeholder. No file is
stored on disk for this - `lease_agreement.agreement_file_url` is kept
only as an "is an agreement available" marker (see plan Decision 7 /
its follow-up), not a real path.
"""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BRAND_COLOR = colors.HexColor("#2f5233")
MUTED_COLOR = colors.HexColor("#6d716a")
BORDER_COLOR = colors.HexColor("#ded8cb")


def _format_date(value) -> str:
    if value is None:
        return "—"
    return value.strftime("%d %B %Y")


def _format_money(amount) -> str:
    return f"Rs. {amount:,.2f}"


def generate_lease_agreement_pdf(lease) -> bytes:
    guest = lease.guest
    unit = lease.unit
    property_ = unit.property

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "MeridianTitle", parent=styles["Title"], textColor=BRAND_COLOR, fontSize=22, spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "MeridianSubtitle", parent=styles["Normal"], textColor=MUTED_COLOR, fontSize=11, spaceAfter=14,
    )
    heading_style = ParagraphStyle(
        "MeridianHeading", parent=styles["Heading2"], textColor=BRAND_COLOR, fontSize=13,
        spaceBefore=16, spaceAfter=6,
    )
    body_style = ParagraphStyle("MeridianBody", parent=styles["Normal"], fontSize=10, leading=15)
    meta_style = ParagraphStyle("MeridianMeta", parent=styles["Normal"], fontSize=8, textColor=MUTED_COLOR)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        title=f"Lease Agreement - {unit.unit_number}",
    )

    story = []
    story.append(Paragraph("MERIDIAN RESIDENCES", title_style))
    story.append(Paragraph("Residential Lease Agreement", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_COLOR, spaceAfter=14))

    story.append(
        Paragraph(
            f"Document generated {datetime.now(timezone.utc).strftime('%d %B %Y')} &nbsp;|&nbsp; "
            f"Lease ID: {lease.id}",
            meta_style,
        )
    )

    story.append(Paragraph("Parties", heading_style))
    story.append(
        Paragraph(
            f"This agreement is made between <b>{property_.name}</b> (\"the Property\"), "
            f"located at {property_.address or 'the address on file'}, and "
            f"<b>{guest.name}</b> (\"the Resident\").",
            body_style,
        )
    )

    story.append(Paragraph("Lease Details", heading_style))
    detail_rows = [
        ["Unit", f"{unit.unit_number} ({unit.unit_type or 'N/A'})"],
        ["Lease term", f"{_format_date(lease.start_date)} to {_format_date(lease.end_date)}"],
        ["Monthly rent", _format_money(lease.monthly_rate)],
        ["Renewal date", _format_date(lease.renewal_date)],
        ["Status", lease.status.replace("_", " ").title()],
    ]
    table = Table(detail_rows, colWidths=[1.8 * inch, 4.2 * inch])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (0, -1), BRAND_COLOR),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, BORDER_COLOR),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(table)

    story.append(Paragraph("Terms &amp; Conditions", heading_style))
    terms = [
        "Rent is due on the first day of each month. Late payments may be "
        "subject to a fee as described in the building's payment policy.",
        "The Resident agrees to maintain the unit in good condition and to "
        "report maintenance issues promptly through the resident portal.",
        "Either party may request renewal or termination of this lease in "
        "accordance with the notice periods described in the building's "
        "lease terms document.",
    ]
    for i, term in enumerate(terms, start=1):
        story.append(Paragraph(f"{i}. {term}", body_style))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 24))
    sig_table = Table(
        [
            ["_________________________", "_________________________"],
            ["Resident Signature", "Property Manager Signature"],
            [f"Date: {_format_date(None)}", f"Date: {_format_date(None)}"],
        ],
        colWidths=[3 * inch, 3 * inch],
    )
    sig_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 1), (-1, -1), MUTED_COLOR),
                ("TOPPADDING", (0, 0), (-1, 0), 24),
            ]
        )
    )
    story.append(sig_table)

    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            "This is a system-generated document produced for Meridian Residences "
            "residents and does not require a physical signature to be viewed.",
            meta_style,
        )
    )

    doc.build(story)
    return buffer.getvalue()
