from django.urls import path
from . import views

app_name = "webapp"

urlpatterns = [
    # HTML entry-point — subdomain-based (BotFather URL: https://{subdomain}.multilang.uz/webapp/)
    path("", views.webapp_index_subdomain, name="index_subdomain"),

    # HTML entry-point — legacy center_id-based URL (kept for backward compatibility)
    path("<int:center_id>/", views.webapp_index, name="index"),

    # JSON API — all require initData + center_id in the request body
    path("api/init/", views.api_init, name="api_init"),
    path("api/register/", views.api_register, name="api_register"),
    path("api/order/create/", views.api_create_order, name="api_create_order"),
    path("api/orders/", views.api_my_orders, name="api_my_orders"),
    path("api/orders/<int:order_id>/", views.api_order_detail, name="api_order_detail"),
    path("api/orders/<int:order_id>/receipt/", views.api_upload_receipt, name="api_upload_receipt"),

    # Profile view / update
    path("api/profile/", views.api_profile, name="api_profile"),

    # Center / branch info (about us, help, other services)
    path("api/center-info/", views.api_center_info, name="api_center_info"),

    # Price list for user's branch
    path("api/pricelist/", views.api_pricelist, name="api_pricelist"),
]
