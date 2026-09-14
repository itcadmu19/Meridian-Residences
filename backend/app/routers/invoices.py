from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_staff
from app.schemas.auth import CurrentUser
from app.schemas.common import Meta, SuccessResponse
from app.schemas.invoice import (
    GenerateBatchRequest,
    GenerateInvoiceRequest,
    InvoiceBatchResult,
    InvoiceInsightResponse,
    InvoiceResponse,
    DueDateUpdate,
    OverdueSweepResult,
    PaymentStatusUpdate,
)
from app.services import invoice_service
from app.services import invoice_pdf
from app.services.invoice_service import InvoiceAccessDeniedError, InvoiceNotFoundError, LeaseNotEligibleError

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _error(status: int, message: str, code: str):
    return HTTPException(status, detail={"message": message, "error_code": code})


@router.get("", response_model=SuccessResponse[list[InvoiceResponse]])
def list_invoices(
    lease_id: UUID | None = None,
    payment_status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    items, total = invoice_service.list_invoices(
        db, current_user.guest_id, current_user.role, lease_id, payment_status, date_from, date_to, page, page_size
    )
    return SuccessResponse(
        data=[InvoiceResponse.model_validate(item) for item in items],
        meta=Meta(page=page, page_size=page_size, total=total),
    )


@router.get("/insights", response_model=SuccessResponse[InvoiceInsightResponse])
def get_invoice_insights(
    lease_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        result = invoice_service.get_invoice_insights(db, current_user.guest_id, current_user.role, lease_id)
    except InvoiceNotFoundError:
        raise _error(404, "Lease not found", "LEASE_NOT_FOUND")
    except InvoiceAccessDeniedError:
        raise _error(403, "You do not have access to this lease", "FORBIDDEN")
    return SuccessResponse(data=InvoiceInsightResponse(
        risk_level=result.risk_level,
        late_payment_count=result.late_payment_count,
        total_invoices_considered=result.total_invoices_considered,
        average_days_late=result.average_days_late,
        overdue_count=result.overdue_count,
        overdue_amount=result.overdue_amount,
        insight=result.insight,
    ))


@router.get("/export/pdf")
def export_invoices_pdf(
    lease_id: UUID | None = None,
    payment_status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    invoices = invoice_service.list_invoices_for_export(
        db, current_user.guest_id, current_user.role, lease_id, payment_status, date_from, date_to
    )
    pdf_bytes = invoice_pdf.build_invoice_statement_pdf(invoices, {
        "payment_status": payment_status,
        "date_from": date_from,
        "date_to": date_to,
    })
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=meridian-invoice-statement.pdf"},
    )


@router.post("/mark-overdue", response_model=SuccessResponse[OverdueSweepResult])
def mark_overdue_invoices(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_staff),
):
    flagged_count = invoice_service.mark_overdue_invoices(db, current_user.role)
    return SuccessResponse(data=OverdueSweepResult(flagged_count=flagged_count))


@router.post("/generate", response_model=SuccessResponse[InvoiceResponse], status_code=201)
def generate_invoice(
    payload: GenerateInvoiceRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        invoice, created = invoice_service.generate_invoice(
            db, current_user.guest_id, current_user.role, payload.lease_id,
            payload.billing_period_start, payload.billing_period_end, payload.due_date, payload.amount,
        )
    except InvoiceNotFoundError:
        raise _error(404, "Lease not found", "LEASE_NOT_FOUND")
    except InvoiceAccessDeniedError:
        raise _error(403, "You do not have access to this lease", "FORBIDDEN")
    except LeaseNotEligibleError as exc:
        raise _error(400, str(exc), "LEASE_NOT_ACTIVE")
    except ValueError as exc:
        raise _error(422, str(exc), "INVALID_BILLING_PERIOD")
    return SuccessResponse(data=InvoiceResponse.model_validate(invoice), message=None if created else "Existing invoice returned")


@router.post("/generate-batch", response_model=SuccessResponse[InvoiceBatchResult])
def generate_batch(
    payload: GenerateBatchRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_staff),
):
    try:
        invoice_ids, duplicate_count, failed_count = invoice_service.generate_batch(db, payload, current_user.role)
    except ValueError as exc:
        raise _error(422, str(exc), "INVALID_BILLING_PERIOD")
    return SuccessResponse(data=InvoiceBatchResult(
        generated_count=len(invoice_ids) - duplicate_count,
        duplicate_count=duplicate_count,
        failed_count=failed_count,
        invoice_ids=invoice_ids,
    ))


@router.get("/{invoice_id}", response_model=SuccessResponse[InvoiceResponse])
def get_invoice(invoice_id: UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    try:
        invoice = invoice_service.get_invoice(db, invoice_id, current_user.guest_id, current_user.role)
    except InvoiceNotFoundError:
        raise _error(404, "Invoice not found", "INVOICE_NOT_FOUND")
    except InvoiceAccessDeniedError:
        raise _error(403, "You do not have access to this invoice", "FORBIDDEN")
    return SuccessResponse(data=InvoiceResponse.model_validate(invoice))


@router.patch("/{invoice_id}/payment-status", response_model=SuccessResponse[InvoiceResponse])
def update_payment_status(
    invoice_id: UUID,
    payload: PaymentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        invoice = invoice_service.update_payment_status(
            db, invoice_id, payload.payment_status, current_user.guest_id, current_user.role
        )
    except InvoiceNotFoundError:
        raise _error(404, "Invoice not found", "INVOICE_NOT_FOUND")
    except InvoiceAccessDeniedError:
        raise _error(403, "You do not have access to this invoice", "FORBIDDEN")
    except ValueError as exc:
        raise _error(400, str(exc), "INVALID_PAYMENT_STATUS")
    return SuccessResponse(data=InvoiceResponse.model_validate(invoice))


@router.patch("/{invoice_id}/due-date", response_model=SuccessResponse[InvoiceResponse])
def extend_due_date(
    invoice_id: UUID,
    payload: DueDateUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        invoice = invoice_service.extend_due_date(
            db, invoice_id, payload.due_date, current_user.guest_id, current_user.role
        )
    except InvoiceNotFoundError:
        raise _error(404, "Invoice not found", "INVOICE_NOT_FOUND")
    except InvoiceAccessDeniedError:
        raise _error(403, "Only staff can extend invoice due dates", "FORBIDDEN")
    except ValueError as exc:
        raise _error(400, str(exc), "INVALID_DUE_DATE")
    return SuccessResponse(data=InvoiceResponse.model_validate(invoice))


@router.post("/{invoice_id}/pay", response_model=SuccessResponse[InvoiceResponse])
def submit_payment(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        invoice = invoice_service.submit_payment(db, invoice_id, current_user.guest_id, current_user.role)
    except InvoiceNotFoundError:
        raise _error(404, "Invoice not found", "INVOICE_NOT_FOUND")
    except InvoiceAccessDeniedError:
        raise _error(403, "Only residents can submit invoice payments", "FORBIDDEN")
    except ValueError as exc:
        raise _error(400, str(exc), "INVALID_PAYMENT_STATUS")
    return SuccessResponse(data=InvoiceResponse.model_validate(invoice), message="Payment submitted for staff approval")


@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        invoice, lease = invoice_service.get_invoice_with_lease(db, invoice_id, current_user.guest_id, current_user.role)
    except InvoiceNotFoundError:
        raise _error(404, "Invoice not found", "INVOICE_NOT_FOUND")
    except InvoiceAccessDeniedError:
        raise _error(403, "You do not have access to this invoice", "FORBIDDEN")
    pdf_bytes = invoice_pdf.build_invoice_pdf(invoice, lease)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice-{invoice.id}.pdf"},
    )
