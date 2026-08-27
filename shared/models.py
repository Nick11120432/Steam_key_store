from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class User(AbstractUser):
    email = models.EmailField(unique=True)
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users"
        ordering = ["-registered_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(balance__gte=0),
                name="user_balance_nonnegative",
            )
        ]

    def __str__(self) -> str:
        return self.username


class Item(models.Model):
    class Rarity(models.TextChoices):
        COMMON = "common", "Common"
        RARE = "rare", "Rare"
        EPIC = "epic", "Epic"
        LEGENDARY = "legendary", "Legendary"

    name = models.CharField(max_length=255)
    steam_app_id = models.PositiveBigIntegerField(db_index=True)
    image_url = models.URLField(max_length=1000)
    rarity = models.CharField(max_length=16, choices=Rarity.choices, db_index=True)
    estimated_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        db_table = "items"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["steam_app_id", "rarity"], name="item_app_rarity_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_rarity_display()})"


class Case(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    opening_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        db_index=True,
    )
    image_url = models.URLField(max_length=1000)
    is_active = models.BooleanField(default=True, db_index=True)
    items = models.ManyToManyField(
        Item,
        through="CaseItem",
        related_name="cases",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cases"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name


class CaseItem(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="case_items")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="case_items")
    weight = models.PositiveIntegerField(
        default=1,
        help_text="Относительный вес выпадения. Вероятность = weight / сумма weight в кейсе.",
    )

    class Meta:
        db_table = "case_items"
        constraints = [
            models.UniqueConstraint(fields=["case", "item"], name="unique_case_item"),
            models.CheckConstraint(condition=Q(weight__gt=0), name="case_item_weight_gt_zero"),
        ]
        indexes = [
            models.Index(fields=["case", "weight"], name="case_weight_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.case} -> {self.item} ({self.weight})"


class Key(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Доступен"
        ASSIGNED = "assigned", "Назначен"
        USED = "used", "Использован"

    key = models.CharField(max_length=255, unique=True)
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="keys")
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="keys",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "activation_keys"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["item", "status"], name="key_item_status_idx"),
            models.Index(fields=["owner", "status"], name="key_owner_status_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(status="available", owner__isnull=True)
                    | Q(status__in=["assigned", "used"], owner__isnull=False)
                ),
                name="key_owner_status_consistent",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.item.name}: {self.key} [{self.status}]"


class Opening(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="openings")
    case = models.ForeignKey(Case, on_delete=models.PROTECT, related_name="openings")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="openings")
    key = models.OneToOneField(
        Key,
        on_delete=models.PROTECT,
        related_name="opening",
        null=True,
        blank=True,
    )
    opened_at = models.DateTimeField(auto_now_add=True, db_index=True)
    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        db_table = "openings"
        ordering = ["-opened_at", "-id"]
        indexes = [
            models.Index(fields=["user", "-opened_at"], name="opening_user_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user} opened {self.case} -> {self.item}"


class Transaction(models.Model):
    class Type(models.TextChoices):
        CREDIT = "credit", "Пополнение"
        DEBIT = "debit", "Списание"

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="transactions")
    type = models.CharField(max_length=8, choices=Type.choices, db_index=True)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    description = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "transactions"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="txn_user_date_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="transaction_amount_gt_zero"),
        ]

    def __str__(self) -> str:
        return f"{self.user}: {self.type} {self.amount}"
