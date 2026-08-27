import hashlib
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from shared.models import Case, CaseItem, Item, Key


STEAM_IMAGE = "https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/header.jpg"

# Prices are demo/internal values for the case-opening project, not live Steam prices.
ITEMS = {
    "stardew": {
        "name": "Stardew Valley",
        "steam_app_id": 413150,
        "rarity": Item.Rarity.COMMON,
        "estimated_price": Decimal("499.00"),
    },
    "hollow": {
        "name": "Hollow Knight",
        "steam_app_id": 367520,
        "rarity": Item.Rarity.COMMON,
        "estimated_price": Decimal("699.00"),
    },
    "hades": {
        "name": "Hades",
        "steam_app_id": 1145360,
        "rarity": Item.Rarity.RARE,
        "estimated_price": Decimal("999.00"),
    },
    "witcher3": {
        "name": "The Witcher 3: Wild Hunt",
        "steam_app_id": 292030,
        "rarity": Item.Rarity.RARE,
        "estimated_price": Decimal("1299.00"),
    },
    "cyberpunk": {
        "name": "Cyberpunk 2077",
        "steam_app_id": 1091500,
        "rarity": Item.Rarity.EPIC,
        "estimated_price": Decimal("2499.00"),
    },
    "eldenring": {
        "name": "ELDEN RING",
        "steam_app_id": 1245620,
        "rarity": Item.Rarity.EPIC,
        "estimated_price": Decimal("2999.00"),
    },
    "bg3": {
        "name": "Baldur's Gate 3",
        "steam_app_id": 1086940,
        "rarity": Item.Rarity.LEGENDARY,
        "estimated_price": Decimal("3499.00"),
    },
}

CASES = [
    {
        "name": "Starter Case",
        "description": "Недорогой демо-кейс для первой проверки открытия и выдачи ключа.",
        "opening_price": Decimal("149.00"),
        "image_item": "hollow",
        "drops": {
            "stardew": 45,
            "hollow": 35,
            "hades": 15,
            "witcher3": 5,
        },
    },
    {
        "name": "RPG Case",
        "description": "Ролевые игры: от доступных вариантов до редких AAA-наград.",
        "opening_price": Decimal("399.00"),
        "image_item": "witcher3",
        "drops": {
            "hades": 35,
            "witcher3": 30,
            "cyberpunk": 18,
            "eldenring": 12,
            "bg3": 5,
        },
    },
    {
        "name": "Premium Case",
        "description": "Повышенная вероятность получить дорогую игру эпической редкости.",
        "opening_price": Decimal("799.00"),
        "image_item": "cyberpunk",
        "drops": {
            "witcher3": 25,
            "cyberpunk": 35,
            "eldenring": 25,
            "bg3": 15,
        },
    },
    {
        "name": "Legendary Case",
        "description": "Демо-кейс верхнего уровня с Cyberpunk 2077, ELDEN RING и Baldur's Gate 3.",
        "opening_price": Decimal("1299.00"),
        "image_item": "bg3",
        "drops": {
            "cyberpunk": 35,
            "eldenring": 35,
            "bg3": 30,
        },
    },
]


def demo_key_value(app_id: int, index: int) -> str:
    digest = hashlib.sha1(f"steam-case-demo:{app_id}:{index}".encode()).hexdigest()[:8].upper()
    return f"DEMO-{app_id}-{index:04d}-{digest}"


class Command(BaseCommand):
    help = "Create/update demo Steam items, cases, drop weights and fake activation keys."

    def add_arguments(self, parser):
        parser.add_argument(
            "--keys-per-item",
            type=int,
            default=20,
            help="How many AVAILABLE demo keys to ensure for each demo item (default: 20).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        keys_per_item = options["keys_per_item"]
        if keys_per_item < 0 or keys_per_item > 10000:
            raise CommandError("--keys-per-item must be between 0 and 10000")

        item_objects: dict[str, Item] = {}
        created_items = 0
        created_cases = 0
        created_keys = 0

        for code, data in ITEMS.items():
            app_id = data["steam_app_id"]
            item, created = Item.objects.update_or_create(
                steam_app_id=app_id,
                defaults={
                    "name": data["name"],
                    "image_url": STEAM_IMAGE.format(app_id=app_id),
                    "rarity": data["rarity"],
                    "estimated_price": data["estimated_price"],
                },
            )
            item_objects[code] = item
            created_items += int(created)

        for case_data in CASES:
            image_item = item_objects[case_data["image_item"]]
            case, created = Case.objects.update_or_create(
                name=case_data["name"],
                defaults={
                    "description": case_data["description"],
                    "opening_price": case_data["opening_price"],
                    "image_url": image_item.image_url,
                    "is_active": True,
                },
            )
            created_cases += int(created)

            desired_item_ids = set()
            for item_code, weight in case_data["drops"].items():
                item = item_objects[item_code]
                desired_item_ids.add(item.id)
                CaseItem.objects.update_or_create(
                    case=case,
                    item=item,
                    defaults={"weight": weight},
                )

            # Keep each named demo case deterministic if the command is rerun.
            CaseItem.objects.filter(case=case).exclude(item_id__in=desired_item_ids).delete()

        for item in item_objects.values():
            available_demo_count = Key.objects.filter(
                item=item,
                owner__isnull=True,
                status=Key.Status.AVAILABLE,
                key__startswith=f"DEMO-{item.steam_app_id}-",
            ).count()

            missing = max(0, keys_per_item - available_demo_count)
            if not missing:
                continue

            existing_values = set(
                Key.objects.filter(
                    item=item,
                    key__startswith=f"DEMO-{item.steam_app_id}-",
                ).values_list("key", flat=True)
            )

            index = 1
            while missing:
                value = demo_key_value(item.steam_app_id, index)
                index += 1
                if value in existing_values:
                    continue

                Key.objects.create(
                    key=value,
                    item=item,
                    owner=None,
                    status=Key.Status.AVAILABLE,
                )
                existing_values.add(value)
                created_keys += 1
                missing -= 1

        self.stdout.write(self.style.SUCCESS("Demo catalog is ready."))
        self.stdout.write(f"Items: {len(item_objects)} total ({created_items} newly created)")
        self.stdout.write(f"Cases: {len(CASES)} total ({created_cases} newly created)")
        self.stdout.write(f"New fake demo keys: {created_keys}")
        self.stdout.write(
            self.style.WARNING(
                "DEMO-* values are fake test keys and cannot be activated in Steam."
            )
        )
