from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.common import SuccessResponse
from app.schemas.lease import LeaseResponse
from app.services import lease_service

router = APIRouter(prefix="/guests", tags=["guests"])


@router.get("/{guest_id}/leases", response_model=SuccessResponse[list[LeaseResponse]])
def get_guest_leases(guest_id: UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    if current_user.role not in ("staff", "admin") and current_user.guest_id != guest_id:
        raise HTTPException(403, detail={"message": "You do not have access to these leases", "error_code": "FORBIDDEN"})
    rows = lease_service.get_guest_leases(db, guest_id, current_user.role)
    data = [LeaseResponse.model_validate({**lease.__dict__, **details}) for lease, details in rows]
    return SuccessResponse(data=data)
