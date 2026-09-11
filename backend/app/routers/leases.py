from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.common import SuccessResponse
from app.schemas.lease import LeaseResponse, LeaseSummaryResponse
from app.services import lease_service
from app.services.lease_service import LeaseAccessDeniedError, LeaseNotFoundError

router = APIRouter(prefix="/leases", tags=["leases"])


def _lease_data(lease, details):
    return LeaseResponse.model_validate({**lease.__dict__, **details})


@router.get("/{lease_id}", response_model=SuccessResponse[LeaseResponse])
def get_lease(lease_id: UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    try:
        lease, details = lease_service.get_lease(db, lease_id, current_user.guest_id, current_user.role)
    except LeaseNotFoundError:
        raise HTTPException(404, detail={"message": "Lease not found", "error_code": "LEASE_NOT_FOUND"})
    except LeaseAccessDeniedError:
        raise HTTPException(403, detail={"message": "You do not have access to this lease", "error_code": "FORBIDDEN"})
    return SuccessResponse(data=_lease_data(lease, details))


@router.get("/{lease_id}/summary", response_model=SuccessResponse[LeaseSummaryResponse])
def get_summary(lease_id: UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    try:
        lease, details, summary = lease_service.get_summary(db, lease_id, current_user.guest_id, current_user.role)
    except LeaseNotFoundError:
        raise HTTPException(404, detail={"message": "Lease not found", "error_code": "LEASE_NOT_FOUND"})
    except LeaseAccessDeniedError:
        raise HTTPException(403, detail={"message": "You do not have access to this lease", "error_code": "FORBIDDEN"})
    return SuccessResponse(data=LeaseSummaryResponse(lease=_lease_data(lease, details), **summary))
