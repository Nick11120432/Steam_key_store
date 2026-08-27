from decimal import Decimal

import pytest

from shared.models import Item, Key, User


@pytest.mark.django_db(transaction=True)
def test_inventory_and_mark_used(client, registered_user):
    user = User.objects.get(username="alice")
    item = Item.objects.create(
        name="Inventory Game",
        steam_app_id=777,
        image_url="https://example.com/inventory.png",
        rarity=Item.Rarity.RARE,
        estimated_price=Decimal("15.00"),
    )
    key = Key.objects.create(
        item=item,
        key="INV-KEY-0001",
        owner=user,
        status=Key.Status.ASSIGNED,
    )

    inventory = client.get(
        "/api/v1/inventory",
        headers=registered_user["headers"],
    )
    assert inventory.status_code == 200
    assert inventory.json()["total"] == 1

    used = client.post(
        f"/api/v1/inventory/{key.id}/use",
        headers=registered_user["headers"],
    )
    assert used.status_code == 200
    assert used.json()["status"] == "used"

    key.refresh_from_db()
    assert key.status == Key.Status.USED
