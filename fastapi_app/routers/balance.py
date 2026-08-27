from fastapi import APIRouter, Depends, Query

from fastapi_app.dependencies import get_current_user
from fastapi_app.django_bootstrap import django  # noqa: F401
from fastapi_app.schemas import (
    BalanceResponse,
    TopUpRequest,
    TransactionListResponse,
)
from fastapi_app.services import top_up_balance
from shared.models import Transaction, User

router = APIRouter(prefix="/balance", tags=["balance"])


@router.post("/top-up", response_model=BalanceResponse)
def top_up(payload: TopUpRequest, user: User = Depends(get_current_user)):
    balance = top_up_balance(user_id=user.id, amount=payload.amount)
    return {"balance": balance}


@router.get("/transactions", response_model=TransactionListResponse)
def transactions(
    user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    queryset = Transaction.objects.filter(user=user).order_by("-created_at", "-id")
    total = queryset.count()
    rows = queryset[offset : offset + limit]
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": row.id,
                "type": row.type,
                "amount": row.amount,
                "created_at": row.created_at,
                "description": row.description,
            }
            for row in rows
        ],
    }
