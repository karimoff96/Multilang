from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Subscription management
    path('subscriptions/', views.subscription_list, name='subscription_list'),
    path('subscriptions/create/<int:center_id>/', views.subscription_create, name='subscription_create'),
    path('subscriptions/<int:pk>/', views.subscription_detail, name='subscription_detail'),
    path('subscriptions/<int:pk>/update-status/', views.subscription_update_status, name='subscription_update_status'),
    
    # Tariff management
    path('tariffs/', views.tariff_list, name='tariff_list'),
    
    # Usage tracking
    path('usage-tracking/', views.usage_tracking_list, name='usage_tracking'),
    
    # Centers with subscription status
    path('centers/', views.centers_list, name='centers_list'),
]
