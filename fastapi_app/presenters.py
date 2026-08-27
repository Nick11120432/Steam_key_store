from decimal import Decimal, ROUND_HALF_UP

from shared.models import Case, CaseItem, Key, Opening


def item_dict(item):
    return {
        "id": item.id,
        "name": item.name,
        "steam_app_id": item.steam_app_id,
        "image_url": item.image_url,
        "rarity": item.rarity,
        "estimated_price": item.estimated_price,
    }


def case_summary_dict(case: Case):
    return {
        "id": case.id,
        "name": case.name,
        "description": case.description,
        "opening_price": case.opening_price,
        "image_url": case.image_url,
        "is_active": case.is_active,
    }


def case_detail_dict(case: Case, case_items: list[CaseItem]):
    total_weight = sum(ci.weight for ci in case_items)
    items = []

    for ci in case_items:
        chance = Decimal("0.00")
        if total_weight:
            chance = (
                Decimal(ci.weight)
                * Decimal("100")
                / Decimal(total_weight)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        items.append(
            {
                "item": item_dict(ci.item),
                "weight": ci.weight,
                "chance_percent": chance,
            }
        )

    data = case_summary_dict(case)
    data["items"] = items
    return data


def key_dict(key: Key):
    return {
        "id": key.id,
        "key": key.key,
        "status": key.status,
        "item": item_dict(key.item),
        "added_at": key.added_at,
    }


def opening_history_dict(opening: Opening):
    return {
        "id": opening.id,
        "case": case_summary_dict(opening.case),
        "item": item_dict(opening.item),
        "key": key_dict(opening.key) if opening.key else None,
        "cost": opening.cost,
        "opened_at": opening.opened_at,
    }
