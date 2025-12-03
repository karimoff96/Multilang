"""
URL configuration for orders app.
"""

from django.urls import path
from .views import (
    ordersList, orderDetail, orderEdit, updateOrderStatus, deleteOrder,
    assignOrder, unassignOrder, receivePayment, completeOrder,
    api_order_stats, api_branch_staff, myOrders
)

urlpatterns = [
    # Order list and detail
    path("", ordersList, name="ordersList"),
    path("my-orders/", myOrders, name="myOrders"),
    path("<int:order_id>/", orderDetail, name="orderDetail"),
    path("<int:order_id>/edit/", orderEdit, name="orderEdit"),
    
    # Order actions
    path("<int:order_id>/update-status/", updateOrderStatus, name="updateOrderStatus"),
    path("<int:order_id>/delete/", deleteOrder, name="deleteOrder"),
    path("<int:order_id>/assign/", assignOrder, name="assignOrder"),
    path("<int:order_id>/unassign/", unassignOrder, name="unassignOrder"),
    path("<int:order_id>/receive-payment/", receivePayment, name="receivePayment"),
    path("<int:order_id>/complete/", completeOrder, name="completeOrder"),
    
    # API endpoints
    path("api/stats/", api_order_stats, name="api_order_stats"),
    path("api/branch/<int:branch_id>/staff/", api_branch_staff, name="api_branch_staff"),
]
