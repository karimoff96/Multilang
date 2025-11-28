from django.contrib import admin
from django.urls import reverse
from .models import BotUser, Order, OrderMedia
from django.utils.html import format_html


# Register your models here.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bot_user",
        "product",
        "total_pages",
        "copy_number",
        "total_price",
        "payment_type",
        "status_display",
        "language",
        "is_active",
        "created_at",
    )
    list_filter = (
        "status",
        "payment_type",
        "is_active",
        "created_at",
        "product__category",
    )
    search_fields = (
        "bot_user__name",
        "bot_user__username",
        "product__name",
        "product__name_uz",
        "product__name_ru",
        "product__name_en",
        "description",
    )
    ordering = ("-created_at",)

    def status_display(self, obj):
        """Display status with color coding"""
        colors = {
            "pending": "orange",
            "payment_pending": "blue",
            "payment_received": "purple",
            "payment_confirmed": "green",
            "in_progress": "teal",
            "ready": "darkgreen",
            "completed": "gray",
            "cancelled": "red",
        }
        color = colors.get(obj.status, "black")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_display.short_description = "Status"
    status_display.admin_order_field = "status"

    fieldsets = (
        (
            "Order Information",
            {
                "fields": (
                    "bot_user",
                    "product",
                    "language",
                    "description",
                    "status",
                    "is_active",
                )
            },
        ),
        (
            "Pricing & Files",
            {
                "fields": (
                    "total_pages",
                    "copy_number",
                    "total_price",
                    "payment_type",
                    "recipt",
                )
            },
        ),
        ("Files", {"fields": ("files",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ("created_at", "updated_at", "total_pages", "total_price")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("bot_user", "product")
            .prefetch_related("files")
        )


@admin.register(OrderMedia)
class OrderMediaAdmin(admin.ModelAdmin):
    list_display = ("file", "pages", "created_at")
    list_filter = ("created_at",)
    ordering = ("-created_at",)

    readonly_fields = ("pages", "created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request)
