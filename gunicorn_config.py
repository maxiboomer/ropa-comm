"""
Gunicorn configuration for RoPA production deployment.
Loaded by: gunicorn -c gunicorn_config.py app:app
"""
import multiprocessing
import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("ROPA_DATA_DIR", Path.home() / "Library/Application Support/ropa"))
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Network
bind = "127.0.0.1:8000"
backlog = 2048

# Workers
workers = min(4, (multiprocessing.cpu_count() * 2) + 1)
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
graceful_timeout = 30

# Process naming
proc_name = "ropa"

# Logging
accesslog = str(LOG_DIR / "gunicorn-access.log")
errorlog = str(LOG_DIR / "gunicorn-error.log")
loglevel = "info"
access_log_format = '%(h)s - %(u)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'

# Process lifecycle
preload_app = True
max_requests = 1000
max_requests_jitter = 50

# Security
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190
