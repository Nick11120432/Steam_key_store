import secrets
from decimal import Decimal

from django.db import connection
from django.db import transaction as db_transaction

from fastapi_app.config import settings
from fastapi_app.exceptions import ServiceError
from shared.models import Case, CaseItem, Key, Opening, Transaction, User


def _choose_weighted_case_item(case_items: list[CaseItem]) -> CaseItem:
    total_weight = sum(ci.weight for ci in case_items)
    if total_weight <= 0:
        raise ServiceError("Case has no valid drop weights", 409)

    point = secrets.randbelow(total_weight)
    cumulative = 0

    for case_item in case_items:
        cumulative += case_item.weight
        if point < cumulative:
            return case_item

    raise RuntimeError("Weighted selection failed unexpectedly")


def _select_available_key(item_id: int):
    queryset = Key.objects.filter(
        item_id=item_id,
        status=Key.Status.AVAILABLE,
        owner__isnull=True,
    ).order_by("id")

    if connection.features.has_select_for_update:
        if connection.features.has_select_for_update_skip_locked:
            queryset = queryset.select_for_update(skip_locked=True)
        else:
            queryset = queryset.select_for_update()

    return queryset.first()


@db_transaction.atomic
def open_case(*, user_id: int, case_id: int) -> tuple[Opening, Decimal]:
    try:
        user = User.objects.select_for_update().get(id=user_id, is_active=True)
    except User.DoesNotExist:
        raise ServiceError("User not found", 404)

    try:
        case = Case.objects.select_for_update().get(id=case_id, is_active=True)
    except Case.DoesNotExist:
        raise ServiceError("Case not found", 404)

    case_items = list(
        CaseItem.objects.select_for_update()
        .filter(case=case)
        .select_related("item")
        .order_by("id")
    )
    if not case_items:
        raise ServiceError("Case has no items configured", 409)

    if user.balance < case.opening_price:
        raise ServiceError("Insufficient balance", 400)

    selected = _choose_weighted_case_item(case_items)
    key = _select_available_key(selected.item_id)

    if key is None and settings.case_no_key_policy == "error":
        raise ServiceError("No activation key is available for the selected item", 409)

    user.balance -= case.opening_price
    user.save(update_fields=["balance"])

    if key is not None:
        key.owner = user
        key.status = Key.Status.ASSIGNED
        key.save(update_fields=["owner", "status"])

    opening = Opening.objects.create(
        user=user,
        case=case,
        item=selected.item,
        key=key,
        cost=case.opening_price,
    )

    Transaction.objects.create(
        user=user,
        type=Transaction.Type.DEBIT,
        amount=case.opening_price,
        description=f"Opening case #{case.id}: {case.name}",
    )

    return opening, user.balance


@db_transaction.atomic
def top_up_balance(*, user_id: int, amount: Decimal) -> Decimal:
    if amount <= 0:
        raise ServiceError("Top-up amount must be positive", 422)

    try:
        user = User.objects.select_for_update().get(id=user_id, is_active=True)
    except User.DoesNotExist:
        raise ServiceError("User not found", 404)

    user.balance += amount
    user.save(update_fields=["balance"])

    Transaction.objects.create(
        user=user,
        type=Transaction.Type.CREDIT,
        amount=amount,
        description="Test balance top-up",
    )

    return user.balance


@db_transaction.atomic
def mark_key_used(*, user_id: int, key_id: int) -> Key:
    try:
        key = (
            Key.objects.select_for_update()
            .select_related("item")
            .get(id=key_id, owner_id=user_id)
        )
    except Key.DoesNotExist:
        raise ServiceError("Key not found in your inventory", 404)

    if key.status == Key.Status.USED:
        return key

    if key.status != Key.Status.ASSIGNED:
        raise ServiceError("Only assigned keys can be marked as used", 409)

    key.status = Key.Status.USED
    key.save(update_fields=["status"])
    return key
