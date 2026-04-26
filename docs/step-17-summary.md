# Step 17: Deployment & Production Setup — Summary

## What Should Be Done

Production-ready deployment checklist and configuration.

## Pre-Deployment Checklist

### 1. Security Hardening

**Update Settings**
```
DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
SECRET_KEY = os.urandom(50).hex()  # Generate strong secret key
```

**API Security**
- Enable rate limiting on all endpoints
- Add HTTPS/SSL certificate (Let's Encrypt recommended)
- Configure CORS for frontend domain only
- Enable CSRF protection

### 2. Database Migration

**From SQLite to PostgreSQL**

```bash
# 1. Install PostgreSQL
brew install postgresql

# 2. Create production database
createdb intradoc_ai_prod
createuser intradoc_user

# 3. Update .env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=intradoc_ai_prod
DB_USER=intradoc_user
DB_PASSWORD=<strong_password>
DB_HOST=localhost
DB_PORT=5432

# 4. Run migrations
python manage.py migrate

# 5. Backup SQLite data (if migrating from existing)
python manage.py dumpdata > backup.json
python manage.py loaddata backup.json
```

### 3. Document Storage

**Local Storage vs Cloud**

**Local Storage (Current)**
```
MEDIA_ROOT=/var/www/intradoc_ai/media
FAISS_INDEX_DIR=/var/www/intradoc_ai/faiss_indexes
```

**Cloud Storage (AWS S3 - Recommended)**
```bash
# Install boto3
pip install boto3 django-storages

# Update settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = 'intradoc-ai-prod'
AWS_S3_REGION_NAME = 'us-east-1'
```

### 4. LLM Service Configuration

**Current: Groq API**
```
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
LLM_MODEL = 'llama-3.1-8b-instant'
LLM_TIMEOUT = 120
```

**Verify Before Launch:**
- Test with production API key
- Monitor rate limits (30 req/min, 5 concurrent)
- Set up alerting for API failures
- Have fallback LLM model configured

### 5. Logging & Monitoring

**Production Logging**
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/intradoc_ai/app.log',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/intradoc_ai/error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Deployment Options

### Option 1: Linux Server (Recommended for Control)

**Setup:**
```bash
# 1. SSH into server
ssh user@your-server.com

# 2. Clone repository
cd /var/www
git clone <your-repo> intradoc_ai
cd intradoc_ai

# 3. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Setup environment variables
cp .env.example .env
nano .env  # Edit with production values

# 5. Collect static files
python manage.py collectstatic --noinput

# 6. Run migrations
python manage.py migrate

# 7. Create superuser
python manage.py createsuperuser

# 8. Start with Gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

**Systemd Service File** (auto-restart on reboot)

Create `/etc/systemd/system/intradoc.service`:
```ini
[Unit]
Description=IntraDoc AI
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/intradoc_ai
ExecStart=/var/www/intradoc_ai/venv/bin/gunicorn \
  --workers 4 \
  --bind unix:/var/www/intradoc_ai/intradoc.sock \
  core.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable intradoc
sudo systemctl start intradoc
sudo systemctl status intradoc
```

### Option 2: Docker Container

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations and start server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "core.wsgi:application"]

EXPOSE 8000
```

**Docker Compose:**
```yaml
version: '3.9'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: intradoc_ai_prod
      POSTGRES_USER: intradoc_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    command: >
      sh -c "python manage.py migrate &&
             gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4"
    ports:
      - "8000:8000"
    environment:
      DEBUG: "False"
      DB_HOST: db
      GROQ_API_KEY: ${GROQ_API_KEY}
    volumes:
      - ./media:/app/media
      - ./faiss_indexes:/app/faiss_indexes
    depends_on:
      - db

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web

volumes:
  postgres_data:
```

**Build and run:**
```bash
docker-compose up -d
docker-compose logs -f
```

### Option 3: Cloud Platform (Heroku/Railway/Render)

**For Render:**

Create `render.yaml`:
```yaml
services:
  - type: web
    name: intradoc-ai
    env: python
    buildCommand: pip install -r requirements.txt && python manage.py migrate
    startCommand: gunicorn core.wsgi:application
    envVars:
      - key: DEBUG
        value: "False"
      - key: ALLOWED_HOSTS
        value: intradoc-ai.onrender.com
      - key: GROQ_API_KEY
        fromEnv: GROQ_API_KEY
      - key: DATABASE_URL
        fromDatabase:
          name: intradoc-db
          property: connectionString
  
  - type: pserv
    name: intradoc-db
    ipWhitelist: []
    plan: standard
```

## FAISS Index Backup

**Backup Strategy:**
```bash
# Daily backup
0 2 * * * tar -czf /backup/faiss_indexes_$(date +\%Y\%m\%d).tar.gz /var/www/intradoc_ai/faiss_indexes

# Weekly database backup
0 3 * * 0 pg_dump intradoc_ai_prod | gzip > /backup/db_$(date +\%Y\%m\%d).sql.gz
```

## Monitoring & Alerting

### Key Metrics to Monitor

1. **API Response Time**
   - Target: < 2 seconds average
   - Alert if: > 5 seconds for 5 min

2. **Error Rate**
   - Target: < 0.1%
   - Alert if: > 1% in 5 min window

3. **LLM Service Health**
   - Monitor Groq API status
   - Alert on 429/500 errors

4. **Database Performance**
   - Query execution time
   - Connection pool usage

5. **Disk Space**
   - Media files size
   - FAISS index size
   - Log files

### Monitoring Tools

- **Datadog**: Full APM monitoring
- **New Relic**: Application performance
- **Sentry**: Error tracking
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization

## SSL/HTTPS Setup

### Using Let's Encrypt (Free)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Auto-renewal setup
sudo certbot renew --dry-run

# Configure Nginx to use certificate
```

### Nginx Configuration

```nginx
upstream intradoc {
    server localhost:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Proxy settings
    location / {
        proxy_pass http://intradoc;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static/ {
        alias /var/www/intradoc_ai/staticfiles/;
    }
    
    # Media files
    location /media/ {
        alias /var/www/intradoc_ai/media/;
    }
}
```

## Performance Tuning

### Database Optimization
```sql
-- Create indexes on frequently queried columns
CREATE INDEX idx_document_department ON documents(department);
CREATE INDEX idx_chatlog_user_timestamp ON chat_logs(user_id, timestamp DESC);
CREATE INDEX idx_document_uploaded_by ON documents(uploaded_by);
```

### Caching Strategy
```python
# Cache document list for 5 minutes
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'redis_client.DefaultClient',
        },
        'KEY_PREFIX': 'intradoc',
        'TIMEOUT': 300,
    }
}
```

### Worker Scaling
```bash
# Gunicorn with multiple workers
gunicorn core.wsgi:application \
  --workers 8 \
  --worker-class sync \
  --worker-connections 1000 \
  --max-requests 1000 \
  --max-requests-jitter 50
```

## Disaster Recovery

### Database Backup/Restore
```bash
# Backup
pg_dump intradoc_ai_prod > backup.sql

# Restore
psql intradoc_ai_prod < backup.sql
```

### FAISS Index Rebuild
```bash
# If index corrupted, rebuild from documents
python manage.py rebuild_indexes

# Manual rebuild
from ai.vector import rebuild_all_indexes
rebuild_all_indexes()
```

## Production Checklist

- [ ] Change DEBUG to False
- [ ] Set strong SECRET_KEY
- [ ] Configure ALLOWED_HOSTS
- [ ] Switch to PostgreSQL
- [ ] Setup SSL/HTTPS
- [ ] Configure static files serving
- [ ] Setup logging
- [ ] Test database backups
- [ ] Setup monitoring/alerting
- [ ] Load test with production data
- [ ] Verify CORS configuration
- [ ] Setup rate limiting
- [ ] Create backup strategy
- [ ] Document runbooks
- [ ] Train operations team

---

**Ready for production deployment with security, scalability, and reliability.**
