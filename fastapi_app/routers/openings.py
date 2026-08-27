from fastapi import APIRouter, Depends, Query

from fastapi_app.dependencies import get_current_user
from fastapi_app.django_bootstrap import django  # noqa: F401
from fastapi_app.presenters import opening_history_dict
from fastapi_app.schemas import OpeningHistoryResponse
from shared.models import Opening, User

router = APIRouter(prefix="/openings", tags=["openings"])


@router.get("", response_model=OpeningHistoryResponse)
def opening_history(
    user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    queryset = (
        Opening.objects.filter(user=user)
        .select_related("case", "item", "key__item")
        .order_by("-opened_at", "-id")
    )
    total = queryset.count()
    rows = queryset[offset : offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [opening_history_dict(row) for row in rows],
    }
