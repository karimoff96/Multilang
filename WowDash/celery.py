"""
Celery application config for WowDash.

Broker:  Redis (same instance used by Django cache/sessions).
Backend: Redis for task result storage.

Workers are started separately:
    celery -A WowDash worker -l INFO -c 2 --queues broadcasts,default

Add to supervisor (see deployment/multilang-admin-bot.conf for pattern):
    [program:wowdash-celery]
    command=/home/Wow-dash/venv/bin/celery -A WowDash worker -l INFO -c 2
    directory=/home/Wow-dash
    user=www-data
    autostart=true
    autorestart=true
    stdout_logfile=/home/Wow-dash/logs/celery.log
    stderr_logfile=/home/Wow-dash/logs/celery_error.log
"""

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WowDash.settings")

app = Celery("WowDash")

# Read config from Django settings, all keys prefixed with CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in every installed app
app.autodiscover_tasks()
