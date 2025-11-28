from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import Category, Product, Language


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "created_at")


@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = (
        "name",
        "name_uz",
        "name_ru",
        "name_en",
        "description",
        "description_uz",
        "description_ru",
        "description_en",
    )
    ordering = ("-created_at",)


@admin.register(Product)
class ProductAdmin(TranslationAdmin):
    list_display = (
        "__str__",
        "category",
        "ordinary_first_page_price",
        "ordinary_other_page_price",
        "agency_first_page_price",
        "agency_other_page_price",
        "user_copy_price_percentage",
        "agency_copy_price_percentage",
        "min_pages",
        "estimated_days",
        "is_active",
    )
    list_filter = ("category", "is_active", "created_at")
    search_fields = (
        "name",
        "name_uz",
        "name_ru",
        "name_en",
        "description",
        "description_uz",
        "description_ru",
        "description_en",
        "category__name_uz",
        "category__name_ru",
        "category__name_en",
    )
    ordering = ("category", "name")

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "category", "description", "is_active")},
        ),
        (
            "Base Pricing",
            {
                "fields": (
                    "ordinary_first_page_price",
                    "ordinary_other_page_price",
                    "agency_first_page_price",
                    "agency_other_page_price",
                )
            },
        ),
        (
            "Copy Pricing (Additional Copies)",
            {
                "fields": (
                    "user_copy_price_percentage",
                    "agency_copy_price_percentage",
                ),
                "description": "Percentage of base price charged for each additional copy. 100% means each copy costs the same as the base price.",
            },
        ),
        (
            "Other Settings",
            {
                "fields": (
                    "min_pages",
                    "estimated_days",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "service_category",
    )

    def service_category(self, obj):
        return obj.service_category.title()

    service_category.short_description = "Service Category"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category")
