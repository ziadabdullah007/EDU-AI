"""EduCore AI Platform — Payments Router"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_payment_service, require_school_admin, require_teacher
from app.models.payment import PaymentStatus, PaymentType
from app.models.user import User
from app.schemas.payment import CreatePaymentRequest, UpdatePaymentRequest
from app.services.payment import PaymentService
from app.utils.pagination import PaginationParams
from app.utils.responses import success_response

router = APIRouter(prefix="/schools/{school_id}/payments", tags=["Payments"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, summary="Create payment")
async def create_payment(
    school_id: UUID,
    payload: CreatePaymentRequest,
    requesting_user: User = Depends(require_school_admin),
    service: PaymentService = Depends(get_payment_service),
) -> dict:
    payment = await service.create_payment(school_id, payload, requesting_user)
    return success_response(data=payment.model_dump(), message="Payment created.")


@router.get("", response_model=dict, status_code=status.HTTP_200_OK, summary="List school payments")
async def list_school_payments(
    school_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    status_filter: PaymentStatus | None = Query(None, alias="status"),
    payment_type: PaymentType | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    requesting_user: User = Depends(require_school_admin),
    service: PaymentService = Depends(get_payment_service),
) -> dict:
    params = PaginationParams(page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)
    result = await service.list_school_payments(
        school_id, params, requesting_user, search=search,
        status=status_filter, payment_type=payment_type,
    )
    return success_response(data=result.model_dump(), message="Payments retrieved.")


@router.get("/students/{student_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Student payments")
async def list_student_payments(
    school_id: UUID,
    student_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: PaymentStatus | None = Query(None, alias="status"),
    payment_type: PaymentType | None = Query(None),
    requesting_user: User = Depends(require_teacher),
    service: PaymentService = Depends(get_payment_service),
) -> dict:
    params = PaginationParams(page=page, page_size=page_size)
    result = await service.list_student_payments(
        school_id, student_id, params, requesting_user, status=status_filter, payment_type=payment_type
    )
    return success_response(data=result.model_dump(), message="Student payments retrieved.")


@router.get("/students/{student_id}/balance", response_model=dict, status_code=status.HTTP_200_OK, summary="Student balance")
async def get_student_balance(
    school_id: UUID,
    student_id: UUID,
    requesting_user: User = Depends(require_teacher),
    service: PaymentService = Depends(get_payment_service),
) -> dict:
    balance = await service.get_student_balance(school_id, student_id, requesting_user)
    return success_response(data=balance.model_dump(), message="Balance retrieved.")


@router.get("/{payment_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Get payment")
async def get_payment(
    school_id: UUID,
    payment_id: UUID,
    requesting_user: User = Depends(require_teacher),
    service: PaymentService = Depends(get_payment_service),
) -> dict:
    payment = await service.get_payment(school_id, payment_id, requesting_user)
    return success_response(data=payment.model_dump(), message="Payment retrieved.")


@router.patch("/{payment_id}", response_model=dict, status_code=status.HTTP_200_OK, summary="Update payment")
async def update_payment(
    school_id: UUID,
    payment_id: UUID,
    payload: UpdatePaymentRequest,
    requesting_user: User = Depends(require_school_admin),
    service: PaymentService = Depends(get_payment_service),
) -> dict:
    payment = await service.update_payment(school_id, payment_id, payload, requesting_user)
    return success_response(data=payment.model_dump(), message="Payment updated.")
