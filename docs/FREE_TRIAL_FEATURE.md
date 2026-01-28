# Free Trial Feature Implementation

## Overview
Added a complete free trial system to the billing module, allowing new customers to test the platform with a 10-day trial period before committing to a paid subscription.

## Changes Made

### 1. Database Models (billing/models.py)

#### Tariff Model
- Added `is_trial` field (BooleanField) - Marks tariff as a trial plan
- Added `trial_days` field (IntegerField) - Number of days for trial period (default: 10)

#### Subscription Model
- Added `is_trial` field (BooleanField) - Marks subscription as trial
- Added `trial_end_date` field (DateField) - When trial expires
- Updated `save()` method to auto-calculate trial dates
- Added trial-specific methods:
  - `is_trial_active()` - Check if trial is currently active
  - `trial_days_remaining()` - Calculate remaining trial days
  - `convert_trial_to_paid(tariff, pricing)` - Convert trial to paid subscription

### 2. Management Command
**File**: `billing/management/commands/create_trial_tariff.py`

Creates a "Free Trial" tariff with:
- 10-day trial period
- Limits: 2 branches, 5 staff, 50 monthly orders
- Price: $0.00 (completely free)
- Auto-activates immediately on creation

**Usage**:
```bash
python manage.py create_trial_tariff
```

### 3. Views (billing/views.py)

#### Updated `subscription_create()`
- Detects trial tariffs automatically
- For trials:
  - Pricing field not required
  - Auto-sets status to 'active'
  - Sets amount_paid to $0.00
  - Disables payment fields

#### New `convert_trial_to_paid()`
- Superuser-only view
- Converts trial subscription to paid plan
- Creates history entry for audit trail
- Validates trial status before conversion

### 4. Templates

#### subscription_detail.html
- Shows "Free Trial" badge for trial subscriptions
- Displays trial end date and days remaining
- Red warning when ≤3 days left
- "Convert to Paid" button for trials

#### subscription_create.html
- Auto-detects trial tariffs
- Disables pricing/payment fields for trials
- Shows "10-day free trial" notice
- JavaScript handles trial vs paid tariff switching

#### convert_trial.html (New)
- Dedicated conversion interface
- Shows current trial status
- Lists available paid tariffs
- Displays tariff limits before conversion
- Warning about payment collection

### 5. Admin Updates (billing/admin.py)

#### TariffAdmin
- Added `is_trial` and `trial_days` to list display
- Added "Trial Settings" fieldset
- Filter by trial status

#### SubscriptionAdmin
- Added "Trial Period" fieldset
- Shows `is_trial` and `trial_end_date`

### 6. URLs (billing/urls.py)
New endpoint:
```python
path('subscriptions/<int:pk>/convert-trial/', views.convert_trial_to_paid, name='convert_trial_to_paid')
```

### 7. Migration
**File**: `billing/migrations/0002_subscription_is_trial_subscription_trial_end_date_and_more.py`

Adds 4 new fields:
- `Tariff.is_trial`
- `Tariff.trial_days`
- `Subscription.is_trial`
- `Subscription.trial_end_date`

## Usage Workflow

### Creating a Trial Subscription
1. Superuser goes to `/billing/centers/`
2. Clicks "Create Subscription" for a center
3. Selects "Free Trial" tariff
4. Form auto-fills:
   - Duration: "10 days"
   - Status: "Active"
   - Amount: $0.00
5. Payment fields automatically disabled
6. Subscription created instantly

### Converting Trial to Paid
1. Navigate to trial subscription detail page
2. Click "Convert to Paid" button
3. Select desired paid tariff
4. Choose billing duration (1, 3, 6, or 12 months)
5. Review tariff limits
6. Confirm conversion
7. System:
   - Cancels trial
   - Creates new paid subscription
   - Sets status to "Pending" (awaiting payment)
   - Records conversion in history

### Trial Expiration
- Automatic status updates via `save()` method
- When trial_end_date passes:
  - Status changes to "Expired"
  - Organization loses access (enforced by decorators)
- Admin can manually extend or convert

## Free Trial Tariff Details
- **Name**: Free Trial
- **Slug**: free-trial
- **Duration**: 10 days (configurable)
- **Price**: $0.00
- **Limits**:
  - Max Branches: 2
  - Max Staff: 5
  - Max Monthly Orders: 50
- **Features**: All basic features included
- **Auto-activation**: Yes
- **Payment required**: No

## Testing Checklist
- [ ] Create free trial subscription for new center
- [ ] Verify trial auto-activates
- [ ] Check trial days countdown
- [ ] Test trial expiration (set trial_end_date to past)
- [ ] Convert trial to paid subscription
- [ ] Verify history entry created
- [ ] Test trial badge display
- [ ] Confirm payment fields disabled for trials
- [ ] Check admin interface shows trial fields

## Future Enhancements
1. **Auto-notification**: Email/SMS when trial expires in 3 days
2. **One-click upgrade**: In-app upgrade button for center owners
3. **Trial extensions**: Allow admins to extend trials
4. **Analytics**: Track trial-to-paid conversion rates
5. **Custom trial periods**: Per-center trial duration
6. **Trial reminders**: Daily countdown notifications
7. **Credit card capture**: Require card for trial (no charge)
8. **Auto-conversion**: Convert to paid at trial end if card on file

## Notes
- Trial tariff must exist before creating trial subscriptions
- Run `python manage.py create_trial_tariff` after deployment
- Only superusers can create/convert subscriptions
- Trial conversions create new subscription (old one cancelled)
- All trial activity logged in SubscriptionHistory
