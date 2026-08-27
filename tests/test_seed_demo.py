from django.core.management import call_command
import pytest

from shared.models import Case, CaseItem, Item, Key


@pytest.mark.django_db(transaction=True)
def test_seed_demo_is_idempotent_and_creates_catalog():
    call_command("seed_demo", keys_per_item=2)

    assert Item.objects.filter(steam_app_id=1091500, name="Cyberpunk 2077").exists()
    assert Case.objects.filter(name="Starter Case", is_active=True).exists()
    assert Case.objects.filter(name="Legendary Case", is_active=True).exists()
    assert CaseItem.objects.filter(case__name="Starter Case").count() == 4
    assert Key.objects.filter(key__startswith="DEMO-", status=Key.Status.AVAILABLE).count() == 14

    call_command("seed_demo", keys_per_item=2)
    assert Key.objects.filter(key__startswith="DEMO-", status=Key.Status.AVAILABLE).count() == 14
