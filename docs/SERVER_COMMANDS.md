# Server Commands Reference

Quick reference for all production server commands.

---

## Django Application

### Start/Stop/Restart
```bash
# Via Supervisor (production)
sudo supervisorctl restart wemard
sudo supervisorctl stop wemard
sudo supervisorctl start wemard
sudo supervisorctl status wemard

# Manual (development)
python manage.py runserver
python manage.py runserver 0.0.0.0:8000
```

### Database
```bash
# Run migrations
python manage.py migrate

# Create migration
python manage.py makemigrations

# Show migrations status
python manage.py showmigrations

# Rollback migration
python manage.py migrate app_name 0001

# Backup database
pg_dump dbname > backup_$(date +%Y%m%d).sql

# Restore database
psql dbname < backup_20260217.sql
```

### Static Files
```bash
# Collect static files
python manage.py collectstatic --noinput

# Clear static files
rm -rf staticfiles/*
python manage.py collectstatic --noinput
```

### Translations
```bash
# Compile message files
python manage.py compilemessages

# Make messages (extract translatable strings)
python manage.py makemessages -l uz -l ru -l en

# Manual compile
scripts/compile_messages_manual.py
```

---

## Customer Bots (Translation Centers)

### Control Bots
```bash
# Via Supervisor (production)
sudo supervisorctl restart wowdash-bots
sudo supervisorctl stop wowdash-bots
sudo supervisorctl start wowdash-bots
sudo supervisorctl status wowdash-bots

# Manual (development/testing)
python manage.py run_bots                    # All bots
python manage.py run_bots --center-id 1      # Specific center
python manage.py run_bots --list             # List all centers
```

### Setup Webhooks
```bash
# Setup webhooks for production (preferred over polling)
python manage.py setup_webhooks
python manage.py setup_webhooks --center-id 1
```

---

## Admin Bot (@multilang_robot)

### Control Bot
```bash
# Via Supervisor (production)
sudo supervisorctl restart multilang-admin-bot
sudo supervisorctl stop multilang-admin-bot
sudo supervisorctl start multilang-admin-bot
sudo supervisorctl status multilang-admin-bot

# View logs
sudo tail -f /var/log/supervisor/multilang-admin-bot.log

# Manual (development/testing)
python manage.py admin_bot
```

### Configuration & Testing
```bash
# Show configuration
python manage.py admin_bot --configure

# Test notifications
python manage.py admin_bot --test

# Test contact notification
python manage.py test_contact_notification

# Test channel access
python manage.py test_channel_access -1003856186766
python manage.py test_channel_access -1003856186766 --send-test
```

---

## Supervisor (Process Manager)

### Control All Services
```bash
# Status of all services
sudo supervisorctl status

# Restart all services
sudo supervisorctl restart all

# Stop all services
sudo supervisorctl stop all

# Reload configuration after changes
sudo supervisorctl reread
sudo supervisorctl update
```

### View Logs
```bash
# Django app
sudo tail -f /var/log/supervisor/wemard.log
sudo tail -f /var/log/supervisor/wemard-error.log

# Customer bots
sudo tail -f /var/log/supervisor/wowdash-bots.log

# Admin bot
sudo tail -f /var/log/supervisor/multilang-admin-bot.log
```

### Configuration Files
```bash
# View configs
sudo ls -la /etc/supervisor/conf.d/

# Edit config
sudo nano /etc/supervisor/conf.d/wemard.conf
sudo nano /etc/supervisor/conf.d/multilang-admin-bot.conf

# After editing, reload
sudo supervisorctl reread
sudo supervisorctl update
```

---

## System Monitoring

### Check Processes
```bash
# All Python processes
ps aux | grep python

# Django processes
ps aux | grep manage.py

# Bot processes
ps aux | grep admin_bot
ps aux | grep run_bots

# Gunicorn workers
ps aux | grep gunicorn
```

### Resource Usage
```bash
# Memory usage
free -h

# Disk usage
df -h

# Check specific directory size
du -sh /home/wemard/app/media
du -sh /home/wemard/app/logs

# CPU and memory per process
top
htop  # if installed
```

### Network
```bash
# Check port usage
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :80

# Test if port is accessible
curl http://localhost:8000
curl http://your-domain.com
```

---

## File Management

### Backups
```bash
# Database backup
cd /home/wemard/app
pg_dump your_db_name > backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Media files backup
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Full backup
tar -czf full_backup_$(date +%Y%m%d).tar.gz \
  --exclude='venv' \
  --exclude='staticfiles' \
  --exclude='__pycache__' \
  /home/wemard/app
```

### Archive Management
```bash
# Archive old orders (manual)
python manage.py archive_old_orders

# Install archive cron job
cd /home/wemard/app/scripts
chmod +x install_archive_cron.sh
./install_archive_cron.sh

# Check cron job
crontab -l
```

### Logs
```bash
# View Django logs
tail -f logs/django.log
tail -f logs/error.log

# Clear old logs
find logs/ -name "*.log" -mtime +30 -delete

# Rotate logs manually
logrotate -f /etc/logrotate.d/wemard
```

---

## Git Operations

### Update Code
```bash
cd /home/wemard/app

# Pull latest changes
git pull origin main

# Check current branch
git branch

# Check status
git status

# View recent commits
git log --oneline -10
```

### After Code Update
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install/update dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py migrate

# 4. Collect static files
python manage.py collectstatic --noinput

# 5. Compile translations
python manage.py compilemessages

# 6. Restart services
sudo supervisorctl restart wemard
sudo supervisorctl restart wowdash-bots
sudo supervisorctl restart multilang-admin-bot
```

---

## Environment & Configuration

### Virtual Environment
```bash
# Activate
source /home/wemard/app/venv/bin/activate

# Deactivate
deactivate

# Install dependencies
pip install -r requirements.txt

# Update requirements
pip freeze > requirements.txt
```

### Environment Variables
```bash
# View .env file
cat .env

# Edit .env file
nano .env

# After editing .env, restart services
sudo supervisorctl restart all
```

### Django Settings
```bash
# Check current settings
python manage.py diffsettings

# Shell access
python manage.py shell

# Shell Plus (if installed)
python manage.py shell_plus
```

---

## User Management

### Create Users
```bash
# Create superuser
python manage.py createsuperuser

# Create user via shell
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.create_user('username', 'email@example.com', 'password')
```

### Manage Staff
```bash
# List all users
python manage.py shell
>>> from accounts.models import User
>>> User.objects.all().values('id', 'username', 'email')
```

---

## Testing & Debugging

### Run Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test orders
python manage.py test organizations

# Run specific test
python manage.py test orders.tests.OrderTestCase

# With coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Debug
```bash
# Check for errors
python manage.py check

# Validate templates
python manage.py validate_templates

# Show URLs
python manage.py show_urls

# Database shell
python manage.py dbshell
```

---

## Nginx & Web Server

### Control Nginx
```bash
# Restart Nginx
sudo systemctl restart nginx

# Reload configuration
sudo systemctl reload nginx

# Check status
sudo systemctl status nginx

# Test configuration
sudo nginx -t
```

### SSL Certificates (Certbot)
```bash
# Renew certificates
sudo certbot renew

# Check certificate status
sudo certbot certificates

# Manual renewal
sudo certbot renew --force-renewal
```

---

## Common Workflows

### Deploy New Changes
```bash
# 1. SSH to server
ssh wemard@your-server.com

# 2. Navigate to app
cd /home/wemard/app

# 3. Backup database
pg_dump your_db > backups/pre_deploy_$(date +%Y%m%d).sql

# 4. Pull changes
git pull origin main

# 5. Activate venv
source venv/bin/activate

# 6. Install dependencies
pip install -r requirements.txt

# 7. Run migrations
python manage.py migrate

# 8. Collect static
python manage.py collectstatic --noinput

# 9. Restart services
sudo supervisorctl restart all

# 10. Check status
sudo supervisorctl status
```

### Add New Translation Center
```bash
# 1. Create via Django admin panel at /admin/

# 2. Setup webhook (if using webhooks)
python manage.py setup_webhooks --center-id NEW_ID

# 3. Restart bots
sudo supervisorctl restart wowdash-bots

# 4. Test bot
# Send /start to the center's bot on Telegram
```

### Troubleshoot Service Down
```bash
# 1. Check status
sudo supervisorctl status

# 2. View logs
sudo tail -f /var/log/supervisor/SERVICE_NAME.log

# 3. Try restart
sudo supervisorctl restart SERVICE_NAME

# 4. If still down, check errors
sudo supervisorctl tail -100 SERVICE_NAME

# 5. Manual run to see errors
cd /home/wemard/app
source venv/bin/activate
python manage.py COMMAND  # e.g., runserver, admin_bot
```

---

## Quick Cheat Sheet

| Task | Command |
|------|---------|
| Restart Django | `sudo supervisorctl restart wemard` |
| Restart All | `sudo supervisorctl restart all` |
| View Status | `sudo supervisorctl status` |
| Check Logs | `sudo tail -f /var/log/supervisor/SERVICE.log` |
| Run Migrations | `python manage.py migrate` |
| Collect Static | `python manage.py collectstatic --noinput` |
| Start Admin Bot | `python manage.py admin_bot` (dev) |
| Test Admin Bot | `python manage.py admin_bot --test` |
| Pull Updates | `git pull origin main` |
| Restart Nginx | `sudo systemctl restart nginx` |

---

## Important Paths

```
/home/wemard/app/                          # Application root
/home/wemard/app/venv/                     # Virtual environment
/home/wemard/app/.env                      # Environment variables
/home/wemard/app/logs/                     # Application logs
/home/wemard/app/media/                    # Uploaded files
/home/wemard/app/backups/                  # Database backups
/etc/supervisor/conf.d/                    # Supervisor configs
/var/log/supervisor/                       # Supervisor logs
/etc/nginx/sites-available/                # Nginx configs
```

---

## Support & Help

```bash
# Django management commands help
python manage.py help
python manage.py help COMMAND

# Show all management commands
python manage.py help --commands

# Python shell for debugging
python manage.py shell

# Check Django version
python manage.py version
```
