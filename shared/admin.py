from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Case, CaseItem, Item, Key, Opening, Transaction, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "balance", "is_staff", "registered_at")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email")
    readonly_fields = ("registered_at", "last_login", "date_joined")
    fieldsets = UserAdmin.fieldsets + (
        ("Steam Cases", {"fields": ("balance", "registered_at")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Steam Cases", {"fields": ("email", "balance")}),
    )


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "steam_app_id", "rarity", "estimated_price")
    list_filter = ("rarity",)
    search_fields = ("name", "steam_app_id")


class CaseItemInline(admin.TabularInline):
    model = CaseItem
    extra = 1
    autocomplete_fields = ("item",)


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("name", "opening_price", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    inlines = (CaseItemInline,)


@admin.register(CaseItem)
class CaseItemAdmin(admin.ModelAdmin):
    list_display = ("case", "item", "weight")
    autocomplete_fields = ("case", "item")


@admin.register(Key)
class KeyAdmin(admin.ModelAdmin):
    list_display = ("key", "item", "status", "owner", "added_at")
    list_filter = ("status", "item__rarity")
    search_fields = ("key", "item__name", "owner__username", "owner__email")
    autocomplete_fields = ("item", "owner")
    readonly_fields = ("added_at",)


class ReadOnlyAdminMixin:
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Opening)
class OpeningAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("id", "user", "case", "item", "key", "cost", "opened_at")
    list_filter = ("case", "item__rarity")
    search_fields = ("user__username", "user__email", "key__key")
    readonly_fields = ("user", "case", "item", "key", "cost", "opened_at")


@admin.register(Transaction)
class TransactionAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("id", "user", "type", "amount", "created_at", "description")
    list_filter = ("type",)
    search_fields = ("user__username", "user__email", "description")
    readonly_fields = ("user", "type", "amount", "created_at", "description")
