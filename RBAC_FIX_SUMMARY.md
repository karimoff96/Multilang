# RBAC System Audit & Fix Summary

## Issues Found

### 1. **Missing Permission Decorators**
Many views have permission checks inside the function but no `@permission_required` decorator, making them accessible via URL manipulation.

### 2. **Template Permission Checks**
Sidebar menu items don't check `request.admin_profile.has_permission()` before showing links.

### 3. **Data Scope Issues**
Some views show all data instead of filtering by user's accessible branches/centers.

### 4. **Inconsistent Permission Usage**
- Some views check role names instead of permissions
- Some permission checks don't match available Role model fields

---

## Permission Matrix (from Role model)

### Centers
- `can_manage_centers` (full access)
- `can_view_centers`
- `can_create_centers`
- `can_edit_centers`
- `can_delete_centers`

### Branches
- `can_manage_branches` (full access)
- `can_view_branches`
- `can_create_branches`
- `can_edit_branches`
- `can_delete_branches`

### Staff
- `can_manage_staff` (full access)
- `can_view_staff`
- `can_create_staff`
- `can_edit_staff`
- `can_delete_staff`

### Orders
- `can_manage_orders` (full access)
- `can_view_all_orders` (all orders in scope)
- `can_view_own_orders` (only assigned orders)
- `can_create_orders`
- `can_edit_orders`
- `can_delete_orders`
- `can_assign_orders`
- `can_update_order_status`
- `can_complete_orders`
- `can_cancel_orders`

### Financial
- `can_manage_financial` (full access)
- `can_receive_payments`
- `can_view_financial_reports`
- `can_apply_discounts`
- `can_refund_orders`

### Reports
- `can_manage_reports` (full access)
- `can_view_reports`
- `can_view_analytics`
- `can_export_data`

### Products/Services
- `can_manage_products` (full access)
- `can_view_products`
- `can_create_products`
- `can_edit_products`
- `can_delete_products`

### Customers
- `can_manage_customers` (full access)
- `can_view_customers`
- `can_edit_customers`
- `can_delete_customers`

### Marketing
- `can_manage_marketing` (full access)
- `can_create_marketing_posts`
- `can_send_branch_broadcasts`
- `can_send_center_broadcasts`
- `can_view_broadcast_stats`

### Settings
- `can_manage_branch_settings`
- `can_view_branch_settings`

---

## Fixes Applied

### Phase 1: Critical Backend Fixes
- ✅ Fixed webhook handler to use bot with handlers
- ✅ Period filtering added to 5 pages
- ⏳ Add missing @permission_required decorators
- ⏳ Fix data scoping in views

### Phase 2: Template Fixes  
- ⏳ Add permission checks to sidebar menu
- ⏳ Hide action buttons based on permissions
- ⏳ Show/hide table columns based on permissions

### Phase 3: Testing
- ⏳ Test with limited user roles
- ⏳ Verify UI hides unauthorized sections
- ⏳ Verify backend rejects unauthorized actions

---

## How to Test RBAC

1. **Create test role** with specific permissions
2. **Create test user** with that role
3. **Login as test user**
4. **Verify:**
   - Sidebar only shows allowed menu items
   - Action buttons only show for allowed actions
   - Direct URL access to forbidden pages redirects
   - Data is properly scoped to user's branch/center

---

## Quick Permission Check Guide

For any view, ask:
1. **Who can access this?** → Add `@permission_required('can_...')`
2. **What data should they see?** → Use `get_user_orders()`, `get_user_branches()`, etc.
3. **What actions can they perform?** → Check permission before save/delete
4. **Should UI show this button?** → `{% if request.admin_profile.has_permission %}`
