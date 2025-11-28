# Translation Center

A comprehensive Telegram bot system for document translation and apostille services with per-page pricing and automated file processing.

## 🏗️ Architecture Overview

This project implements a complete translation center management system with:

- **Telegram Bot Integration** - User registration and service ordering
- **Per-Page Pricing System** - Dynamic pricing based on document content
- **Multi-Format File Processing** - PDF, DOCX, images, and text files
- **Multi-Language Support** - Uzbek, Russian, and English
- **Admin Management System** - Separate interfaces for bot users and internal staff

## 📊 Model Structure

### **Users Module**
- **`TelegramUser`** - Bot users (customers)
  - Fields: user_id, username, name, phone, language, step, is_active, is_agency
  - Purpose: Store and manage bot user data

- **`Accaunts`** - Internal users (admins, staff)
  - Fields: name, email, password, is_active, is_superuser
  - Purpose: Django authentication for internal management

### **Services Module**
- **`MainService`** - Service categories (Translation, Apostille)
- **`DocumentType`** - Document types with per-page pricing
- **Page counting utilities** - Automatic page detection

### **Orders Module**
- **`Order`** - Service orders linked to TelegramUser
- **`OrderFiles`** - Uploaded files with page counts
- **Automatic pricing calculation** based on pages and user type

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Django 5.2+
- Telegram Bot Token

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd translation-center
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables:**
```bash
cp .env.example .env
# Edit .env with your bot token and admin IDs
```

5. **Run migrations:**
```bash
python manage.py migrate
```

6. **Setup basic data:**
```bash
python manage.py setup_initial_data
```

7. **Run development server:**
```bash
python manage.py runserver
```

8. **Set webhook for bot:**
Update the webhook URL in `bot/bot.py`

## 📱 Bot Features

### User Registration
- Automatic user creation on /start
- Multi-language selection (UZ, RU, EN)
- Step-by-step registration with validation
- Phone number collection via contact button

### Service Ordering
- Per-page pricing system
- Automatic page counting from uploaded files
- Agency discounts
- Order tracking and management

### Supported File Types
- **PDF files** - Direct page counting
- **DOCX files** - Content-based estimation
- **Images** - 1 page per image
- **Text files** - Line-based estimation

## 🔧 Admin Features

### TelegramUser Management
- View all bot users and their data
- Filter by language, status, agency
- Search by name, username, phone
- Registration progress tracking

### Order Management
- View all orders with TelegramUser details
- File management with page counts
- Pricing and payment tracking
- Order status management

### Internal User Management
- Admin/staff account management
- Superuser permissions
- Internal system access

## 🌍 Multi-Language Support

The bot supports 3 languages with complete translations:
- **Uzbek** (uz) - Primary language
- **Russian** (ru) - Secondary language
- **English** (en) - International language

All messages, buttons, and responses are localized.

## 📋 API Endpoints

- **Bot Webhook:** `/bot/` - Handles Telegram bot updates
- **Admin Panel:** `/admin/` - Django admin interface

## 🛠️ Development

### Project Structure
```
translation-center/
├── bot/                    # Telegram bot application
│   ├── bot.py             # Main bot logic
│   ├── translations.py    # Multi-language translations
│   └── enhanced_bot.py    # Additional bot features
├── services/              # Core business logic
│   ├── models.py          # MainService, DocumentType
│   ├── bot_helpers.py     # Bot integration helpers
│   └── page_counter.py    # File processing utilities
├── users/                 # User management
│   ├── models.py          # TelegramUser, Accaunts, Order
│   └── admin.py           # Admin interfaces
├── core/                  # Django core settings
└── requirements.txt       # Python dependencies
```

### Key Commands
```bash
# Run tests
python test_bot.py

# Create migrations
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Setup initial data
python manage.py setup_initial_data

# Access admin
python manage.py createsuperuser
```

## 🔒 Security Features

- **User data separation** - Clear distinction between bot users and internal users
- **Input validation** - All user inputs are validated and sanitized
- **File upload security** - Safe file processing with type checking
- **Admin authentication** - Proper Django authentication system

## 📈 Production Deployment

1. **Environment Setup:**
   - Configure production database
   - Set secure bot token and admin IDs
   - Configure webhook URL

2. **Security:**
   - Use HTTPS for webhook
   - Set up proper file upload limits
   - Configure firewall and security groups

3. **Monitoring:**
   - Set up logging for bot interactions
   - Monitor database performance
   - Track user registration and order metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python test_bot.py`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the bot's help command
- Contact system administrators
- Review the documentation in BOT_IMPLEMENTATION.md

---

**Translation Center Bot** - Automated document translation and apostille services with intelligent pricing and file processing.
