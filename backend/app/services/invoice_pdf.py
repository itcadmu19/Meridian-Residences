"""Renders recurring-invoice records as downloadable PDF documents (Member 2 — Story 2)."""

from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_BRAND_FOREST = colors.HexColor("#26382A")
_BRAND_CREAM = colors.HexColor("#F6F0E4")
_BRAND_BORDER = colors.HexColor("#DED8CB")
_BRAND_MUTED = colors.HexColor("#6D716A")

_STYLES = getSampleStyleSheet()
_TITLE_STYLE = ParagraphStyle("MeridianTitle", parent=_STYLES["Title"], textColor=_BRAND_FOREST, fontSize=20)
_SUBTITLE_STYLE = ParagraphStyle("MeridianSubtitle", parent=_STYLES["Normal"], textColor=_BRAND_MUTED)


def _format_currency(amount) -> str:
    return f"Rs. {Decimal(amount):,.2f}"


def _base_doc():
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, topMargin=24 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm
    )
    return buffer, doc


def _table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _BRAND_FOREST),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, _BRAND_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _BRAND_CREAM]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])


def build_invoice_pdf(invoice, lease) -> bytes:
    """Single invoice statement including lease/unit/resident context."""
    buffer, doc = _base_doc()
    unit_number = lease.unit.unit_number if lease and lease.unit else "-"
    guest_name = lease.guest.name if lease and lease.guest else "-"

    elements = [
        Paragraph("MERIDIAN RESIDENCES", _TITLE_STYLE),
        Paragraph("Recurring Invoice Statement", _SUBTITLE_STYLE),
        Spacer(1, 14),
        Paragraph(f"Invoice ID: {invoice.id}", _STYLES["Normal"]),
        Paragraph(f"Resident: {guest_name} &nbsp;|&nbsp; Unit: {unit_number}", _STYLES["Normal"]),
        Spacer(1, 16),
    ]

    rows = [
        ["Billing Period", "Amount", "Due Date", "Status"],
        [
            f"{invoice.billing_period_start:%d %b %Y} - {invoice.billing_period_end:%d %b %Y}",
            _format_currency(invoice.amount),
            f"{invoice.due_date:%d %b %Y}",
            invoice.payment_status.upper(),
        ],
    ]
    table = Table(rows, colWidths=[170, 100, 100, 90])
    table.setStyle(_table_style())
    elements.append(table)

    if invoice.paid_at:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Paid on: {invoice.paid_at:%d %b %Y}", _STYLES["Normal"]))

    doc.build(elements)
    return buffer.getvalue()


def build_invoice_statement_pdf(invoices, filters: dict) -> bytes:
    """Filtered multi-invoice statement matching the Invoices page filters."""
    buffer, doc = _base_doc()

    filter_summary = ", ".join(f"{key}: {value}" for key, value in filters.items() if value) or "All invoices"
    elements = [
        Paragraph("MERIDIAN RESIDENCES", _TITLE_STYLE),
        Paragraph("Recurring Invoice Statement", _SUBTITLE_STYLE),
        Spacer(1, 6),
        Paragraph(f"Filters: {filter_summary}", _STYLES["Normal"]),
        Spacer(1, 14),
    ]

    rows = [["Billing Period", "Unit", "Amount", "Due Date", "Status"]]
    total = Decimal("0")
    for invoice in invoices:
        unit_number = invoice.lease.unit.unit_number if invoice.lease and invoice.lease.unit else "-"
        rows.append([
            f"{invoice.billing_period_start:%d %b %Y} - {invoice.billing_period_end:%d %b %Y}",
            unit_number,
            _format_currency(invoice.amount),
            f"{invoice.due_date:%d %b %Y}",
            invoice.payment_status.upper(),
        ])
        total += Decimal(invoice.amount)

    table = Table(rows, colWidths=[150, 60, 90, 90, 80])
    table.setStyle(_table_style())
    elements.append(table)
    elements.append(Spacer(1, 14))
    elements.append(Paragraph(f"Total: {_format_currency(total)} ({len(invoices)} invoice(s))", _STYLES["Heading3"]))

    doc.build(elements)
    return buffer.getvalue()
