# Bulk Payment & Top Up - Quick Start Guide

## 🎯 Purpose
Process payments for agencies and customers with outstanding debts (borrowings) in bulk, using FIFO (First In, First Out) strategy.

## 🚪 Access
**Sidebar Menu** → **Bulk Payment & Top Up** (under Orders section)

Or

**Sidebar Menu** → **Reports** → **Payment History** (to view past payments)

## 👥 Who Can Use This?
- ✅ **Superusers**: Full access to all centers
- ✅ **Owners**: Access to their translation center
- ✅ **Managers**: Access to their branch
- ✅ **Staff with permission**: Users granted `can_manage_bulk_payments`

## 📋 Step-by-Step Usage

### Step 1: Select a Customer
You have two options:

**Option A: Top Debtors Table**
1. View the table showing customers with highest debts
2. Filter by customer type if needed (All/Agencies/Individuals)
3. Click on any row or the "Select" button

**Option B: Search**
1. Use the search box: "Or Search Customer"
2. Type name or phone number
3. Click on a search result

### Step 2: Review Customer Debt
After selection, you'll see:
- 📊 **Customer Info**: Name, phone, type (Agency/Individual)
- 💰 **Total Debt**: Outstanding amount across all orders
- 📦 **Orders**: Number of unpaid orders
- ⏱️ **Oldest Debt**: How many days the oldest order is unpaid
- 📄 **Order Details**: List of all outstanding orders with amounts

### Step 3: Enter Payment Details
1. **Payment Amount**: Enter the amount customer is paying
   - Can be partial or full payment
   - Must be greater than $0
2. **Payment Method**: Choose from:
   - Cash
   - Bank Transfer
   - Card Payment
   - Other
3. **Receipt/Note** (Optional): Add transaction ID or notes

### Step 4: Preview Distribution
1. Click **"Preview Distribution"** button
2. Review how payment will be applied:
   - ✅ Which orders will be paid (FIFO order)
   - ✅ Amount applied to each order
   - ✅ Which orders will be fully paid
   - ✅ Remaining debt after payment
   - ⚠️ Any unused payment amount

### Step 5: Process Payment
1. After reviewing preview, click **"Process Payment"**
2. Wait for confirmation
3. Success modal appears with:
   - Payment amount processed
   - Number of orders paid
   - Number of fully paid orders
   - Remaining debt

### Step 6: Next Action
Choose one:
- **Close**: Return to bulk payment page
- **Process Another Payment**: Reload page to process next customer

## 💡 Key Concepts

### FIFO Payment Distribution
**First In, First Out** - Oldest orders get paid first.

**Example:**
```
Customer has 3 orders:
├─ Order #100 (30 days old): $150 remaining
├─ Order #101 (15 days old): $200 remaining
└─ Order #102 (5 days old): $100 remaining
   Total: $450

Payment received: $300

Distribution:
1. Order #100 gets $150 → Fully Paid ✓
2. Order #101 gets $150 → $50 remaining
3. Order #102 gets $0 → Unchanged

Result: 1 fully paid, $150 total remaining
```

### Debt Color Codes
- 🔴 **Red (High)**: Over $1,000 - Urgent attention needed
- 🟠 **Orange (Medium)**: $500-$1,000 - Moderate priority
- 🟢 **Green (Low)**: Under $500 - Low priority

### Customer Types
- 🏢 **Agency (B2B)**: Business customers who place bulk orders
- 👤 **Individual (B2C)**: Individual customers

## 🎨 UI Elements Guide

### Top Debtors Table
```
┌─────────────────────────────────────────────────────┐
│ Customer │ Phone │ Type │ Total Debt │ Orders │ Action │
├─────────────────────────────────────────────────────┤
│ John Doe │ +123  │ 🏢   │ $1,250.00  │   8    │ Select │ ← Click row or button
├─────────────────────────────────────────────────────┤
│ Jane Ltd │ +456  │ 🏢   │ $850.00    │   5    │ Select │
└─────────────────────────────────────────────────────┘
```

### Customer Debt Summary Cards
```
┌──────────────┐  ┌────────────────┐  ┌──────────────┐
│ 👤 Customer  │  │ ⚠️ Total Debt  │  │ ⏱️ Oldest    │
│ John Doe     │  │ $1,250.00      │  │ 30 days      │
│ +1234567890  │  │ 8 orders       │  │              │
│ 🏢 Agency    │  │                │  │              │
└──────────────┘  └────────────────┘  └──────────────┘
```

### Outstanding Orders List
```
┌─────────────────────────────────────┐
│ 📄 Order #100                        │
│ Created: 2026-01-01 • 30 days old   │
│ ─────────────────────────────────── │
│ Product: Translation | Branch: Main │
│ ─────────────────────────────────── │
│ Total: $150.00 | Received: $0.00   │
│            Remaining: $150.00 ➤     │
└─────────────────────────────────────┘
```

### Payment Preview
```
┌─────────────────────────────────────┐
│ 📊 Payment Distribution Preview      │
├─────────────────────────────────────┤
│ Payment Amount: $300.00             │
│ Orders Affected: 2                  │
│ Fully Paid: 1                       │
│ Remaining Debt After: $150.00       │
├─────────────────────────────────────┤
│ FIFO Distribution:                  │
│                                     │
│ 1. Order #100 ✅ Fully Paid         │
│    -$150.00 → $0.00 remaining      │
│                                     │
│ 2. Order #101                       │
│    -$150.00 → $50.00 remaining     │
└─────────────────────────────────────┘
```

## ⚠️ Important Notes

### Payment Processing
- ✅ Payments are **irreversible** once processed
- ✅ Always **preview before processing**
- ✅ System uses **database transactions** (all or nothing)
- ✅ Complete **audit trail** maintained

### Order Status Updates
- When an order is fully paid, status automatically changes to "Payment Confirmed"
- Partial payments are tracked in the `received` field
- Payment history maintained for each order

### Data Visibility (RBAC)
- You only see customers within your access scope
- Superusers see everything
- Owners see their center
- Managers see their branch

## 🔍 Finding Past Payments

### Payment History Page
Access via: **Reports** → **Payment History**

Shows:
- All bulk payments processed
- Filter by customer or payment method
- Last 100 payments
- Click to view details

## 🆘 Troubleshooting

### "No outstanding orders found"
- Customer has no unpaid orders
- All orders are fully paid or cancelled

### "Permission denied"
- Contact admin to grant `can_manage_bulk_payments` permission
- Check if you're assigned to correct branch/center

### "Invalid payment amount"
- Amount must be greater than $0
- Check decimal format (use dot, not comma)

### Preview doesn't match expectations
- Review FIFO logic - oldest orders paid first
- Check if some orders have partial payments already

### Payment button doesn't appear
- Must click "Preview Distribution" first
- Ensure payment amount is valid

## 📞 Support

If you encounter issues:
1. Check this guide first
2. Review the detailed documentation: `BULK_PAYMENT_TOPPING_UP_IMPLEMENTATION.md`
3. Contact system administrator
4. Check audit logs if payment is not showing

## ✅ Best Practices

1. **Always Preview**: Never skip the preview step
2. **Verify Customer**: Double-check you selected the right customer
3. **Document Payment**: Use receipt/note field for reference numbers
4. **Regular Processing**: Process payments regularly to prevent large accumulations
5. **Follow Up**: Check payment history to confirm processing
6. **Communicate**: Inform customer of payment receipt
7. **Track Receipts**: Keep physical/digital receipt backups

## 🎓 Tips & Tricks

- **Keyboard Navigation**: Tab through form fields quickly
- **Search Shortcuts**: Start typing customer name for instant results
- **Filter Smart**: Use customer type filter to focus on agencies
- **Mobile Access**: Works on tablets and phones too
- **Bulk Days**: Schedule specific days for bulk payment processing
- **Priority First**: Sort top debtors table and handle largest debts first

## 📊 Reporting

After processing payments, check:
- **Finance Dashboard**: Updated revenue figures
- **Debtors Report**: Track remaining outstanding debts
- **Payment History**: Verify all transactions recorded
- **Order Reports**: See payment status updates

---

**Remember**: The system is designed to be intuitive, but when in doubt, always preview before processing!
