from django.urls import path
from . import views

urlpatterns = [
    # Categories
    path("categories/", views.categoryList, name="categoryList"),
    path("categories/add/", views.addCategory, name="addCategory"),
    path("categories/<int:category_id>/", views.categoryDetail, name="categoryDetail"),
    path("categories/<int:category_id>/edit/", views.editCategory, name="editCategory"),
    path("categories/<int:category_id>/delete/", views.deleteCategory, name="deleteCategory"),
    
    # Products
    path("products/", views.productList, name="productList"),
    path("products/add/", views.addProduct, name="addProduct"),
    path("products/<int:product_id>/", views.productDetail, name="productDetail"),
    path("products/<int:product_id>/edit/", views.editProduct, name="editProduct"),
    path("products/<int:product_id>/delete/", views.deleteProduct, name="deleteProduct"),
]
