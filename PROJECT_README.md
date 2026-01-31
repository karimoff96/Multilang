# WowDash - Translation Management Platform

> Complete SaaS platform for translation service management with subscription billing and Telegram bot integration.

## 📁 Project Structure

```
Wow-dash/
├── accounts/               # User authentication and profiles
├── billing/                # Subscription billing system
│   ├── management/
│   │   └── commands/      # Legacy commands (use scripts/ instead)
│   ├── models.py          # Tariff, Subscription, UsageTracking
│   └── views.py           # Billing management views
├── bot/                    # Telegram bot integration
├── core/                   # Core order management
├── docs/                   # Project documentation
│   ├── README.md          # Main project documentation (3000+ lines)
│   ├── COMPLETE_DOCUMENTATION.md  # Consolidated billing/feature docs
│   ├── DEPLOYMENT_GUIDE.md
│   └── USER_GUIDE.md
├── landing/                # Public landing pages
├── marketing/              # Marketing campaigns
├── orders/                 # Order processing system
├── organizations/          # Multi-tenant organization management
├── scripts/                # Management and utility scripts
│   ├── manage_billing.py  # ⭐ Tariff setup and billing management
│   └── translation_utils.py  # Translation compilation
├── services/               # Service/product catalog
├── static/                 # Static assets (CSS, JS, images)
├── templates/              # Django templates
├── tests/                  # Test files
│   ├── test_features.py
│   ├── test_tariff_permissions.py
│   └── ...
└── WowDash/               # Project settings
    ├── settings.py
    ├── urls.py
    └── wsgi.py
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone repository
git clone <repository-url>
cd Wow-dash

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env  # Edit with your settings
```

### 2. Initialize Database

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Setup billing system (creates 5 tariff tiers)
python scripts/manage_billing.py setup-all
```

### 3. Run Development Server

```bash
python manage.py runserver
```

Visit: http://localhost:8000

## 📊 Billing System

### Tariff Tiers

| Tier | Price | Features | Limits |
|------|-------|----------|--------|
| Trial | FREE (14 days) | 35% | 1 branch, 2 staff, 50 orders/mo |
| Starter | $49/mo | 54% | 1 branch, 3 staff, 200 orders/mo |
| Professional ⭐ | $149/mo | 78% | 5 branches, 15 staff, 1K orders/mo |
| Business | $349/mo | 95% | 20 branches, 50 staff, 5K orders/mo |
| Enterprise | Custom | 100% | Unlimited |

### Management Commands

```bash
# Setup all tariff tiers
python scripts/manage_billing.py setup-tiers

# View feature comparison matrix
python scripts/manage_billing.py view-matrix

# Populate usage tracking
python scripts/manage_billing.py populate-usage

# Full setup (tiers + usage)
python scripts/manage_billing.py setup-all
```

## 🛠️ Utility Scripts

### Billing Management
```bash
python scripts/manage_billing.py [command]

Commands:
  setup-tiers     Create all 5 tariff tiers
  create-trial    Create trial tariff only
  populate-usage  Setup usage tracking
  view-matrix     Display feature comparison
  setup-all       Full setup
```

### Translation Utils
```bash
python scripts/translation_utils.py [command]

Commands:
  compile         Compile .po to .mo files
  check           Check for missing translations
```

## 📚 Documentation

- **[docs/README.md](docs/README.md)** - Main project documentation (3000+ lines)
  - Complete feature reference
  - Architecture details
  - Business model explanation
  
- **[docs/COMPLETE_DOCUMENTATION.md](docs/COMPLETE_DOCUMENTATION.md)** - Consolidated docs
  - Billing system details
  - Tariff strategy
  - Feature implementation guide
  
- **[docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - Production deployment
  
- **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** - End-user documentation

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific test file
python manage.py test tests.test_features

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

Test files are organized in `tests/` directory:
- `test_features.py` - Feature access tests
- `test_tariff_permissions.py` - Subscription permission tests
- `test_feature_translations.py` - Translation tests

## 🔑 Key Features

### Subscription-Based Access
- 5 tariff tiers with progressive feature unlocking
- 37 individual feature flags
- Automatic capacity limit enforcement
- Usage tracking and analytics

### Multi-Tenant Architecture
- Organization-based isolation
- Branch management
- Role-based access control (RBAC)
- Custom staff permissions

### Telegram Bot Integration
- Customer-facing order placement
- Automated notifications
- Webhook management
- Multi-language support

### Order Management
- Complete order lifecycle
- Payment tracking
- Receipt management
- File attachments
- Status tracking

## 🔧 Configuration

### Environment Variables

Create `.env` file with:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# For PostgreSQL (production):
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=wowdash
# DB_USER=postgres
# DB_PASSWORD=password
# DB_HOST=localhost
# DB_PORT=5432

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_WEBHOOK_URL=https://your-domain.com/bot/webhook/

# Static/Media
STATIC_URL=/static/
MEDIA_URL=/media/
```

## 📦 Dependencies

Main dependencies (see `requirements.txt` for full list):
- Django 5.2.7
- python-telegram-bot
- Pillow (image handling)
- python-dateutil
- django-filter

## 🚢 Deployment

### Quick Deployment Checklist

```bash
# 1. Backup database
python manage.py dumpdata > backup.json

# 2. Pull latest code
git pull origin main

# 3. Install/update dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Setup billing (if first time)
python scripts/manage_billing.py setup-tiers

# 6. Collect static files
python manage.py collectstatic --noinput

# 7. Restart server
systemctl restart gunicorn  # Or your WSGI server
```

See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for detailed production setup.

## 📝 Migration from Old Structure

If upgrading from previous version, note these changes:

### Files Moved/Consolidated

**Removed (functionality in `scripts/manage_billing.py`):**
- ~~`setup_tariff_tiers.py`~~ → `scripts/manage_billing.py setup-tiers`
- ~~`view_tariff_matrix.py`~~ → `scripts/manage_billing.py view-matrix`
- ~~`billing/management/commands/seed_tariffs.py`~~ → Use new script
- ~~`billing/management/commands/create_trial_tariff.py`~~ → Use new script

**Removed (functionality in `scripts/translation_utils.py`):**
- ~~`compile_messages.py`~~ → `scripts/translation_utils.py compile`
- ~~`compile_po.py`~~ → Use new script
- ~~`compile_po_simple.py`~~ → Use new script
- ~~`translate_po.py`~~ → Use new script

**Documentation Consolidated:**
- Multiple feature/billing docs → `docs/COMPLETE_DOCUMENTATION.md`
- Test reports moved to `tests/` directory

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Write/update tests
4. Update documentation
5. Submit pull request

## 📄 License

Proprietary - All rights reserved

## 📧 Support

- Documentation: See `docs/` directory
- Issues: GitHub issue tracker
- Email: support@wowdash.com

---

## 🎯 Common Tasks

### Adding a New Feature Flag

1. Add boolean field to `billing/models.py` Tariff model
2. Add to appropriate tier in `scripts/manage_billing.py`
3. Run: `python manage.py makemigrations billing`
4. Run: `python manage.py migrate`
5. Update: `python scripts/manage_billing.py setup-tiers`

### Creating Custom Tariff

```python
# In Django shell or script
from billing.models import Tariff

custom_tariff = Tariff.objects.create(
    slug='custom-plan',
    title='Custom Plan',
    max_branches=10,
    max_staff=25,
    feature_orders_basic=True,
    feature_orders_advanced=True,
    # ... enable desired features
)
```

### Checking Subscription Status

```python
# In view
organization = request.user.profile.center
subscription = organization.subscription

if subscription.is_active():
    # Check specific feature
    if subscription.has_feature('advanced_analytics'):
        # Show advanced analytics
        pass
```

---

**Version:** 2.0  
**Last Updated:** January 2026  
**Django Version:** 5.2.7  
**Python Version:** 3.10+
