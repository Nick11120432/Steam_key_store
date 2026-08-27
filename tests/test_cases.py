from decimal import Decimal

import pytest

from shared.models import Case, CaseItem, Item, Key, Opening, Transaction, User


@pytest.mark.django_db(transaction=True)
def test_list_case_details_and_open_case(client, registered_user):
    item = Item.objects.create(
        name="Example Game",
        steam_app_id=123456,
        image_url="https://example.com/game.png",
        rarity=Item.Rarity.EPIC,
        estimated_price=Decimal("25.00"),
    )
    case = Case.objects.create(
        name="Epic Case",
        description="Test case",
        opening_price=Decimal("5.00"),
        image_url="https://example.com/case.png",
    )
    CaseItem.objects.create(case=case, item=item, weight=10)
    key = Key.objects.create(item=item, key="AAAA-BBBB-CCCC")

    topup = client.post(
        "/api/v1/balance/top-up",
        json={"amount": "10.00"},
        headers=registered_user["headers"],
    )
    assert topup.status_code == 200
    assert topup.json()["balance"] == "10.00"

    listing = client.get("/api/v1/cases?rarity=epic")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    detail = client.get(f"/api/v1/cases/{case.id}")
    assert detail.status_code == 200
    assert detail.json()["items"][0]["chance_percent"] == "100.00"

    opened = client.post(
        f"/api/v1/cases/{case.id}/open",
        headers=registered_user["headers"],
    )
    assert opened.status_code == 200, opened.text
    body = opened.json()
    assert body["item"]["id"] == item.id
    assert body["key"]["key"] == "AAAA-BBBB-CCCC"
    assert body["balance_after"] == "5.00"

    key.refresh_from_db()
    assert key.status == Key.Status.ASSIGNED
    assert key.owner.username == "alice"
    assert Opening.objects.count() == 1
    assert Transaction.objects.filter(type=Transaction.Type.DEBIT).count() == 1

    user = User.objects.get(username="alice")
    assert user.balance == Decimal("5.00")


@pytest.mark.django_db(transaction=True)
def test_open_case_without_key_item_only_policy(client, registered_user):
    item = Item.objects.create(
        name="No Key Game",
        steam_app_id=999,
        image_url="https://example.com/no-key.png",
        rarity=Item.Rarity.COMMON,
        estimated_price=Decimal("3.00"),
    )
    case = Case.objects.create(
        name="No Key Case",
        opening_price=Decimal("1.00"),
        image_url="https://example.com/no-key-case.png",
    )
    CaseItem.objects.create(case=case, item=item, weight=1)

    client.post(
        "/api/v1/balance/top-up",
        json={"amount": "2.00"},
        headers=registered_user["headers"],
    )

    response = client.post(
        f"/api/v1/cases/{case.id}/open",
        headers=registered_user["headers"],
    )
    assert response.status_code == 200
    assert response.json()["key"] is None
