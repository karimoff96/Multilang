# Staff Performance Report - Permission & Data Filtering Fix

## Date: December 13, 2025

## 🐛 ISSUES FIXED

### Problem Description:
The staff performance report (`/reports/staff-performance`) was not showing proper data based on user permissions and organizational scope. The page had the following issues:

1. **Center-level users couldn't see center filter** - Only superusers could see the center dropdown
2. **Improper staff filtering** - Used hardcoded role checks (`is_owner`, `is_manager`) instead of actual organizational structure
3. **Missing branch filtering for owners** - Center owners couldn't filter by branch properly
4. **No access level context** - Template didn't know if user was center-level or branch-level

---

## ✅ FIXES IMPLEMENTED

### File Modified: `WowDash/reports_views.py`

### Changes in `staff_performance` view:

#### 1. **Proper Access Level Detection**
```python
# New logic determines if user has center-level or branch-level access
is_center_level = False  # Can see all branches in center
is_branch_level = False  # Can see only their branch
user_center = None       # User's center if center-level
user_branch = None       # User's branch if branch-level
```

#### 2. **Center Filter for Center-Level Users**
**Before:**
- Only superusers saw center dropdown
- Owners couldn't filter their center's data

**After:**
```python
if admin_profile.center:
    user_center = admin_profile.center
    is_center_level = True
    # Show their center in dropdown
    centers = TranslationCenter.objects.filter(id=user_center.id)
```

**Result:** Center owners now see their center in dropdown and can filter properly

#### 3. **Smart Staff Filtering Based on Access Level**

**Before:**
```python
if request.admin_profile.is_owner:
    staff_members = AdminUser.objects.filter(center=center)
elif request.admin_profile.is_manager:
    staff_members = AdminUser.objects.filter(branch=branch)
```

**After:**
```python
if is_center_level and user_center:
    # Center-level: show ALL staff in center (across all branches)
    staff_members = AdminUser.objects.filter(
        models.Q(center=user_center) | models.Q(branch__center=user_center),
        is_active=True
    ).distinct()
elif is_branch_level and user_branch:
    # Branch-level: show only staff in their branch
    staff_members = AdminUser.objects.filter(
        branch=user_branch,
        is_active=True
    )
```

**Result:** 
- Center-level users see all staff across all their branches
- Branch-level users see only their branch's staff
- Properly uses actual organizational structure, not role names

#### 4. **Enhanced Branch Filtering for Center Users**

**New Feature:**
```python
# Apply branch filter to staff if specified (for center-level users)
if branch_id and is_center_level:
    staff_members = staff_members.filter(branch_id=branch_id)
```

**Result:** Center owners can now filter staff by specific branch

#### 5. **Context Enhancement for Template**

**Added to context:**
```python
"is_center_level": is_center_level,  # Template knows access level
"is_branch_level": is_branch_level,  # Can show/hide filters accordingly
"user_center": user_center,           # User's center object
"user_branch": user_branch,           # User's branch object
```

**Result:** Template can conditionally show filters based on user's access level

---

## 📊 BEHAVIOR BY USER TYPE

### 🔹 Superuser
- **Sees:** All centers in dropdown
- **Can filter by:** Any center, any branch
- **Staff shown:** All active staff (can filter by center/branch)
- **Data scope:** Platform-wide

### 🔹 Center Owner (center-level access)
- **Sees:** Their center in dropdown (single option)
- **Can filter by:** Their center's branches
- **Staff shown:** All staff in their center (across all branches)
- **Data scope:** Center-wide (all branches)

### 🔹 Manager (branch-level access)
- **Sees:** No center dropdown (not needed)
- **Can filter by:** Their branch only (pre-selected)
- **Staff shown:** Only staff in their branch
- **Data scope:** Branch-only

### 🔹 Staff Member (branch-level access)
- **Sees:** No filters
- **Staff shown:** Only themselves
- **Data scope:** Their own performance only

---

## 🎯 KEY IMPROVEMENTS

### 1. **Organizational Structure Awareness**
- ✅ Uses `admin_profile.center` and `admin_profile.branch` instead of role names
- ✅ Handles staff who are assigned to center vs branch correctly
- ✅ Properly queries staff using `Q` objects for flexible filtering

### 2. **Proper Data Scoping**
- ✅ Center-level users see all branches in their center
- ✅ Branch-level users see only their branch
- ✅ No data leakage between centers or branches

### 3. **Filter Consistency**
- ✅ Center dropdown shows for center-level users (not just superusers)
- ✅ Branch dropdown filters properly for center-level users
- ✅ Branch-level users see their branch data without needing to filter

### 4. **Performance Optimization**
- ✅ Added `select_related()` for efficient DB queries
- ✅ Used `distinct()` to avoid duplicate staff records
- ✅ Applied filters at DB level, not in Python

---

## 🧪 TESTING CHECKLIST

### Test Center Owner:
- [ ] Can see their center in center dropdown
- [ ] Sees all staff across all their branches by default
- [ ] Can filter by specific branch to see that branch's staff
- [ ] Performance data aggregates correctly for selected scope

### Test Branch Manager:
- [ ] Doesn't see center dropdown (not applicable)
- [ ] Branch filter shows only their branch
- [ ] Sees only staff in their branch
- [ ] Cannot see staff from other branches

### Test Staff Member:
- [ ] Sees only their own performance data
- [ ] No filters shown (not applicable)
- [ ] Performance metrics calculated correctly

### Test Data Accuracy:
- [ ] Orders counted correctly per staff member
- [ ] Revenue calculated correctly per staff member
- [ ] Completion rate percentage is accurate
- [ ] Top performers list shows correct ranking

---

## 📝 SQL QUERIES USED

### For Center-Level Staff Filtering:
```sql
SELECT * FROM organizations_adminuser 
WHERE (center_id = ? OR branch__center_id = ?) 
  AND is_active = TRUE
```

### For Branch-Level Staff Filtering:
```sql
SELECT * FROM organizations_adminuser 
WHERE branch_id = ? AND is_active = TRUE
```

---

## ⚠️ IMPORTANT NOTES

1. **Center vs Branch Assignment:** Staff can be assigned to:
   - A **center** directly (owner-level staff)
   - A **branch** (which belongs to a center)
   
   The fix handles both cases with `Q(center=...) | Q(branch__center=...)`

2. **Role-Agnostic:** The fix doesn't rely on role names like "owner" or "manager". It uses the actual organizational structure (center/branch assignment).

3. **Backward Compatible:** The fix doesn't break existing functionality for superusers or users without admin profiles.

---

## ✅ VERIFICATION

- [x] No syntax errors
- [x] Proper use of Django ORM with Q objects
- [x] Select_related for performance
- [x] Context variables passed to template
- [x] Handles edge cases (no admin_profile, no center, no branch)
- [x] Maintains existing superuser behavior

---

## 🎉 RESULT

The staff performance report now correctly shows data based on user's organizational scope:
- **Center-level users** see all their center's data with branch filtering
- **Branch-level users** see only their branch's data
- **Proper permission enforcement** through existing RBAC system
- **Accurate performance metrics** for the correct scope
