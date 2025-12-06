# WowDash Project Commands Reference

## Server Management

### Gunicorn (Web Server)
```bash
# Reload gunicorn workers (graceful restart - applies code changes)
kill -HUP $(pgrep -f "gunicorn.*WowDash" | head -1)

# Check if gunicorn is running
ps aux | grep gunicorn

# View gunicorn logs
tail -f /var/log/wowdash/error.log
tail -f /var/log/wowdash/access.log
```

### Supervisor (Bot Process Manager)
```bash
# Restart all bots
sudo supervisorctl restart wowdash-bots

# Restart ALL supervisor-managed processes
sudo supervisorctl restart all

# Check bot status
sudo supervisorctl status wowdash-bots

# Check ALL processes status
sudo supervisorctl status

# Stop bots
sudo supervisorctl stop wowdash-bots

# Start bots
sudo supervisorctl start wowdash-bots

# View bot logs
sudo supervisorctl tail -f wowdash-bots
```

### Nginx (Reverse Proxy)
```bash
# Test nginx configuration
sudo nginx -t

# Reload nginx (apply config changes)
sudo systemctl reload nginx

# Restart nginx
sudo systemctl restart nginx

# Check nginx status
sudo systemctl status nginx
```

---

## Django Management Commands

### Database
```bash
# Activate virtual environment first
source venv/bin/activate

# Create new migrations after model changes
python manage.py makemigrations

# Apply pending migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Rollback migration (replace app_name and migration_number)
python manage.py migrate app_name migration_number
```

### Static Files
```bash
# Collect static files for production
python manage.py collectstatic --noinput
```

### User Management
```bash
# Create superuser
python manage.py createsuperuser

# Change user password
python manage.py changepassword username
```

### Django Shell
```bash
# Open Django shell
python manage.py shell

# Open Django shell with IPython (if installed)
python manage.py shell_plus
```

### Testing
```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test accounts
python manage.py test orders
python manage.py test organizations

# Run specific test class
python manage.py test orders.tests.PaymentTestCase
```

---

## Git Commands

```bash
# Pull latest changes
git pull

# Check status
git status

# Add all changes
git add .

# Commit with message
git commit -m "Your commit message"

# Push to remote
git push

# Switch branch
git checkout branch_name

# Create and switch to new branch
git checkout -b new_branch_name
```

---

## Bot Management

### Run Bots Manually (for debugging)
```bash
# Activate virtual environment
source venv/bin/activate

# Run all bots
python manage.py run_bots

# Run specific center's bot (by subdomain)
python manage.py run_bots --subdomain center_subdomain
```

### Check Bot Logs
```bash
# View supervisor logs
sudo tail -f /var/log/supervisor/wowdash-bots-stdout*.log
sudo tail -f /var/log/supervisor/wowdash-bots-stderr*.log
```

---

## Database Queries (Django Shell)

```bash
python manage.py shell
```

```python
# Common queries in Django shell

# Get all centers
from organizations.models import TranslationCenter
TranslationCenter.objects.all()

# Get all staff for a center
from organizations.models import AdminUser
AdminUser.objects.filter(center_id=1)

# Get all orders
from orders.models import Order
Order.objects.all().count()

# Get user by username
from django.contrib.auth.models import User
user = User.objects.get(username='admin')

# Get admin profile for user
user.admin_profile

# Check user permissions
user.admin_profile.role.can_view_orders
user.admin_profile.has_permission('can_view_orders')
```

---

## Environment

### Virtual Environment
```bash
# Activate
source venv/bin/activate

# Deactivate
deactivate

# Install requirements
pip install -r requirements.txt

# Update requirements file
pip freeze > requirements.txt
```

### Environment Variables
```bash
# View .env file
cat .env

# Edit .env file
nano .env
```

---

## Deployment Checklist

1. **Pull latest code:**
   ```bash
   git pull
   ```

2. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Install new dependencies (if any):**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations (if any):**
   ```bash
   python manage.py migrate
   ```

5. **Collect static files (if changed):**
   ```bash
   python manage.py collectstatic --noinput
   ```

6. **Reload gunicorn:**
   ```bash
   kill -HUP $(pgrep -f "gunicorn.*WowDash" | head -1)
   ```

7. **Restart bots (if bot code changed):**
   ```bash
   sudo supervisorctl restart wowdash-bots
   ```

---

## Troubleshooting

### Check for Python errors
```bash
# Check gunicorn error log
tail -100 /var/log/wowdash/error.log

# Check supervisor bot logs
sudo supervisorctl tail wowdash-bots stderr
```

### Check disk space
```bash
df -h
```

### Check memory usage
```bash
free -h
```

### Check running processes
```bash
htop
# or
top
```

### Check port usage
```bash
# Check what's using port 8000 (gunicorn)
sudo lsof -i :8000

# Check what's using port 80 (nginx)
sudo lsof -i :80
```

### Restart everything
```bash
# Full restart sequence
sudo supervisorctl restart wowdash-bots && kill -HUP $(pgrep -f "gunicorn.*WowDash" | head -1)

# Or with nginx reload
sudo supervisorctl restart wowdash-bots && kill -HUP $(pgrep -f "gunicorn.*WowDash" | head -1) && sudo systemctl reload nginx
```

### Quick Restart (Bots + Gunicorn)
```bash
# One-liner to restart both bots and web server
sudo supervisorctl restart wowdash-bots && kill -HUP $(pgrep -f "gunicorn.*WowDash" | head -1) && echo "✅ Bots and Gunicorn restarted"
```

---

## File Locations

| Component | Location |
|-----------|----------|
| Project Root | `/home/Wow-dash/` |
| Virtual Environment | `/home/Wow-dash/venv/` |
| Static Files | `/home/Wow-dash/staticfiles/` |
| Media Files | `/home/Wow-dash/media/` |
| Gunicorn Logs | `/var/log/wowdash/` |
| Supervisor Config | `/etc/supervisor/conf.d/` |
| Nginx Config | `/etc/nginx/sites-available/` |
