# Permission Template Tags - Migration Guide

## Overview

A comprehensive permission template tag system has been implemented to provide a DRY approach for permission-based UI rendering. This replaces verbose inline permission checks with clean, reusable template tags.

## Files Created/Modified

### New Files
- `organizations/templatetags/__init__.py` - Package init
- `organizations/templatetags/permission_tags.py` - Permission template tags library

### Updated Templates (Examples)
1. ✅ `templates/partials/sidebar.html` - Navigation sidebar
2. ✅ `templates/orders/ordersList.html` - Orders list page
3. ✅ `templates/orders/orderDetail.html` - Order detail page (load added)

## Quick Reference

### Loading the Tags
```django
{% load permission_tags %}
```

### Available Tags

#### Simple Permission Check
```django
{% has_perm 'can_manage_orders' as can_manage %}
{% if can_manage %}...{% endif %}
```

#### Multiple Permissions (ANY)
```django
{% has_any_perm 'can_view_reports,can_view_analytics' as can_view %}
```

#### Multiple Permissions (ALL)
```django
{% has_all_perm 'can_edit_orders,can_delete_orders' as can_modify %}
```

#### Action-Based Check
```django
{% can_do 'orders.edit' as can_edit %}
{% can_do 'orders.delete' as can_delete %}
{% can_do 'payments.receive' as can_pay %}
```

#### Role Checks
```django
{% is_role 'owner' as is_owner_role %}
{% is_role 'manager' as is_mgr %}
{% is_at_least 'manager' as is_manager_or_above %}
```

#### Block Tags
```django
{% if_perm 'can_manage_orders' %}
    <button>Edit</button>
{% else_perm %}
    <span class="disabled">No Permission</span>
{% endif_perm %}

{% if_can_do 'orders.delete' %}
    <button class="btn-danger">Delete</button>
{% endif_can_do %}
```

### Available Actions (for `can_do`)

| Action | Required Permission(s) |
|--------|----------------------|
| `orders.view_all` | can_view_all_orders |
| `orders.view_own` | can_view_own_orders |
| `orders.create` | can_create_orders |
| `orders.edit` | can_edit_orders |
| `orders.delete` | can_delete_orders |
| `orders.assign` | can_assign_orders |
| `orders.update_status` | can_update_order_status |
| `orders.complete` | can_complete_orders |
| `orders.cancel` | can_cancel_orders |
| `payments.receive` | can_receive_payments |
| `payments.refund` | can_refund_orders |
| `payments.discount` | can_apply_discounts |
| `staff.view` | can_view_staff |
| `staff.manage` | can_manage_staff |
| `products.manage` | can_manage_products |
| `reports.view` | can_view_reports |
| `reports.financial` | can_view_financial_reports |
| `analytics.view` | can_view_analytics |
| `marketing.create_posts` | can_create_marketing_posts |
| `marketing.broadcast_branch` | can_send_branch_broadcasts |
| `marketing.broadcast_center` | can_send_center_broadcasts |

## Migration Checklist

### Templates Already Updated ✅
- [x] `templates/partials/sidebar.html`
- [x] `templates/orders/ordersList.html`
- [x] `templates/orders/orderDetail.html` (load statement added)

### Templates To Update 📋

#### High Priority (User-Facing Actions)
- [ ] `templates/orders/orderDetail.html` - Replace remaining inline checks
- [ ] `templates/orders/orderCreate.html` - Creation permissions
- [ ] `templates/orders/orderEdit.html` - Edit permissions

#### Organization Templates
- [ ] `templates/organizations/staff_list.html` - Staff management
- [ ] `templates/organizations/staff_form.html` - Staff create/edit
- [ ] `templates/organizations/role_form.html` - Role management
- [ ] `templates/organizations/branch_list.html` - Branch management
- [ ] `templates/organizations/center_list.html` - Center management

#### User Templates
- [ ] `templates/users/usersList.html` - Customer list
- [ ] `templates/users/userView.html` - Customer detail

#### Service Templates
- [ ] `templates/services/categoryList.html` - Categories
- [ ] `templates/services/productList.html` - Products

#### Report Templates
- [ ] `templates/reports/financial_reports.html`
- [ ] `templates/reports/order_reports.html`
- [ ] `templates/reports/staff_performance.html`
- [ ] `templates/reports/branch_comparison.html`
- [ ] `templates/reports/customer_analytics.html`

## Before/After Examples

### Before (Verbose)
```django
{% if permissions.can_view_reports or permissions.can_view_analytics or user.is_superuser %}
    <li><a href="{% url 'reports' %}">Reports</a></li>
{% endif %}
```

### After (Clean)
```django
{% has_any_perm 'can_view_reports,can_view_analytics' as can_reports %}
{% if can_reports %}
    <li><a href="{% url 'reports' %}">Reports</a></li>
{% endif %}
```

### Before (Role Check)
```django
{% if request.user.is_superuser or is_owner or is_manager %}
    <button>Edit</button>
{% endif %}
```

### After (Clean)
```django
{% is_at_least 'manager' as can_manage %}
{% if can_manage %}
    <button>Edit</button>
{% endif %}
```

### Before (Action Check)
```django
{% if permissions.can_delete_orders or user.is_superuser %}
    <button>Delete</button>
{% endif %}
```

### After (Clean)
```django
{% can_do 'orders.delete' as can_delete %}
{% if can_delete %}
    <button>Delete</button>
{% endif %}
```

## Testing

After updating templates, verify:
1. Superuser sees all elements
2. Owner sees owner-level elements
3. Manager sees manager-level elements
4. Staff sees only staff-level elements
5. Unauthenticated users see nothing restricted

## Notes

- The `{% load permission_tags %}` must be at the top of each template
- Tags automatically handle superuser (grants all permissions)
- Tags automatically handle is_owner context variable
- Action mapping is extensible in `permission_tags.py`
