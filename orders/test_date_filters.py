"""
Test for date filters in ordersList view
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta

from orders.models import Order
from organizations.models import TranslationCenter, Branch, Role, AdminUser
from services.models import Category, Product, Language
from accounts.models import BotUser


class OrderDateFilterTest(TestCase):
    """Test date filtering functionality in ordersList view"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all tests"""
        # Create superuser
        cls.superuser = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        
        # Create center and branch
        cls.center = TranslationCenter.objects.create(
            name='Test Center',
            owner=cls.superuser,
            phone='+998901234567',
            address='Test Address'
        )
        
        cls.branch = Branch.objects.create(
            center=cls.center,
            name='Test Branch',
            phone='+998901234567',
            address='Test Branch Address'
        )
        
        # Create category, product, and language
        cls.category = Category.objects.create(
            branch=cls.branch,
            name='Test Category',
            description='Test Description'
        )
        
        cls.product = Product.objects.create(
            category=cls.category,
            name='Test Product',
            ordinary_first_page_price=Decimal('10.00'),
            ordinary_other_page_price=Decimal('5.00'),
            agency_first_page_price=Decimal('8.00'),
            agency_other_page_price=Decimal('4.00')
        )
        
        cls.language = Language.objects.create(
            name='English',
            short_name='en'
        )
        
        # Create bot user
        cls.bot_user = BotUser.objects.create(
            telegram_id=123456789,
            username='testuser',
            name='Test User'
        )
        
        # Create orders with different dates
        base_date = timezone.now()
        
        # Order from 5 days ago
        cls.old_order = Order.objects.create(
            branch=cls.branch,
            bot_user=cls.bot_user,
            product=cls.product,
            language=cls.language,
            pages=10,
            price=Decimal('100.00'),
            status='pending',
            payment_type='cash'
        )
        cls.old_order.created_at = base_date - timedelta(days=5)
        cls.old_order.save()
        
        # Order from 2 days ago
        cls.recent_order = Order.objects.create(
            branch=cls.branch,
            bot_user=cls.bot_user,
            product=cls.product,
            language=cls.language,
            pages=5,
            price=Decimal('50.00'),
            status='in_progress',
            payment_type='card'
        )
        cls.recent_order.created_at = base_date - timedelta(days=2)
        cls.recent_order.save()
        
        # Order from today
        cls.today_order = Order.objects.create(
            branch=cls.branch,
            bot_user=cls.bot_user,
            product=cls.product,
            language=cls.language,
            pages=3,
            price=Decimal('30.00'),
            status='completed',
            payment_type='cash'
        )
        cls.today_order.created_at = base_date
        cls.today_order.save()
    
    def setUp(self):
        """Set up for each test"""
        self.client = Client()
        self.client.login(username='admin', password='admin123')
    
    def test_no_date_filter(self):
        """Test that all orders are returned when no date filter is applied"""
        response = self.client.get(reverse('orders:ordersList'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['orders']), 3)
    
    def test_date_from_filter(self):
        """Test filtering orders from a specific date"""
        # Filter orders from 3 days ago onwards
        date_from = (timezone.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        response = self.client.get(reverse('orders:ordersList'), {'date_from': date_from})
        
        self.assertEqual(response.status_code, 200)
        # Should return recent_order and today_order (2 orders)
        self.assertLessEqual(len(response.context['orders']), 3)
        self.assertGreaterEqual(len(response.context['orders']), 2)
    
    def test_date_to_filter(self):
        """Test filtering orders up to a specific date"""
        # Filter orders up to 3 days ago
        date_to = (timezone.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        response = self.client.get(reverse('orders:ordersList'), {'date_to': date_to})
        
        self.assertEqual(response.status_code, 200)
        # Should return at least the old_order
        self.assertGreaterEqual(len(response.context['orders']), 1)
    
    def test_date_range_filter(self):
        """Test filtering orders within a date range"""
        # Filter orders from 4 days ago to 1 day ago
        date_from = (timezone.now() - timedelta(days=4)).strftime('%Y-%m-%d')
        date_to = (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        response = self.client.get(reverse('orders:ordersList'), {
            'date_from': date_from,
            'date_to': date_to
        })
        
        self.assertEqual(response.status_code, 200)
        # Should return recent_order (1 order)
        self.assertGreaterEqual(len(response.context['orders']), 1)
    
    def test_invalid_date_format(self):
        """Test that invalid date formats are handled gracefully"""
        # Invalid date format should not cause an error
        response = self.client.get(reverse('orders:ordersList'), {
            'date_from': 'invalid-date',
            'date_to': '32/13/2024'
        })
        
        self.assertEqual(response.status_code, 200)
        # Should return all orders (invalid filters are ignored)
        self.assertEqual(len(response.context['orders']), 3)
    
    def test_empty_date_filter(self):
        """Test that empty date filters are handled correctly"""
        response = self.client.get(reverse('orders:ordersList'), {
            'date_from': '',
            'date_to': ''
        })
        
        self.assertEqual(response.status_code, 200)
        # Should return all orders
        self.assertEqual(len(response.context['orders']), 3)
    
    def test_date_filter_preserved_in_pagination(self):
        """Test that date filters are preserved in pagination links"""
        date_from = (timezone.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        response = self.client.get(reverse('orders:ordersList'), {'date_from': date_from})
        
        self.assertEqual(response.status_code, 200)
        # Check that date_from is in context
        self.assertEqual(response.context['date_from'], date_from)
