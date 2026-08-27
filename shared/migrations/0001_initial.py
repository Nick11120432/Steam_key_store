import decimal

import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("username", models.CharField(error_messages={"unique": "A user with that username already exists."}, help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.", max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name="username")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.", verbose_name="active")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("balance", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=12, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))])),
                ("registered_at", models.DateTimeField(auto_now_add=True)),
                ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.", related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={
                "db_table": "users",
                "ordering": ["-registered_at"],
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Item",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("steam_app_id", models.PositiveBigIntegerField(db_index=True)),
                ("image_url", models.URLField(max_length=1000)),
                ("rarity", models.CharField(choices=[("common", "Common"), ("rare", "Rare"), ("epic", "Epic"), ("legendary", "Legendary")], db_index=True, max_length=16)),
                ("estimated_price", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))])),
            ],
            options={
                "db_table": "items",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Case",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("opening_price", models.DecimalField(db_index=True, decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.01"))])),
                ("image_url", models.URLField(max_length=1000)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "cases",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="CaseItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("weight", models.PositiveIntegerField(default=1, help_text="Относительный вес выпадения. Вероятность = weight / сумма weight в кейсе.")),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="case_items", to="shared.case")),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="case_items", to="shared.item")),
            ],
            options={
                "db_table": "case_items",
            },
        ),
        migrations.AddField(
            model_name="case",
            name="items",
            field=models.ManyToManyField(related_name="cases", through="shared.CaseItem", to="shared.item"),
        ),
        migrations.CreateModel(
            name="Key",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=255, unique=True)),
                ("status", models.CharField(choices=[("available", "Доступен"), ("assigned", "Назначен"), ("used", "Использован")], db_index=True, default="available", max_length=16)),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="keys", to="shared.item")),
                ("owner", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="keys", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "activation_keys",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="Opening",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("opened_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("cost", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))])),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="openings", to="shared.case")),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="openings", to="shared.item")),
                ("key", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="opening", to="shared.key")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="openings", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "openings",
                "ordering": ["-opened_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(choices=[("credit", "Пополнение"), ("debit", "Списание")], db_index=True, max_length=8)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.01"))])),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("description", models.CharField(blank=True, max_length=500)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="transactions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "transactions",
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="item",
            index=models.Index(fields=["steam_app_id", "rarity"], name="item_app_rarity_idx"),
        ),
        migrations.AddIndex(
            model_name="caseitem",
            index=models.Index(fields=["case", "weight"], name="case_weight_idx"),
        ),
        migrations.AddConstraint(
            model_name="caseitem",
            constraint=models.UniqueConstraint(fields=("case", "item"), name="unique_case_item"),
        ),
        migrations.AddConstraint(
            model_name="caseitem",
            constraint=models.CheckConstraint(condition=models.Q(weight__gt=0), name="case_item_weight_gt_zero"),
        ),
        migrations.AddIndex(
            model_name="key",
            index=models.Index(fields=["item", "status"], name="key_item_status_idx"),
        ),
        migrations.AddIndex(
            model_name="key",
            index=models.Index(fields=["owner", "status"], name="key_owner_status_idx"),
        ),
        migrations.AddConstraint(
            model_name="key",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("owner__isnull", True), ("status", "available")),
                    models.Q(("owner__isnull", False), ("status__in", ["assigned", "used"])),
                    _connector="OR",
                ),
                name="key_owner_status_consistent",
            ),
        ),
        migrations.AddIndex(
            model_name="opening",
            index=models.Index(fields=["user", "-opened_at"], name="opening_user_date_idx"),
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(fields=["user", "-created_at"], name="txn_user_date_idx"),
        ),
        migrations.AddConstraint(
            model_name="transaction",
            constraint=models.CheckConstraint(condition=models.Q(amount__gt=0), name="transaction_amount_gt_zero"),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(condition=models.Q(balance__gte=0), name="user_balance_nonnegative"),
        ),
    ]
