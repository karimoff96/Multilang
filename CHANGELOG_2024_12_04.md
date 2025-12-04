# Changelog - December 4, 2025

## Marketing Module Fixes

### 1. ✅ Target Info Editable After Creation
**Files:** `marketing/views.py`, `templates/marketing/edit.html`

- Allow editing branches/centers for draft and scheduled posts
- Previously, target info was only editable during creation
- Now users can modify target audience until the post is sent

### 2. ✅ Fixed Recipient Count Showing 0
**Files:** `marketing/broadcast_service.py`

- Updated `get_recipients()` queryset to properly filter by branch/center FK
- Was using incorrect field lookup, now correctly queries `BotUser` by branch/center

### 3. ✅ Human-Readable Telegram Error Messages
**Files:** `marketing/broadcast_service.py`

- Added `get_friendly_error_message()` function
- Translates raw Telegram API errors to user-friendly messages
- Examples:
  - "bot was blocked by the user" → "User blocked the bot"
  - "chat not found" → "User deleted their Telegram account"
  - "user is deactivated" → "User's Telegram account is deactivated"

### 4. ✅ Improved Error Display in Admin UI
**Files:** `templates/marketing/detail.html`

- Added collapsible error details section
- Shows friendly error message prominently
- Technical details available via "Show Details" toggle
- Added tooltips explaining error types in recipient table

---

## Excel Export Upgrade

### 5. ✅ Created Comprehensive Export Service
**Files:** `core/export_service.py` (NEW - ~1400 lines)

- `ExcelExporter` class with multi-sheet support
- `ReportExporter` wrapper class with unified interface
- Styled headers (blue background, white bold text)
- Auto column widths based on content
- Proper data typing (dates, decimals, numbers)
- Frozen header rows
- Dynamic filenames with date range

### 6. ✅ Updated Export View
**Files:** `WowDash/reports_views.py`

- Replaced old CSV-only export with comprehensive Excel export
- Supports all 7 report types
- Full filter support (period, branch, center, status)
- Multi-tenant data isolation via RBAC

### 7. ✅ Added openpyxl Dependency
**Files:** `requirements.txt`

- Added `openpyxl==3.1.2` for Excel file generation

---

## Export Buttons Added to Templates

### 8. ✅ Orders Report
**Files:** `templates/reports/orders.html`

**Excel Sheets:**
- Orders (Detailed) - Full order data with 18 columns
- Status Breakdown - Orders grouped by status
- Language Breakdown - Orders grouped by language
- Daily Summary - Day-by-day totals

### 9. ✅ Financial Report
**Files:** `templates/reports/financial.html`

**Excel Sheets:**
- Revenue Summary - Key financial metrics
- Revenue by Status - Breakdown by order status
- Revenue by Branch - Performance per branch
- Revenue by Product - Sales per product
- Daily Revenue Trend - Day-by-day revenue
- Payment Details - Recent payments (top 500)

### 10. ✅ Staff Performance
**Files:** `templates/reports/staff_performance.html`

**Excel Sheets:**
- Staff Summary - All staff metrics
- Orders by Staff - Detailed orders assigned to staff
- Daily Staff Activity - Day-by-day staff performance

### 11. ✅ Branch Comparison
**Files:** `templates/reports/branch_comparison.html`

**Excel Sheets:**
- Branch Summary - All branches with KPIs
- Daily Branch Performance - Day-by-day per branch
- Branch Staff Details - Staff breakdown per branch

### 12. ✅ Customer Analytics
**Files:** `templates/reports/customers.html`

**Excel Sheets:**
- Customer Summary - Key customer metrics
- Top Customers - Top 50 by revenue
- Customer List - Detailed customer data (top 500)
- B2B vs B2C - Agency vs regular breakdown
- New Customers - Customers acquired in period

### 13. ✅ Unit Economy
**Files:** `templates/reports/unit_economy.html`

**Excel Sheets:**
- Summary - Overall remaining balance metrics
- By Branch - Outstanding per branch
- By Client Type - B2B vs B2C debts
- By Center - Outstanding per center
- Top Debtors - Top 100 customers with debt
- Outstanding Orders - Orders with remaining balance (top 500)

### 14. ✅ My Statistics
**Files:** `templates/reports/my_statistics.html`

**Excel Sheets:**
- Summary - Personal KPIs
- My Orders - All orders assigned to user
- Daily Performance - Day-by-day personal stats

---

## Testing Checklist

### Marketing Module
- [ ] Edit a draft/scheduled post → See Branch/Center selection fields
- [ ] View broadcast detail → Recipient count shows actual number (not 0)
- [ ] View failed broadcast → Error message is user-friendly
- [ ] View failed broadcast → Click "Show Details" for technical error

### Excel Exports
- [ ] Orders Report → Export Excel → Opens multi-sheet file
- [ ] Financial Report → Export Excel → Opens multi-sheet file
- [ ] Staff Performance → Export Excel → Opens multi-sheet file
- [ ] Branch Comparison → Export Excel → Opens multi-sheet file
- [ ] Customer Analytics → Export Excel → Opens multi-sheet file
- [ ] Unit Economy → Export Excel → Opens multi-sheet file
- [ ] My Statistics → Export Excel → Opens multi-sheet file

### Pre-requisites
```bash
pip install openpyxl==3.1.2
```

---

## Files Modified Summary

| File | Type | Changes |
|------|------|---------|
| `marketing/views.py` | Modified | Added centers/branches to edit context |
| `marketing/broadcast_service.py` | Modified | Fixed queryset, added friendly errors |
| `templates/marketing/edit.html` | Modified | Show target info for editable posts |
| `templates/marketing/detail.html` | Modified | Collapsible error display |
| `core/export_service.py` | **New** | Complete Excel export service |
| `WowDash/reports_views.py` | Modified | New export_report view |
| `requirements.txt` | Modified | Added openpyxl |
| `templates/reports/orders.html` | Modified | Export button with filters |
| `templates/reports/financial.html` | Modified | Export button with filters |
| `templates/reports/staff_performance.html` | Modified | Added export button |
| `templates/reports/branch_comparison.html` | Modified | Added export button |
| `templates/reports/customers.html` | Modified | Added export button |
| `templates/reports/unit_economy.html` | Modified | Added export button |
| `templates/reports/my_statistics.html` | Modified | Added export button |
