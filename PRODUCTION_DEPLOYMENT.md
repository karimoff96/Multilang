# Multi-Worker Production Deployment Guide

This guide explains how to deploy the WowDash project for production with multiple workers and proper scalability.

## Prerequisites

1. **Redis Server** - For caching and session management
2. **PostgreSQL Database** - For production data storage
3. **Nginx** - As reverse proxy (for webhooks)
4. **Supervisor/Systemd** - For process management

## Environment Variables

Create a `.env.production` file:

```bash
# Django settings
DEBUG=False
SECRET_KEY=your-very-long-and-random-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (PostgreSQL)
USE_POSTGRES=true
DB_NAME=wowdash_production
DB_USER=wowdash_user
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432

# Redis
USE_REDIS=true
REDIS_URL=redis://localhost:6379/0

# Telegram (per center - configured in admin)
TELEGRAM_BOT_USERNAME=your_bot_username

# Webhook settings
WEBHOOK_BASE_URL=https://yourdomain.com
USE_WEBHOOK=true

# Email
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Installation Steps

### 1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv postgresql postgresql-contrib redis-server nginx supervisor

# Start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Start PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 2. Set Up PostgreSQL

```bash
sudo -u postgres psql

CREATE DATABASE wowdash_production;
CREATE USER wowdash_user WITH PASSWORD 'your-secure-password';
ALTER ROLE wowdash_user SET client_encoding TO 'utf8';
ALTER ROLE wowdash_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE wowdash_user SET timezone TO 'Asia/Tashkent';
GRANT ALL PRIVILEGES ON DATABASE wowdash_production TO wowdash_user;
\q
```

### 3. Set Up Python Environment

```bash
cd /var/www/wowdash
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Django

```bash
# Copy environment file
cp .env.production .env

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 5. Gunicorn Configuration

Create `/etc/supervisor/conf.d/wowdash.conf`:

```ini
[program:wowdash]
command=/var/www/wowdash/venv/bin/gunicorn WowDash.wsgi:application --workers 4 --bind 127.0.0.1:8000 --timeout 120 --keep-alive 5 --max-requests 1000 --max-requests-jitter 50
directory=/var/www/wowdash
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/wowdash/gunicorn.log
environment=DJANGO_SETTINGS_MODULE="WowDash.settings"

[program:wowdash-bots]
command=/var/www/wowdash/venv/bin/python manage.py run_bots
directory=/var/www/wowdash
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/wowdash/bots.log
environment=DJANGO_SETTINGS_MODULE="WowDash.settings"
```

```bash
# Create log directory
sudo mkdir -p /var/log/wowdash
sudo chown www-data:www-data /var/log/wowdash

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start wowdash wowdash-bots
```

### 6. Nginx Configuration

Create `/etc/nginx/sites-available/wowdash`:

```nginx
upstream wowdash {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 100M;

    location /static/ {
        alias /var/www/wowdash/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/wowdash/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://wowdash;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/wowdash /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Architecture Overview

```
                    ┌─────────────────────────────────────┐
                    │           Telegram API               │
                    └─────────────┬───────────────────────┘
                                  │ Webhook
                                  ▼
                    ┌─────────────────────────────────────┐
                    │             Nginx                    │
                    │     (SSL termination, static)        │
                    └─────────────┬───────────────────────┘
                                  │
                                  ▼
         ┌────────────────────────────────────────────────────┐
         │                    Gunicorn                         │
         │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
         │   │Worker 1 │ │Worker 2 │ │Worker 3 │ │Worker 4 │  │
         │   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘  │
         │        │           │           │           │        │
         └────────┼───────────┼───────────┼───────────┼────────┘
                  │           │           │           │
                  ▼           ▼           ▼           ▼
         ┌────────────────────────────────────────────────────┐
         │                      Redis                          │
         │         (Sessions, Cache, Bot State)                │
         └────────────────────────────────────────────────────┘
                                  │
                                  ▼
         ┌────────────────────────────────────────────────────┐
         │                   PostgreSQL                        │
         │             (Primary Data Storage)                  │
         └────────────────────────────────────────────────────┘
```

## Webhook vs Polling Mode

### Development (Polling)
- Use `python manage.py run_bots`
- Each center's bot polls Telegram for updates
- Simple but uses more resources

### Production (Webhook)
- Telegram pushes updates to your server
- More efficient, lower latency
- Requires HTTPS and public URL

To set up webhooks for all centers:
```bash
python manage.py setup_webhooks --base-url https://yourdomain.com
```

## State Management

The project now uses persistent state storage for multi-worker support:

### Old Approach (In-Memory) ❌
```python
user_data = {}  # Lost when worker restarts
uploaded_files = {}  # Not shared between workers
```

### New Approach (Database + Redis) ✅
```python
from bot.state_manager import StateManager

# Get state for user
state = StateManager.get(user_id, center_id)

# Store data
state.product_id = 123
state.add_file(file_id)

# Retrieve data
order_id = state.pending_payment_order_id

# Clear on completion
state.clear()
```

## Scaling Recommendations

### Horizontal Scaling
1. Add more Gunicorn workers (2-4 per CPU core)
2. Add Redis replicas if needed
3. Use PostgreSQL connection pooling (PgBouncer)

### Vertical Scaling
- RAM: 4GB minimum, 8GB recommended
- CPU: 2 cores minimum, 4+ for high traffic
- SSD: For database performance

### Monitoring
- Use `supervisorctl status` to check processes
- Monitor Redis with `redis-cli info`
- Set up log rotation for `/var/log/wowdash/`

## Maintenance Commands

```bash
# Restart all services
sudo supervisorctl restart wowdash wowdash-bots

# View logs
tail -f /var/log/wowdash/gunicorn.log
tail -f /var/log/wowdash/bots.log

# Database backup
pg_dump wowdash_production > backup_$(date +%Y%m%d).sql

# Clear old sessions
python manage.py clearsessions

# Clear stale bot states (run daily via cron)
python manage.py cleanup_bot_states
```

## Security Checklist

- [ ] DEBUG=False in production
- [ ] Strong SECRET_KEY (use `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Database password is strong
- [ ] Redis is bound to localhost only
- [ ] Firewall configured (allow 80, 443 only)
- [ ] Regular backups configured
- [ ] Log rotation enabled
