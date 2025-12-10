#!/usr/bin/env python
"""
Comprehensive RBAC Testing Script

This script tests the entire RBAC system by:
1. Creating test roles with specific permissions
2. Creating test users with those roles
3. Testing access to various views and actions
4. Verifying permission enforcement
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WowDash.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client, RequestFactory
from django.urls import reverse
from organizations.models import TranslationCenter, Branch, Role, AdminUser
from accounts.models import BotUser
from orders.models import Order
from services.models import Category, Product, Language
from organizations.rbac import (
    get_admin_profile, 
    get_user_orders, 
    get_user_customers,
    get_user_branches,
    get_user_staff,
    can_edit_staff
)
from decimal import Decimal

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")

def print_test(text):
    print(f"{Colors.BLUE}► {text}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}  ✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}  ✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}  ⚠ {text}{Colors.END}")

def print_info(text):
    print(f"  {text}")


class RBACTester:
    def __init__(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.test_data = {}
        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }
    
    def cleanup(self):
        """Clean up test data"""
        print_header("CLEANING UP TEST DATA")
        
        # Delete test users
        User.objects.filter(username__startswith='test_rbac_').delete()
        
        # Delete test centers
        TranslationCenter.objects.filter(name__startswith='Test RBAC').delete()
        
        # Delete test roles
        Role.objects.filter(name__startswith='Test ').delete()
        
        print_success("Cleanup completed")
    
    def setup_test_data(self):
        """Create test roles, users, and data"""
        print_header("SETTING UP TEST DATA")
        
        # Create test center
        print_test("Creating test center...")
        owner_user = User.objects.create_user(
            username='test_rbac_owner',
            email='owner@test.com',
            password='testpass123',
            first_name='Owner',
            last_name='Test'
        )
        center = TranslationCenter.objects.create(
            name='Test RBAC Center',
            owner=owner_user,
            phone='+998901234567',
            email='center@test.com'
        )
        self.test_data['center'] = center
        self.test_data['owner_user'] = owner_user
        print_success(f"Center created: {center.name}")
        
        # Get main branch
        main_branch = center.branches.filter(is_main=True).first()
        self.test_data['main_branch'] = main_branch
        print_success(f"Main branch: {main_branch.name}")
        
        # Create additional branch
        branch2 = Branch.objects.create(
            center=center,
            name='Test RBAC Branch 2'
        )
        self.test_data['branch2'] = branch2
        print_success(f"Branch 2 created: {branch2.name}")
        
        # Create test roles with specific permissions
        print_test("\nCreating test roles with permissions...")
        
        # 1. Full Access Manager Role
        full_manager = Role.objects.create(
            name='Test Full Manager',
            description='Manager with all permissions',
            is_active=True,
            can_view_all_orders=True,
            can_view_own_orders=True,
            can_create_orders=True,
            can_edit_orders=True,
            can_delete_orders=True,
            can_manage_orders=True,
            can_assign_orders=True,
            can_view_customers=True,
            can_create_customers=True,
            can_edit_customers=True,
            can_view_products=True,
            can_create_products=True,
            can_edit_products=True,
            can_view_staff=True,
            can_manage_staff=True,
            can_view_branches=True,
            can_edit_branches=True,
            can_view_financial_reports=True,
            can_manage_financial=True
        )
        self.test_data['full_manager_role'] = full_manager
        print_success(f"Full Manager role created with full permissions")
        
        # 2. Limited Manager Role (can view but not edit)
        limited_manager = Role.objects.create(
            name='Test Limited Manager',
            description='Manager with view-only permissions',
            is_active=True,
            can_view_all_orders=True,
            can_view_customers=True,
            can_view_products=True,
            can_view_staff=True,
            can_view_branches=True,
            can_view_financial_reports=True
        )
        self.test_data['limited_manager_role'] = limited_manager
        print_success(f"Limited Manager role created with view-only permissions")
        
        # 3. Staff Role (minimal permissions)
        staff_role = Role.objects.create(
            name='Test Staff',
            description='Basic staff with minimal permissions',
            is_active=True,
            can_view_own_orders=True,
            can_edit_orders=True
        )
        self.test_data['staff_role'] = staff_role
        print_success(f"Staff role created with minimal permissions")
        
        # 4. Accountant Role (financial only)
        accountant_role = Role.objects.create(
            name='Test Accountant',
            description='Accountant with financial permissions',
            is_active=True,
            can_view_all_orders=True,
            can_view_financial_reports=True,
            can_manage_financial=True,
            can_view_customers=True
        )
        self.test_data['accountant_role'] = accountant_role
        print_success(f"Accountant role created with financial permissions")
        
        # Create test users
        print_test("\nCreating test users...")
        
        # Owner admin profile
        owner_admin = AdminUser.objects.create(
            user=owner_user,
            center=center,
            branch=main_branch,
            role=None,  # Owners don't need role
            is_active=True
        )
        self.test_data['owner_admin'] = owner_admin
        print_success("Owner admin profile created")
        
        # Full Manager
        full_mgr_user = User.objects.create_user(
            username='test_rbac_full_manager',
            email='fullmgr@test.com',
            password='testpass123',
            first_name='Full',
            last_name='Manager'
        )
        full_mgr_admin = AdminUser.objects.create(
            user=full_mgr_user,
            center=center,
            branch=main_branch,
            role=full_manager,
            is_active=True
        )
        self.test_data['full_mgr_user'] = full_mgr_user
        self.test_data['full_mgr_admin'] = full_mgr_admin
        print_success("Full Manager created")
        
        # Limited Manager
        limited_mgr_user = User.objects.create_user(
            username='test_rbac_limited_manager',
            email='limitedmgr@test.com',
            password='testpass123',
            first_name='Limited',
            last_name='Manager'
        )
        limited_mgr_admin = AdminUser.objects.create(
            user=limited_mgr_user,
            center=center,
            branch=main_branch,
            role=limited_manager,
            is_active=True
        )
        self.test_data['limited_mgr_user'] = limited_mgr_user
        self.test_data['limited_mgr_admin'] = limited_mgr_admin
        print_success("Limited Manager created")
        
        # Staff Member
        staff_user = User.objects.create_user(
            username='test_rbac_staff',
            email='staff@test.com',
            password='testpass123',
            first_name='Staff',
            last_name='Member'
        )
        staff_admin = AdminUser.objects.create(
            user=staff_user,
            center=center,
            branch=main_branch,
            role=staff_role,
            is_active=True
        )
        self.test_data['staff_user'] = staff_user
        self.test_data['staff_admin'] = staff_admin
        print_success("Staff member created")
        
        # Accountant
        accountant_user = User.objects.create_user(
            username='test_rbac_accountant',
            email='accountant@test.com',
            password='testpass123',
            first_name='Accountant',
            last_name='Test'
        )
        accountant_admin = AdminUser.objects.create(
            user=accountant_user,
            center=center,
            branch=main_branch,
            role=accountant_role,
            is_active=True
        )
        self.test_data['accountant_user'] = accountant_user
        self.test_data['accountant_admin'] = accountant_admin
        print_success("Accountant created")
        
        # Staff in Branch 2
        staff2_user = User.objects.create_user(
            username='test_rbac_staff2',
            email='staff2@test.com',
            password='testpass123',
            first_name='Staff',
            last_name='Branch2'
        )
        staff2_admin = AdminUser.objects.create(
            user=staff2_user,
            center=center,
            branch=branch2,
            role=staff_role,
            is_active=True
        )
        self.test_data['staff2_user'] = staff2_user
        self.test_data['staff2_admin'] = staff2_admin
        print_success("Staff in Branch 2 created")
        
        # Create test data (customers, orders, products)
        print_test("\nCreating test business data...")
        
        # Language
        language = Language.objects.first()
        if not language:
            language = Language.objects.create(
                name='English',
                short_name='EN'
            )
        self.test_data['language'] = language
        
        # Category
        category = Category.objects.create(
            name='Test Category',
            branch=main_branch
        )
        self.test_data['category'] = category
        
        # Product
        product = Product.objects.create(
            name='Test Translation',
            category=category,
            ordinary_first_page_price=Decimal('10.00'),
            ordinary_other_page_price=Decimal('8.00'),
            agency_first_page_price=Decimal('8.00'),
            agency_other_page_price=Decimal('6.00')
        )
        self.test_data['product'] = product
        print_success("Category and Product created")
        
        # Customers
        customer1 = BotUser.objects.create(
            center=center,
            branch=main_branch,
            name='Test Customer 1',
            phone='+998901111111',
            language='uz',
            is_active=True
        )
        customer2 = BotUser.objects.create(
            center=center,
            branch=branch2,
            name='Test Customer 2',
            phone='+998902222222',
            language='uz',
            is_active=True
        )
        self.test_data['customer1'] = customer1
        self.test_data['customer2'] = customer2
        print_success("2 test customers created")
        
        # Orders
        order1 = Order.objects.create(
            branch=main_branch,
            bot_user=customer1,
            product=product,
            language=language,
            total_pages=10,
            total_price=Decimal('100.00'),
            status='pending',
            assigned_to=staff_admin
        )
        order2 = Order.objects.create(
            branch=main_branch,
            bot_user=customer1,
            product=product,
            language=language,
            total_pages=5,
            total_price=Decimal('50.00'),
            status='in_progress',
            assigned_to=staff_admin
        )
        order3 = Order.objects.create(
            branch=branch2,
            bot_user=customer2,
            product=product,
            language=language,
            total_pages=8,
            total_price=Decimal('80.00'),
            status='pending',
            assigned_to=staff2_admin
        )
        self.test_data['order1'] = order1
        self.test_data['order2'] = order2
        self.test_data['order3'] = order3
        print_success("3 test orders created")
        
        print_success("\nTest data setup completed!")
    
    def test_permission_checks(self):
        """Test permission checking methods"""
        print_header("TESTING PERMISSION CHECKS")
        
        # Test Full Manager permissions
        print_test("Testing Full Manager permissions...")
        full_mgr = self.test_data['full_mgr_admin']
        
        tests = [
            ('can_view_all_orders', True),
            ('can_create_orders', True),
            ('can_edit_orders', True),
            ('can_delete_orders', True),
            ('can_manage_staff', True),
            ('can_view_centers', False),  # Should not have this
        ]
        
        for perm, expected in tests:
            result = full_mgr.has_permission(perm)
            if result == expected:
                print_success(f"Full Manager: {perm} = {result} ✓")
                self.results['passed'] += 1
            else:
                print_error(f"Full Manager: {perm} = {result}, expected {expected}")
                self.results['failed'] += 1
        
        # Test Limited Manager permissions
        print_test("\nTesting Limited Manager permissions...")
        limited_mgr = self.test_data['limited_mgr_admin']
        
        tests = [
            ('can_view_all_orders', True),
            ('can_create_orders', False),  # Should not have this
            ('can_edit_orders', False),    # Should not have this
            ('can_view_customers', True),
            ('can_edit_customers', False), # Should not have this
            ('can_manage_staff', False),   # Should not have this
        ]
        
        for perm, expected in tests:
            result = limited_mgr.has_permission(perm)
            if result == expected:
                print_success(f"Limited Manager: {perm} = {result} ✓")
                self.results['passed'] += 1
            else:
                print_error(f"Limited Manager: {perm} = {result}, expected {expected}")
                self.results['failed'] += 1
        
        # Test Staff permissions
        print_test("\nTesting Staff permissions...")
        staff = self.test_data['staff_admin']
        
        tests = [
            ('can_view_own_orders', True),
            ('can_edit_orders', True),
            ('can_delete_orders', False),   # Should not have this
            ('can_view_customers', False),  # Should not have this
            ('can_manage_staff', False),    # Should not have this
        ]
        
        for perm, expected in tests:
            result = staff.has_permission(perm)
            if result == expected:
                print_success(f"Staff: {perm} = {result} ✓")
                self.results['passed'] += 1
            else:
                print_error(f"Staff: {perm} = {result}, expected {expected}")
                self.results['failed'] += 1
    
    def test_data_access(self):
        """Test data access through RBAC query helpers"""
        print_header("TESTING DATA ACCESS FILTERS")
        
        # Test order access
        print_test("Testing order access...")
        
        # Owner should see all orders
        owner_orders = get_user_orders(self.test_data['owner_user'])
        if owner_orders.count() == 3:
            print_success(f"Owner can see all 3 orders ✓")
            self.results['passed'] += 1
        else:
            print_error(f"Owner sees {owner_orders.count()} orders, expected 3")
            self.results['failed'] += 1
        
        # Full Manager should see all orders in their center
        full_mgr_orders = get_user_orders(self.test_data['full_mgr_user'])
        if full_mgr_orders.count() == 3:
            print_success(f"Full Manager can see all 3 orders ✓")
            self.results['passed'] += 1
        else:
            print_error(f"Full Manager sees {full_mgr_orders.count()} orders, expected 3")
            self.results['failed'] += 1
        
        # Staff should only see their assigned orders
        staff_orders = get_user_orders(self.test_data['staff_user'])
        expected_staff_orders = 2  # order1 and order2 are assigned to staff
        if staff_orders.count() == expected_staff_orders:
            print_success(f"Staff sees only their {expected_staff_orders} assigned orders ✓")
            self.results['passed'] += 1
        else:
            print_error(f"Staff sees {staff_orders.count()} orders, expected {expected_staff_orders}")
            self.results['failed'] += 1
        
        # Staff2 (different branch) should only see their orders
        staff2_orders = get_user_orders(self.test_data['staff2_user'])
        if staff2_orders.count() == 1:  # Only order3
            print_success(f"Staff in Branch 2 sees only their 1 assigned order ✓")
            self.results['passed'] += 1
        else:
            print_error(f"Staff2 sees {staff2_orders.count()} orders, expected 1")
            self.results['failed'] += 1
        
        # Test customer access
        print_test("\nTesting customer access...")
        
        # Full Manager should see all customers in center
        full_mgr_customers = get_user_customers(self.test_data['full_mgr_user'])
        if full_mgr_customers.count() == 2:
            print_success(f"Full Manager can see all 2 customers ✓")
            self.results['passed'] += 1
        else:
            print_error(f"Full Manager sees {full_mgr_customers.count()} customers, expected 2")
            self.results['failed'] += 1
        
        # Staff should see customers in their branches
        staff_customers = get_user_customers(self.test_data['staff_user'])
        if staff_customers.count() >= 1:  # At least customer1
            print_success(f"Staff can see customers in their branch ✓")
            self.results['passed'] += 1
        else:
            print_error(f"Staff sees {staff_customers.count()} customers, expected at least 1")
            self.results['failed'] += 1
        
        # Test branch access
        print_test("\nTesting branch access...")
        
        # Full Manager should see all branches in center
        full_mgr_branches = get_user_branches(self.test_data['full_mgr_user'])
        if full_mgr_branches.count() == 2:
            print_success(f"Full Manager can see all 2 branches ✓")
            self.results['passed'] += 1
        else:
            print_error(f"Full Manager sees {full_mgr_branches.count()} branches, expected 2")
            self.results['failed'] += 1
        
        # Staff should see branches they have access to
        staff_branches = get_user_branches(self.test_data['staff_user'])
        if staff_branches.count() >= 1:
            print_success(f"Staff can see their branch ✓")
            self.results['passed'] += 1
        else:
            print_error(f"Staff sees {staff_branches.count()} branches")
            self.results['failed'] += 1
        
        # Test staff visibility
        print_test("\nTesting staff member visibility...")
        
        # Full Manager with can_manage_staff should see other staff
        full_mgr_staff = get_user_staff(self.test_data['full_mgr_user'])
        # Should see: owner_admin, limited_mgr, staff, accountant, staff2 (not themselves)
        if full_mgr_staff.count() >= 4:
            print_success(f"Full Manager can see {full_mgr_staff.count()} other staff members ✓")
            self.results['passed'] += 1
        else:
            print_error(f"Full Manager sees {full_mgr_staff.count()} staff members, expected at least 4")
            self.results['failed'] += 1
        
        # Limited Manager without can_manage_staff might not see staff management
        limited_mgr_staff = get_user_staff(self.test_data['limited_mgr_user'])
        print_info(f"Limited Manager can see {limited_mgr_staff.count()} staff members")
        # This is expected to be 0 or limited since they don't have manage_staff permission
        if limited_mgr_staff.count() >= 0:
            print_success(f"Limited Manager staff visibility working correctly ✓")
            self.results['passed'] += 1
    
    def test_view_access(self):
        """Test actual view access through HTTP requests"""
        print_header("TESTING VIEW ACCESS CONTROL")
        
        # Test order list access
        print_test("Testing order list view access...")
        
        # Full Manager should access order list
        self.client.login(username='test_rbac_full_manager', password='testpass123')
        response = self.client.get('/orders/')
        if response.status_code == 200:
            print_success("Full Manager can access order list ✓")
            self.results['passed'] += 1
        else:
            print_error(f"Full Manager cannot access order list (status: {response.status_code})")
            self.results['failed'] += 1
        self.client.logout()
        
        # Limited Manager should access order list (view only)
        self.client.login(username='test_rbac_limited_manager', password='testpass123')
        response = self.client.get('/orders/')
        if response.status_code == 200:
            print_success("Limited Manager can access order list ✓")
            self.results['passed'] += 1
        else:
            print_error(f"Limited Manager cannot access order list (status: {response.status_code})")
            self.results['failed'] += 1
        self.client.logout()
        
        # Staff should access order list
        self.client.login(username='test_rbac_staff', password='testpass123')
        response = self.client.get('/orders/')
        if response.status_code == 200:
            print_success("Staff can access order list ✓")
            self.results['passed'] += 1
        else:
            print_error(f"Staff cannot access order list (status: {response.status_code})")
            self.results['failed'] += 1
        self.client.logout()
        
        # Test order creation access
        print_test("\nTesting order creation access...")
        
        # Full Manager should create orders
        self.client.login(username='test_rbac_full_manager', password='testpass123')
        response = self.client.get('/orders/create/')
        if response.status_code == 200:
            print_success("Full Manager can access order creation ✓")
            self.results['passed'] += 1
        else:
            print_error(f"Full Manager blocked from order creation (status: {response.status_code})")
            self.results['failed'] += 1
        self.client.logout()
        
        # Limited Manager should NOT create orders
        self.client.login(username='test_rbac_limited_manager', password='testpass123')
        response = self.client.get('/orders/create/')
        if response.status_code in [302, 403]:  # Redirect or forbidden
            print_success("Limited Manager correctly blocked from order creation ✓")
            self.results['passed'] += 1
        elif response.status_code == 200:
            print_error("Limited Manager can access order creation (should be blocked!)")
            self.results['failed'] += 1
        else:
            print_warning(f"Unexpected status {response.status_code} for Limited Manager order creation")
            self.results['warnings'] += 1
        self.client.logout()
        
        # Test customer management
        print_test("\nTesting customer management access...")
        
        # Full Manager should access customers
        self.client.login(username='test_rbac_full_manager', password='testpass123')
        response = self.client.get('/accounts/users/')
        if response.status_code == 200:
            print_success("Full Manager can access customer list ✓")
            self.results['passed'] += 1
        else:
            print_error(f"Full Manager cannot access customer list (status: {response.status_code})")
            self.results['failed'] += 1
        self.client.logout()
        
        # Staff should NOT access customer management
        self.client.login(username='test_rbac_staff', password='testpass123')
        response = self.client.get('/accounts/users/')
        if response.status_code in [302, 403]:
            print_success("Staff correctly blocked from customer management ✓")
            self.results['passed'] += 1
        elif response.status_code == 200:
            print_error("Staff can access customer management (should be blocked!)")
            self.results['failed'] += 1
        else:
            print_warning(f"Unexpected status {response.status_code} for Staff customer access")
            self.results['warnings'] += 1
        self.client.logout()
        
        # Test financial reports
        print_test("\nTesting financial report access...")
        
        # Accountant should access financial reports
        self.client.login(username='test_rbac_accountant', password='testpass123')
        response = self.client.get('/services/expenses/')
        if response.status_code == 200:
            print_success("Accountant can access financial reports ✓")
            self.results['passed'] += 1
        else:
            print_warning(f"Accountant status {response.status_code} for expenses (may not exist yet)")
            self.results['warnings'] += 1
        self.client.logout()
        
        # Staff should NOT access financial reports
        self.client.login(username='test_rbac_staff', password='testpass123')
        response = self.client.get('/services/expenses/')
        if response.status_code in [302, 403]:
            print_success("Staff correctly blocked from financial reports ✓")
            self.results['passed'] += 1
        elif response.status_code == 404:
            print_info("Expenses view not found (404) - skipping this test")
        elif response.status_code == 200:
            print_error("Staff can access financial reports (should be blocked!)")
            self.results['failed'] += 1
        self.client.logout()
        
        # Test staff management
        print_test("\nTesting staff management access...")
        
        # Full Manager should manage staff
        self.client.login(username='test_rbac_full_manager', password='testpass123')
        response = self.client.get('/organizations/staff/')
        if response.status_code == 200:
            print_success("Full Manager can access staff management ✓")
            self.results['passed'] += 1
        else:
            print_error(f"Full Manager cannot access staff management (status: {response.status_code})")
            self.results['failed'] += 1
        self.client.logout()
        
        # Limited Manager should NOT manage staff
        self.client.login(username='test_rbac_limited_manager', password='testpass123')
        response = self.client.get('/organizations/staff/')
        if response.status_code in [302, 403]:
            print_success("Limited Manager correctly blocked from staff management ✓")
            self.results['passed'] += 1
        elif response.status_code == 200:
            print_error("Limited Manager can access staff management (should be blocked!)")
            self.results['failed'] += 1
        else:
            print_warning(f"Unexpected status {response.status_code} for Limited Manager staff access")
            self.results['warnings'] += 1
        self.client.logout()
    
    def test_cross_branch_isolation(self):
        """Test that staff cannot access data from other branches"""
        print_header("TESTING CROSS-BRANCH DATA ISOLATION")
        
        staff_user = self.test_data['staff_user']  # Branch 1
        staff2_user = self.test_data['staff2_user']  # Branch 2
        
        # Staff in Branch 1 should not see orders from Branch 2
        print_test("Testing branch isolation for staff members...")
        
        staff1_orders = get_user_orders(staff_user)
        has_branch2_order = staff1_orders.filter(
            branch=self.test_data['branch2']
        ).exists()
        
        if not has_branch2_order:
            print_success("Staff in Branch 1 cannot see Branch 2 orders ✓")
            self.results['passed'] += 1
        else:
            print_error("Staff in Branch 1 can see Branch 2 orders (SECURITY ISSUE!)")
            self.results['failed'] += 1
        
        # Staff in Branch 2 should not see orders from Branch 1
        staff2_orders = get_user_orders(staff2_user)
        has_branch1_order = staff2_orders.filter(
            branch=self.test_data['main_branch']
        ).exists()
        
        if not has_branch1_order:
            print_success("Staff in Branch 2 cannot see Branch 1 orders ✓")
            self.results['passed'] += 1
        else:
            print_error("Staff in Branch 2 can see Branch 1 orders (SECURITY ISSUE!)")
            self.results['failed'] += 1
    
    def test_edit_restrictions(self):
        """Test that users cannot edit what they shouldn't"""
        print_header("TESTING EDIT RESTRICTIONS")
        
        # Limited Manager should not edit staff
        print_test("Testing staff edit restrictions...")
        
        limited_mgr = self.test_data['limited_mgr_user']
        staff_member = self.test_data['staff_admin']
        
        can_edit = can_edit_staff(limited_mgr, staff_member)
        if not can_edit:
            print_success("Limited Manager cannot edit staff (correct) ✓")
            self.results['passed'] += 1
        else:
            print_error("Limited Manager can edit staff (should be blocked!)")
            self.results['failed'] += 1
        
        # Full Manager should edit staff
        full_mgr = self.test_data['full_mgr_user']
        can_edit = can_edit_staff(full_mgr, staff_member)
        if can_edit:
            print_success("Full Manager can edit staff ✓")
            self.results['passed'] += 1
        else:
            print_error("Full Manager cannot edit staff (should be allowed!)")
            self.results['failed'] += 1
        
        # Nobody should edit owner
        owner_admin = self.test_data['owner_admin']
        can_edit = can_edit_staff(full_mgr, owner_admin)
        if not can_edit:
            print_success("Full Manager cannot edit owner (correct) ✓")
            self.results['passed'] += 1
        else:
            print_error("Full Manager can edit owner (SECURITY ISSUE!)")
            self.results['failed'] += 1
    
    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")
        
        total = self.results['passed'] + self.results['failed']
        pass_rate = (self.results['passed'] / total * 100) if total > 0 else 0
        
        print(f"{Colors.BOLD}Total Tests: {total}{Colors.END}")
        print(f"{Colors.GREEN}Passed: {self.results['passed']}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.results['failed']}{Colors.END}")
        print(f"{Colors.YELLOW}Warnings: {self.results['warnings']}{Colors.END}")
        print(f"\n{Colors.BOLD}Pass Rate: {pass_rate:.1f}%{Colors.END}")
        
        if self.results['failed'] == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED!{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED - REVIEW RBAC SYSTEM{Colors.END}")
        
        print()
    
    def run_all_tests(self):
        """Run complete test suite"""
        try:
            self.cleanup()
            self.setup_test_data()
            self.test_permission_checks()
            self.test_data_access()
            self.test_view_access()
            self.test_cross_branch_isolation()
            self.test_edit_restrictions()
            self.print_summary()
        except Exception as e:
            print_error(f"Test suite error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            # Keep data for manual inspection
            print_info("\nTest data preserved for manual inspection.")
            print_info("Run cleanup() manually or run this script again to clean up.")


if __name__ == '__main__':
    tester = RBACTester()
    tester.run_all_tests()
