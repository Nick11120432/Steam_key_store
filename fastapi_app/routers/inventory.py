from fastapi import APIRouter, Depends

from fastapi_app.dependencies import get_current_user
from fastapi_app.django_bootstrap import django  # noqa: F401
from fastapi_app.presenters import key_dict
from fastapi_app.schemas import InventoryResponse, KeyPublic
from fastapi_app.services import mark_key_used
from shared.models import Key, User

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=InventoryResponse)
def inventory(user: User = Depends(get_current_user)):
    keys = list(
        Key.objects.filter(
            owner=user,
            status__in=[Key.Status.ASSIGNED, Key.Status.USED],
        )
        .select_related("item")
        .order_by("-added_at", "-id")
    )
    return {"total": len(keys), "items": [key_dict(key) for key in keys]}


@router.post("/{key_id}/use", response_model=KeyPublic)
def use_key(key_id: int, user: User = Depends(get_current_user)):
    key = mark_key_used(user_id=user.id, key_id=key_id)
    return key_dict(key)
