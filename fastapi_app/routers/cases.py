from decimal import Decimal

from fastapi import APIRouter, Depends, Query

from fastapi_app.dependencies import get_current_user
from fastapi_app.django_bootstrap import django  # noqa: F401
from fastapi_app.presenters import case_detail_dict, case_summary_dict, opening_history_dict
from fastapi_app.schemas import CaseDetail, CaseListResponse, OpeningResult
from fastapi_app.services import open_case
from shared.models import Case, CaseItem, Item, User

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=CaseListResponse)
def list_cases(
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    rarity: Item.Rarity | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    queryset = Case.objects.filter(is_active=True)

    if min_price is not None:
        queryset = queryset.filter(opening_price__gte=min_price)
    if max_price is not None:
        queryset = queryset.filter(opening_price__lte=max_price)
    if rarity is not None:
        queryset = queryset.filter(items__rarity=rarity).distinct()

    total = queryset.count()
    cases = queryset.order_by("id")[offset : offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [case_summary_dict(case) for case in cases],
    }


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(case_id: int):
    case = Case.objects.filter(id=case_id, is_active=True).first()
    if case is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Case not found")

    case_items = list(
        CaseItem.objects.filter(case=case)
        .select_related("item")
        .order_by("id")
    )
    return case_detail_dict(case, case_items)


@router.post("/{case_id}/open", response_model=OpeningResult)
def open_case_endpoint(case_id: int, user: User = Depends(get_current_user)):
    opening, balance_after = open_case(user_id=user.id, case_id=case_id)
    opening = (
        opening.__class__.objects
        .select_related("case", "item", "key__item")
        .get(id=opening.id)
    )
    data = opening_history_dict(opening)
    data["balance_after"] = balance_after
    return data
