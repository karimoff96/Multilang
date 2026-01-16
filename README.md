# WEMARD - Translation Center Management System

A comprehensive **multi-tenant SaaS platform** for managing translation centers, with an integrated Telegram bot for customer ordering and a modern admin dashboard for business operations.

---

## 🎯 Project Summary

**WEMARD** is a complete business management solution designed for translation service companies. It enables:

- **Translation Center Owners** to manage multiple branches, staff, services, and track business performance
- **Customers** to order translation/apostille services via Telegram bot with automatic pricing
- **Staff Members** to process orders with role-based access control

### Core Value Proposition
- 🏢 **Multi-tenant Architecture** - One platform serves multiple translation centers with subdomain support
- 🤖 **Telegram Bot Integration** - Customers order directly through center-specific Telegram bots
- 📊 **Real-time Analytics** - Sales, revenue, and staff performance dashboards
- 🔐 **Role-Based Access Control (RBAC)** - Granular permissions for different user types
- 🌍 **Multi-language Support** - Uzbek, Russian, and English interfaces
- 📢 **Marketing Module** - Broadcast messages to customers via Telegram

---

## 🏗️ System Architecture

### User Hierarchy
```
Super Admin (Platform Owner)
    └── Translation Center Owner
            └── Branch
                    ├── Manager
                    └── Staff Members
```

### Main Modules

| Module | Description |
|--------|-------------|
| **Organizations** | Centers, Branches, Staff, Roles & Permissions |
| **Services** | Categories (Translation, Apostille), Products with pricing, Expenses |
| **Orders** | Order lifecycle, payments, file management, assignment |
| **Accounts** | Bot users (customers), Admin users, Agencies |
| **Core** | Regions, Districts, Audit Logs, Admin Notifications |
| **Marketing** | Marketing posts, Broadcast campaigns, Delivery tracking |
| **Bot** | Telegram integration for customer ordering (multi-tenant) |

---

## 👥 User Roles & Permissions

| Role | Access Level |
|------|--------------|
| **Super Admin** | Full platform access, manage all centers |
| **Owner** | Manage their center, all branches, staff, products |
| **Manager** | Manage assigned branch, view reports, assign orders |
| **Staff** | Process assigned orders, view personal statistics |

### Granular Permissions
- Center Management: `can_view_centers`, `can_create_centers`, `can_edit_centers`, `can_delete_centers`
- Branch Management: `can_view_branches`, `can_create_branches`, `can_edit_branches`, `can_delete_branches`
- Staff Management: `can_view_staff`, `can_create_staff`, `can_edit_staff`, `can_delete_staff`
- Order Management: `can_view_orders`, `can_create_orders`, `can_edit_orders`, `can_assign_orders`
- Marketing: `can_create_marketing_posts`, `can_send_branch_broadcasts`, `can_send_center_broadcasts`
- Reports: `can_view_reports`, `can_export_reports`
- Payments: `can_receive_payments`, `can_confirm_payments`

---

## 📱 Telegram Bot Features

### Customer Journey
1. **Start** → Language selection (UZ/RU/EN)
2. **Branch Selection** → Choose from center's branches
3. **Registration** → Name, phone number collection
4. **Service Selection** → Choose category (Translation/Apostille)
5. **Language Selection** → Choose target translation language
6. **Document Selection** → Choose document type
7. **Copy Selection** → Number of additional copies needed
8. **Document Upload** → Upload files (PDF, DOCX, images)
9. **Pricing** → Automatic page counting & price calculation
10. **Payment** → Cash or card with receipt upload
11. **Tracking** → Order status notifications

### Pricing System
- **Per-page pricing** - Dynamic pricing based on document pages
- **Agency discounts** - Special rates for agency customers
- **Copy pricing** - Additional copies at percentage rate
- **Static/Dynamic** - Fixed price or per-page options
- **Extra fees** - Rush fee, special handling

### Supported File Types
- PDF (automatic page counting)
- DOCX (content-based estimation)
- Images (JPG, PNG - 1 page each)
- Text files (line-based estimation)

---

## 🖥️ Admin Dashboard Features

### Dashboard Views
- **Main Dashboard** - Overview with key metrics
- **Sales Dashboard** - Revenue, orders, trends
- **Finance Dashboard** - Payments, pending amounts, debt tracking

### Management Sections
- **Organizations** - Centers, Branches, Staff, Roles
- **Customers** - Bot users with order history
- **Agencies** - Agency management with invitation links
- **Orders** - Full order lifecycle management
- **Services** - Categories, Products, Languages, Expenses
- **Marketing** - Broadcast campaigns and analytics
- **Reports** - Financial, Orders, Staff Performance

### UI Features
- 🌙 Dark/Light mode toggle
- 🌐 Multi-language interface (UZ/RU/EN)
- 📱 Responsive design
- 📊 Interactive charts (ApexCharts)
- 🔍 Advanced search and filtering
- 📄 Pagination with customizable page size
- 📤 Excel export for reports

---

## 🛠️ Technical Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Django 5.2, Python 3.10+ |
| **Database** | SQLite (dev), PostgreSQL (prod) |
| **Cache/State** | Redis (multi-worker support) |
| **Bot** | pyTelegramBotAPI (multi-tenant with webhooks) |
| **Frontend** | Bootstrap 5, jQuery, Iconify |
| **Charts** | ApexCharts |
| **Translations** | django-modeltranslation |
| **File Processing** | PyPDF2, python-docx, Pillow, python-magic |
| **Excel Export** | openpyxl |
| **Production** | Gunicorn, Nginx, Supervisor |

---

## 📁 Project Structure

```
WowDash/
├── accounts/           # Bot users (customers), authentication
│   ├── models.py       # BotUser, AdditionalInfo, BotUserState
│   ├── views.py        # Admin login, user management
│   └── management/     # Commands: cleanup_bot_states, generate_agency_link
├── bot/                # Telegram bot logic (multi-tenant)
│   ├── main.py         # Bot handlers and message processing
│   ├── handlers.py     # Handler registration for multi-tenant bots
│   ├── translations.py # Bot message translations
│   ├── notification_service.py  # Order notifications to channels
│   ├── persistent_state.py      # Redis-backed state management
│   └── management/     # Commands: run_bots, setup_webhooks
├── core/               # Core functionality
│   ├── models.py       # Region, District, AuditLog, AdminNotification
│   ├── audit.py        # Audit logging utilities
│   └── export_service.py # Excel export functionality
├── marketing/          # Marketing & broadcasts
│   ├── models.py       # MarketingPost, BroadcastRecipient
│   ├── broadcast_service.py # Telegram broadcast logic
│   └── views.py        # Marketing dashboard
├── orders/             # Order management
│   ├── models.py       # Order, OrderMedia, Receipt
│   ├── payment_service.py # Payment processing
│   └── views.py        # Order CRUD, assignment
├── organizations/      # Multi-tenant organization structure
│   ├── models.py       # TranslationCenter, Branch, Role, AdminUser
│   ├── rbac.py         # Role-based access control middleware
│   ├── middleware.py   # Subdomain-based tenant identification
│   └── views.py        # Center, Branch, Staff management
├── services/           # Services & pricing
│   ├── models.py       # Category, Product, Language, Expense
│   ├── analytics.py    # Unit economy analytics
│   ├── page_counter.py # Document page counting
│   └── bot_helpers.py  # Bot integration helpers
├── templates/          # HTML templates
├── static/             # CSS, JS, images
├── WowDash/            # Django project settings
│   ├── settings.py     # Configuration
│   ├── urls.py         # URL routing
│   ├── home_views.py   # Dashboard views
│   └── reports_views.py # Report views
├── manage.py
├── requirements.txt
├── README.md
├── PRODUCTION_DEPLOYMENT.md
└── USER_FLOW.md
```

---

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <repository>
cd WowDash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
cp .env.example .env
# Edit .env with your settings

# 4. Run migrations
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Setup initial data (optional)
python manage.py setup_initial_data
python manage.py setup_roles
python manage.py setup_regions

# 7. Run server
python manage.py runserver
```

---

## 🤖 Running Telegram Bots

### Development (Polling Mode)
```bash
python manage.py run_bots
```

### Production (Webhook Mode)
```bash
python manage.py setup_webhooks --base-url https://yourdomain.com
```

---

## 📊 Key Features Summary

### For Center Owners
✅ Multi-branch management  
✅ Staff management with roles  
✅ Product/service configuration  
✅ Revenue and sales analytics  
✅ Staff performance tracking  
✅ Marketing broadcasts  

### For Managers
✅ Branch operations oversight  
✅ Order assignment to staff  
✅ Daily/weekly reports  
✅ Customer management  

### For Staff
✅ Personal order queue  
✅ Order status updates  
✅ Personal statistics  

### For Customers (via Bot)
✅ Easy service ordering  
✅ Automatic price calculation  
✅ Copy number selection  
✅ Order tracking  
✅ Multi-language support  
✅ Payment options (cash/card)  

---

## 🔐 Security

- Django authentication system
- Role-based access control (RBAC)
- Branch-level data isolation
- Subdomain-based tenant separation
- Secure file upload handling
- Input validation and sanitization
- Audit logging for critical actions
- Redis-backed session management

---

## 📈 Analytics & Reports

- **Financial Reports** - Revenue by period, payment methods, debt tracking
- **Order Reports** - Status distribution, volume trends
- **Staff Performance** - Completed orders, average time
- **Customer Analytics** - New registrations, order frequency
- **Unit Economy** - Remaining balance, B2B vs B2C analysis

---

## 🌍 Internationalization

Full support for 3 languages:
- 🇺🇿 **Uzbek** (O'zbek) - Primary
- 🇷🇺 **Russian** (Русский) - Secondary
- 🇬🇧 **English** - International

Both admin interface and bot support language switching.

---

## 📞 Support

For questions and support, contact the system administrator.

---

**WEMARD** - Complete Translation Center Management Solution
