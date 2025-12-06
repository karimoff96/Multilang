"""
Bot integration helpers for the translation center services
"""
import logging
from services.models import Category, Product
from orders.models import Order, OrderMedia
from accounts.models import BotUser
from services.page_counter import count_pages_from_uploaded_file
from bot.notification_service import send_order_notification
import os

logger = logging.getLogger(__name__)


class ServiceManager:
    """Helper class for managing services in the bot"""

    @staticmethod
    def get_categorys():
        """Get all active main services"""
        return Category.objects.filter(is_active=True)

    @staticmethod
    def get_products_by_category(category_id):
        """Get all active document types for a specific main service"""
        try:
            category = Category.objects.get(id=category_id, is_active=True)
            return category.product_set.filter(is_active=True)
        except Category.DoesNotExist:
            return Product.objects.none()

    @staticmethod
    def get_document_price(document_id, is_agency=False, pages=1):
        """Get price for a specific document based on user type and pages"""
        try:
            document = Product.objects.get(id=document_id, is_active=True)
            return document.get_price_for_user_type(is_agency, pages)
        except Product.DoesNotExist:
            return None

    @staticmethod
    def get_document_price_per_page(document_id, is_agency=False):
        """Get price per page for a specific document based on user type"""
        try:
            document = Product.objects.get(id=document_id, is_active=True)
            return document.get_price_per_page_for_user_type(is_agency)
        except Product.DoesNotExist:
            return None

    @staticmethod
    def search_documents_by_name(document_name):
        """Search document types by name"""
        return Product.objects.filter(name__icontains=document_name, is_active=True)

    @staticmethod
    def get_products():
        """Get all active document types"""
        return Product.objects.filter(is_active=True)

    @staticmethod
    def create_order(user_id, document_id, description="", files=None, pages=1):
        """Create an order for a user with file uploads"""
        try:
            user = BotUser.objects.get(user_id=user_id, is_active=True)
            document = Product.objects.get(id=document_id, is_active=True)

            # Create order
            order = Order.objects.create(
                bot_user=user,
                product=document,
                total_pages=pages,
                description=description,
                _update_pages=False,  # Don't update pages yet, we'll set them manually
            )

            # Add files if provided
            if files:
                order_files = []
                for file in files:
                    pages_count = count_pages_from_uploaded_file(file)
                    order_file = OrderMedia.objects.create(file=file, pages=pages_count)
                    order_files.append(order_file)

                # Add files to order
                order.files.set(order_files)

                # Update total pages
                order.update_total_pages()
                order.total_price = order.calculated_price
                order.save()
            
            # Send notification to Telegram channels
            try:
                send_order_notification(order.id)
            except Exception as e:
                logger.warning(f"Failed to send order notification for order {order.id}: {e}")

            return order
        except (BotUser.DoesNotExist, Product.DoesNotExist):
            return None

    @staticmethod
    def add_files_to_order(order_id, files):
        """Add files to an existing order and update page count and price"""
        try:
            order = Order.objects.get(id=order_id, is_active=False)

            order_files = []
            for file in files:
                pages_count = count_pages_from_uploaded_file(file)
                order_file = OrderMedia.objects.create(file=file, pages=pages_count)
                order_files.append(order_file)

            # Add files to order
            order.files.add(*order_files)

            # Update total pages and price
            order.update_total_pages()
            order.total_price = order.calculated_price
            order.save()

            return order
        except Order.DoesNotExist:
            return None

    @staticmethod
    def update_order_pages(order_id):
        """Recalculate pages and price for an order"""
        try:
            order = Order.objects.get(id=order_id)
            order.update_total_pages()
            order.total_price = order.calculated_price
            order.save()
            return order
        except Order.DoesNotExist:
            return None


def format_document_for_display(product):
    """Format document type information for bot display"""
    return {
        "id": product.id,
        "name": product.full_name,
        "category": product.category.name,
        "product": product.name,
        "complexity": product.get_complexity_level_display(),
        "service_category": product.service_category,
        "estimated_days": product.estimated_days,
        "price_per_page_user": float(product.price_per_page_user),
        "price_per_page_agency": float(product.price_per_page_agency),
        "min_pages": product.min_pages,
        "min_price_user": float(product.get_min_price_for_user_type(False)),
        "min_price_agency": float(product.get_min_price_for_user_type(True)),
        "description": product.description
        or f"{product.get_complexity_level_display()} {product.category.name.lower()} service",
    }


def get_user_friendly_price(price, is_agency=False, pages=1):
    """Get user-friendly price display"""
    if pages == 1:
        if is_agency:
            return f"Agency price: ${price}/page"
        return f"Regular price: ${price}/page"
    else:
        if is_agency:
            return f"Agency price: ${price} for {pages} pages (${price/pages:.2f}/page)"
        return f"Regular price: ${price} for {pages} pages (${price/pages:.2f}/page)"


def get_documents_for_user(user_id):
    """Get all available documents for a user"""
    try:
        user = BotUser.objects.get(user_id=user_id, is_active=True)
        return Product.objects.filter(is_active=True)
    except BotUser.DoesNotExist:
        return Product.objects.filter(is_active=True)
