# 🚀 Hostel Management System - Setup & Deployment Guide

## Quick Start (Development)

### 1. Install Python Packages
```bash
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Admin User
```bash
python manage.py createsuperuser
# Follow prompts
```

### 5. Create Test Data (Optional)
```bash
python manage.py shell
```

Then run this Python code:
```python
from accounts.models import CustomUser, StudentProfile, WardenProfile
from django.contrib.auth import get_user_model

User = get_user_model()

# Create test admin
admin_user = User.objects.create_user(
    username='admin',
    email='admin@example.com',
    password='admin123456',
    role='admin',
    first_name='Admin',
    last_name='User'
)

# Create test warden
warden_user = User.objects.create_user(
    username='warden',
    email='warden@example.com',
    password='warden123456',
    role='warden',
    first_name='Warden',
    last_name='User'
)

warden_profile = WardenProfile.objects.create(
    user=warden_user,
    assigned_floor=1,
    office_location='Ground Floor'
)

# Create test student
student_user = User.objects.create_user(
    username='student',
    email='student@example.com',
    password='student123456',
    role='student',
    first_name='Student',
    last_name='User'
)

student_profile = StudentProfile.objects.create(
    user=student_user,
    enrollment_number='ST-001-2024',
    contact_number='9999999999'
)

print("Test users created successfully!")
exit()
```

### 6. Start Development Server
```bash
python manage.py runserver
```

### 7. Access the Application
- **Web App**: http://localhost:8000/login/
- **Admin Panel**: http://localhost:8000/admin/

**Test Credentials**:
- Admin: `admin` / `admin123456`
- Warden: `warden` / `warden123456`
- Student: `student` / `student123456`

---

## 🔐 Production Deployment

### Environment Setup

**Create `.env` for production:**
```bash
DEBUG=False
SECRET_KEY=your-production-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@localhost:5432/hostel_db
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DJANGO_LOG_LEVEL=WARNING
```

### 1. Generate Secret Key
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### 2. Install Production Dependencies
```bash
pip install gunicorn psycopg2-binary whitenoise
```

### 3. Setup PostgreSQL Database
```bash
createdb hostel_db
psql hostel_db < backup.sql  # If migrating from existing DB
```

### 4. Update Settings for Production
- Set `DEBUG = False`
- Update `ALLOWED_HOSTS`
- Configure database connection
- Enable SSL/HTTPS

### 5. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 6. Run Migrations
```bash
python manage.py migrate --no-input
```

### 7. Create Admin User (Production)
```bash
python manage.py createsuperuser
```

### 8. Test with Gunicorn Locally
```bash
gunicorn hostel_management.wsgi:application --bind 0.0.0.0:8000
```

---

## 📦 Database Models Overview

### Accounts App
- `CustomUser`: Extended user model with roles (admin/warden/student)
- `StudentProfile`: Student-specific information
- `WardenProfile`: Warden assignment details

### Core App
- `Room`: Room details (number, capacity, amenities)
- `RoomAllocation`: Student-to-room mapping
- `RoomConditionReport`: Room inspection records

### Operations App
- `Complaint`: Issue reporting system
- `Attendance`: Daily attendance tracking
- `Fee`: Fee management and payments
- `Visitor`: Visitor tracking system
- `LeaveApplication`: Leave request system
- `MaintenanceRequest`: Maintenance issue tracking
- `Announcement`: System announcements
- `Event`: Hostel events
- `RoomRating`: Room feedback system

---

## 🔒 Security Checklist

### Pre-Deployment
- [ ] Change `SECRET_KEY` in production
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Setup SSL/TLS certificate
- [ ] Configure CSRF settings
- [ ] Enable HTTPS redirect
- [ ] Configure secure cookies
- [ ] Setup logging system
- [ ] Enable rate limiting
- [ ] Configure backup strategy

### Database Security
- [ ] Use strong database password
- [ ] Enable database backups
- [ ] Restrict database access
- [ ] Use PostgreSQL (not SQLite) in production
- [ ] Encrypt sensitive data

### Application Security
- [ ] Regular security updates
- [ ] Monitor error logs
- [ ] Implement 2FA (future)
- [ ] Rate limiting on login
- [ ] Account lockout mechanism
- [ ] Regular security audits

---

## 📊 Monitoring & Logs

### Log Files Location
```
hostel_management/logs/hostel.log
```

### View Logs
```bash
tail -f hostel_management/logs/hostel.log
```

### Setup Remote Logging (Optional)
```python
# Configure Sentry for error tracking
import sentry_sdk
sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0
)
```

---

## 🔄 Backup & Restore

### Backup Database
```bash
pg_dump hostel_db > backup.sql
```

### Restore Database
```bash
psql hostel_db < backup.sql
```

### Backup Media Files
```bash
tar -czf media_backup.tar.gz media/
```

---

## 🚀 Docker Deployment (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "hostel_management.wsgi:application", "--bind", "0.0.0.0:8000"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://user:password@db:5432/hostel_db
    depends_on:
      - db
  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=hostel_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Run with Docker:
```bash
docker-compose up
```

---

## 📱 Performance Optimization

### 1. Enable Caching
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 2. Database Query Optimization
- Use `.select_related()` for ForeignKey
- Use `.prefetch_related()` for ManyToMany
- Add indexes to frequently searched fields
- Use `.only()` and `.defer()` to limit fields

### 3. Static Files
- Use CDN for static files
- Enable gzip compression
- Minify CSS/JavaScript

### 4. API Response Caching
```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def my_view(request):
    pass
```

---

## 🧪 Testing

### Run All Tests
```bash
python manage.py test
```

### Run Specific App Tests
```bash
python manage.py test accounts
python manage.py test operations
python manage.py test core
```

### Run with Coverage
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

---

## 📞 Troubleshooting

### Issue: Migration Errors
```bash
# Reset migrations
python manage.py migrate --fake accounts zero
python manage.py migrate accounts

# View migration status
python manage.py showmigrations
```

### Issue: Static Files Not Loading
```bash
# Collect static files
python manage.py collectstatic --clear --noinput

# Check static files directory
ls -la hostel_management/staticfiles/
```

### Issue: Database Connection
```bash
# Test database connection
python manage.py dbshell

# Reset database (development only!)
rm db.sqlite3
python manage.py migrate
```

### Issue: Port Already in Use
```bash
# Use different port
python manage.py runserver 8001

# Find process using port
lsof -i :8000
kill -9 <PID>
```

---

## 📚 Useful Commands

```bash
# Create superuser
python manage.py createsuperuser

# Shell access
python manage.py shell

# Run custom command
python manage.py shell < script.py

# Check for system issues
python manage.py check

# Generate migrations
python manage.py makemigrations --dry-run

# Export data
python manage.py dumpdata > backup.json

# Import data
python manage.py loaddata backup.json

# Clear cache
python manage.py clear_cache

# Create empty migration
python manage.py makemigrations --empty app_name
```

---

## 📖 Documentation Links

- [Django Official Docs](https://docs.djangoproject.com/)
- [Bootstrap 5](https://getbootstrap.com/docs/5.0/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Reverse Proxy](https://nginx.org/en/docs/)

---

**Last Updated**: 2024
**Version**: 2.0.0

For questions or issues, please refer to the main README.md or create an issue on GitHub.
