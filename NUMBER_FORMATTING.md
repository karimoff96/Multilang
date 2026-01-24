# Number Formatting Implementation Guide

## Overview
This document describes the number formatting system implemented across the WowDash application to improve readability of monetary values.

## Implementation Details

### 1. Backend Filters (Python)

**File**: `core/templatetags/number_filters.py`

Two main filters were updated/created:

#### `format_number` Filter
- **Purpose**: Format numbers with thousand separators using spaces for detailed views
- **Usage**: `{{ value|format_number }}`
- **Examples**:
  - `1234` → `1 234`
  - `1234567` → `1 234 567`
  - `1234567.89` → `1 234 567.89`

#### `short_number` Filter
- **Purpose**: Shorten large numbers with K/M suffixes for lists and statistics
- **Usage**: `{{ value|short_number }}`
- **Examples**:
  - `1234` → `1.2K`
  - `1234567` → `1.2M`
  - `10500000` → `11M` (rounded)

### 2. Frontend Utilities (JavaScript)

**File**: `static/js/numberFormat.js`

Provides consistent number formatting for dynamic content:

```javascript
// Format with separators
NumberFormat.formatWithSeparators(1234567) // "1 234 567"

// Shorten with K/M
NumberFormat.shorten(1234567) // "1.2M"

// Currency formatting
NumberFormat.formatCurrency(1234567, false) // "1 234 567 UZS"
NumberFormat.formatCurrency(1234567, true) // "1.2M UZS"
```

#### Data Attributes
Auto-format elements on page load using data attributes:

```html
<!-- Full format with separators -->
<span data-format="full">1234567</span> 
<!-- Becomes: 1 234 567 -->

<!-- Short format with K/M -->
<span data-format="short">1234567</span>
<!-- Becomes: 1.2M -->

<!-- Currency format -->
<span data-format="currency">1234567</span>
<!-- Becomes: 1 234 567 UZS -->

<!-- Short currency -->
<span data-format="currency" data-format-short="true">1234567</span>
<!-- Becomes: 1.2M UZS -->
```

### 3. Where to Use Each Format

#### Use `format_number` (Full Format with Spaces) For:
- ✅ **Detail Pages**: Order details, payment breakdowns
- ✅ **Forms**: Input display values
- ✅ **Receipts**: Payment amounts, totals
- ✅ **Reports**: Detailed financial data
- ✅ **Any context where precision matters**

**Examples**:
```django
<!-- Order Detail -->
<h4>{{ order.total_price|format_number }} UZS</h4>
<!-- Output: 1 234 567 UZS -->

<!-- Payment Receipt -->
<td>{{ receipt.amount|format_number }} UZS</td>
<!-- Output: 45 000 UZS -->
```

#### Use `short_number` (K/M Format) For:
- ✅ **Dashboard Cards**: Statistics, quick metrics
- ✅ **List Views**: Order lists, customer lists
- ✅ **Charts and Graphs**: Axis labels
- ✅ **Mobile Views**: Space-constrained displays
- ✅ **Summary Views**: Overview screens

**Examples**:
```django
<!-- Dashboard Card -->
<h6>{{ today_revenue|short_number }} UZS</h6>
<!-- Output: 1.2M UZS -->

<!-- Statistics -->
<span>{{ total_sales|short_number }}</span>
<!-- Output: 45K -->
```

### 4. Template Updates

All templates must load the filter at the top:

```django
{% load number_filters %}
```

**Updated Templates**:
- ✅ `templates/index.html` - Dashboard (short_number for stats)
- ✅ `templates/orders/orderDetail.html` - Order details (format_number)
- ✅ `templates/orders/orderEdit.html` - Order editing (format_number)
- ⚠️ `templates/orders/ordersList.html` - Needs updating
- ⚠️ `templates/orders/myOrders.html` - Needs updating
- ⚠️ `templates/orders/bulk_payment.html` - Partially updated

### 5. JavaScript Integration

The script is automatically loaded in all pages via `templates/partials/scripts.html`:

```html
<script src="/static/js/numberFormat.js"></script>
```

For dynamic content updates:

```javascript
// After AJAX call that updates prices
$.ajax({
    success: function(data) {
        $('#price').text(NumberFormat.formatWithSeparators(data.price));
        // or for short format:
        $('#total').text(NumberFormat.shorten(data.total));
        
        // Re-apply formatting to all data-format elements
        NumberFormat.applyFormatting();
    }
});
```

### 6. Migration Guide

**To update existing templates**:

1. Add the load tag at the top:
   ```django
   {% load number_filters %}
   ```

2. **For detail pages** (replace `floatformat:0`):
   ```django
   <!-- Before -->
   {{ order.total_price|floatformat:0 }} UZS
   
   <!-- After -->
   {{ order.total_price|format_number }} UZS
   ```

3. **For list/statistics pages**:
   ```django
   <!-- Before -->
   {{ today_revenue|floatformat:0 }} UZS
   
   <!-- After -->
   {{ today_revenue|short_number }} UZS
   ```

4. **For JavaScript dynamic content**:
   ```javascript
   // Before
   $('#amount').text(Math.round(amount) + ' UZS');
   
   // After
   $('#amount').text(NumberFormat.formatWithSeparators(amount) + ' UZS');
   ```

### 7. Testing

**Test Cases**:

| Input | format_number | short_number |
|-------|---------------|--------------|
| 999 | 999 | 999 |
| 1000 | 1 000 | 1K |
| 1500 | 1 500 | 1.5K |
| 10000 | 10 000 | 10K |
| 999999 | 999 999 | 1000K or 1M |
| 1000000 | 1 000 000 | 1M |
| 1234567 | 1 234 567 | 1.2M |
| 10000000 | 10 000 000 | 10M |

### 8. Browser Compatibility

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)  
- ✅ Safari (latest)
- ✅ Mobile browsers

Uses standard JavaScript `toLocaleString()` and regex for formatting.

### 9. Performance Notes

- Filters are cached by Django
- JavaScript formatting runs only on:
  - Page load (DOMContentLoaded)
  - Manual call to `NumberFormat.applyFormatting()`
- Minimal performance impact (<1ms per format operation)

### 10. Future Enhancements

Potential improvements:
- [ ] Add locale-aware formatting (different separators for different locales)
- [ ] Support for decimal precision configuration
- [ ] Billions (B) suffix for very large numbers
- [ ] Currency symbol configuration (not just UZS)
- [ ] RTL language support

## Summary

✅ **Detail pages**: Use `format_number` filter → `1 234 567`  
✅ **List/Stats pages**: Use `short_number` filter → `1.2M`  
✅ **JavaScript**: Use `NumberFormat` utility functions  
✅ **Auto-format**: Use `data-format` attributes

This creates consistent, readable number formatting throughout the application while maintaining precision where needed and brevity where appropriate.
