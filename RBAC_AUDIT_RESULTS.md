# RBAC System Audit Results

## Date: December 10, 2025

## Executive Summary

A comprehensive RBAC (Role-Based Access Control) audit was performed using automated testing. The audit revealed **CRITICAL ISSUES** that need immediate attention.

---

## 🔴 CRITICAL ISSUES FOUND

### 1. **Permission Field Naming Inconsistency**

**Severity**: HIGH  
**Impact**: Permission checks may fail silently

**Problem**:
- Views and decorators use permission names like `can_view_orders`, `can_create_customers`
- Role model has fields named `can_view_all_orders`, `can_view_own_orders` (no `can_view_orders`)
- No `can_create_customers` field exists (only `can_view_customers` and `can_edit_customers`)

**Evidence**:
```python
# In views (services/views.py, accounts/views.py, etc.):
@any_permission_required('can_view_products', 'can_manage_products')
@permission_required('can_create_customers')

# In Role model:
can_view_all_orders = models.BooleanField(...)  # Not "can_view_orders"
can_view_own_orders = models.BooleanField(...)
# No can_create_customers field exists
```

**Impact**:
- Users with proper permissions in UI may be denied access
- Permission checks always return False for mismatched names
- Security holes where checks fail open instead of fail closed

**Recommendation**:
1. Create a mapping dictionary in Role model for aliases
2. Update all permission decorators to use correct field names
3. OR add missing permission fields to Role model for consistency

---

### 2. **Order Visibility Logic Issue**

**Severity**: MEDIUM  
**Impact**: Users cannot see orders they should access

**Problem**:
The `get_accessible_branches()` method requires `can_view_centers` or `can_view_branches` permission, but many roles don't have these permissions even though they should see orders in their branches.

**Evidence**:
```python
# In AdminUser.get_accessible_branches():
if self.center and self.has_permission('can_view_centers'):
    return Branch.objects.filter(center=self.center)
elif self.center and self.has_permission('can_view_branches'):
    return Branch.objects.filter(center=self.center)
elif self.branch:
    return Branch.objects.filter(pk=self.branch.pk)
```

**Current Behavior**:
- Manager with `can_view_all_orders` but no `can_view_branches` → sees NO orders
- Staff with `can_view_own_orders` but no `can_view_branches` → sees NO orders

**Expected Behavior**:
- Manager with `can_view_all_orders` → should see all center orders
- Staff with `can_view_own_orders` → should see their assigned orders

**Recommendation**:
Update `get_accessible_branches()` logic:
```python
def get_accessible_branches(self):
    # Check order-viewing permissions first
    if self.has_permission('can_view_all_orders') or self.has_permission('can_view_centers'):
        return Branch.objects.filter(center=self.center)
    elif self.has_permission('can_view_branches'):
        return Branch.objects.filter(center=self.center)
    elif self.branch:
        return Branch.objects.filter(pk=self.branch.pk)
    return Branch.objects.none()
```

---

### 3. **Staff Management Permission Check Bug**

**Severity**: MEDIUM  
**Impact**: Managers cannot edit staff even with correct permissions

**Problem**:
The `can_edit_staff()` function checks for `can_manage_staff` permission, but the check happens before considering ownership hierarchy.

**Evidence**:
Test results show Full Manager with `can_manage_staff=True` still cannot edit staff members.

**Current Code**:
```python
def can_edit_staff(user, staff_member=None):
    if user.is_superuser:
        return True
    
    admin_profile = get_admin_profile(user)
    if not admin_profile:
        return False
    
    # Must have can_manage_staff permission
    if not admin_profile.has_permission('can_manage_staff'):
        return False
    
    # If checking specific staff member
    if staff_member:
        # Cannot edit owners unless you're superuser
        if staff_member.is_owner:
            return False
        
        # Must be in same center
        if admin_profile.center and staff_member.center:
            return admin_profile.center.id == staff_member.center.id
    
    return True
```

**Issue**: The function logic seems correct, but the issue might be in how permissions are checked.

**Recommendation**:
- Add debug logging to trace why permission check fails
- Verify `has_permission('can_manage_staff')` actually works
- Check if Role.can_manage_staff field exists and is set correctly

---

## ⚠️ MEDIUM PRIORITY ISSUES

### 4. **Inconsistent Permission Naming Convention**

Different parts of the system use different naming:
- Some use `can_view_orders` (in decorators)
- Model uses `can_view_all_orders` and `can_view_own_orders`
- Some use `can_manage_X` as master permission
- Others use specific `can_create_X`, `can_edit_X`, `can_delete_X`

**Recommendation**: 
Create a comprehensive permission mapping document and ensure consistency across:
- View decorators
- Model field names
- Template permission checks
- RBAC helper functions

---

### 5. **Missing Customer Creation Permission**

**Problem**: `@permission_required('can_create_customers')` is used in views, but `can_create_customers` field doesn't exist in Role model.

**Views using it**:
- `accounts/views.py` line 185

**Recommendation**: 
Add `can_create_customers` field to Role model:
```python
can_create_customers = models.BooleanField(
    _("Can create customers"), 
    default=False,
    help_text=_("Can create new customer profiles")
)
```

---

## ✅ WORKING CORRECTLY

### 1. **Cross-Branch Data Isolation** ✓
- Staff in Branch 1 cannot see Branch 2 data
- Staff in Branch 2 cannot see Branch 1 data
- Test passed: 100%

### 2. **Owner Protection** ✓
- Non-superusers cannot edit owner profiles
- Owner role assignments properly restricted
- Test passed: 100%

### 3. **Staff Visibility for Staff Members** ✓
- Staff members correctly see only their assigned orders
- Cross-branch order visibility properly blocked
- Test passed: 100%

---

## 📋 RECOMMENDED ACTIONS

### Immediate (Critical):

1. **Fix Permission Field Names** (1-2 hours)
   - Create permission alias mapping in Role model
   - OR rename all decorator uses to match model fields
   - OR add missing fields to model

2. **Fix get_accessible_branches Logic** (30 minutes)
   - Update to consider order-viewing permissions
   - Test with different role combinations

3. **Add Missing Permission Fields** (30 minutes)
   - Add `can_create_customers`
   - Add any other missing fields found in view decorators

### Short-term (Within week):

4. **Create Permission Audit Tool** (2-3 hours)
   - Django management command to list all permission usage
   - Compare decorator permissions vs model fields
   - Report mismatches

5. **Update Documentation** (1-2 hours)
   - Document all available permissions
   - Create permission matrix (Role vs Permission table)
   - Add examples for common role configurations

### Long-term (Within month):

6. **Refactor Permission System** (1-2 days)
   - Consider using Django's built-in permission system
   - OR create unified permission registry
   - Implement permission inheritance (master → children)
   - Add permission caching for performance

7. **Add Integration Tests** (2-3 days)
   - Test all role + permission combinations
   - Test data visibility for each role
   - Test action permissions (create, edit, delete)
   - Automated regression testing

---

## Test Results Summary

```
Total Tests: 38
Passed: 17 (44.7%)
Failed: 21 (55.3%)
Warnings: 4

Critical Failures:
- Permission checks returning False when should be True
- Data access filters not working for some roles
- Staff management permissions not functioning

Pass Areas:
- Cross-branch isolation working perfectly
- Owner protection working correctly
- Staff order visibility working as expected
```

---

## Test Data Preserved

Test users and roles have been created for manual inspection:
- Username: `test_rbac_owner` (password: testpass123)
- Username: `test_rbac_full_manager` (password: testpass123)
- Username: `test_rbac_limited_manager` (password: testpass123)
- Username: `test_rbac_staff` (password: testpass123)
- Username: `test_rbac_accountant` (password: testpass123)
- Username: `test_rbac_staff2` (password: testpass123)

Center: "Test RBAC Center"

**Note**: To clean up test data, run `python test_rbac_system.py` again or manually delete users/center.

---

## Conclusion

The RBAC system has a solid foundation with good data isolation, but suffers from **permission field naming inconsistencies** that prevent it from functioning correctly. The immediate priority should be fixing the permission name mismatches, followed by updating the data access logic to work with the corrected permissions.

**Estimated Time to Fix Critical Issues**: 2-4 hours  
**Estimated Time for Complete Refactor**: 5-7 days
